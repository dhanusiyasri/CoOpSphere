import { FormEvent, useEffect, useMemo, useState } from 'react';
import { approveNomination, createBatch, createNomination, createParticipant, createProgramme, getBatches, getEnrollments, getInstitutions, getNominations, getParticipants, getProgrammes, rejectNomination, updateParticipant, getCourses, getCourseModules, getCourseLessons, createCourse, createCourseModule, createCourseLesson, getTrainingSchedules, createTrainingSchedule, createAttendanceForSchedule, Batch, Enrollment, Institution, Nomination, ParticipantProfile, Programme, Course, CourseModule, CourseLesson, TrainingSchedule } from './api';

type User = { id: number; full_name: string; email: string; role: string; institution_id?: number };

const makeEmptyProgramme = (institutionId = 0) => ({ institution_id: institutionId, code: '', title: '', category: 'Cooperative Management', mode: 'HYBRID', duration_days: 5, capacity: 30, status: 'PUBLISHED', description: '' });

export function TrainingERP({ user }: { user: User }) {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [nominations, setNominations] = useState<Nomination[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [participants, setParticipants] = useState<ParticipantProfile[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseModules, setCourseModules] = useState<CourseModule[]>([]);
  const [courseLessons, setCourseLessons] = useState<CourseLesson[]>([]);
  const [schedules, setSchedules] = useState<TrainingSchedule[]>([]);
  const [courseForm, setCourseForm] = useState({ programme_id: 0, course_code: '', title: '', description: '', category: 'COOPERATIVE_MANAGEMENT', delivery_mode: 'HYBRID', duration_hours: 4, level: 'FOUNDATION', status: 'PUBLISHED' });
  const [moduleForm, setModuleForm] = useState({ course_id: 0, module_number: 1, title: '', learning_objectives: '', duration_minutes: 60 });
  const [lessonForm, setLessonForm] = useState({ module_id: 0, lesson_number: 1, title: '', content_type: 'TEXT', content_url: '', duration_minutes: 15, is_mandatory: true });
  const [message, setMessage] = useState('');
  const [programmeForm, setProgrammeForm] = useState(makeEmptyProgramme());
  const [batchForm, setBatchForm] = useState({ programme_id: 0, batch_code: '', start_date: '', end_date: '', trainer_id: '', venue: '', capacity: 30, status: 'OPEN' });
  const [nominationForm, setNominationForm] = useState({ batch_id: 0, trainee_id: user.id, remarks: '' });
  const [scheduleForm, setScheduleForm] = useState({ batch_id: 0, course_id: 0, module_id: 0, trainer_id: '', session_date: '', start_time: '09:30', end_time: '11:00', topic: '', venue: '', mode: 'IN_PERSON', status: 'SCHEDULED', notes: '' });
  const [participantForm, setParticipantForm] = useState({ user_id: user.id, participant_code: `NCCT-${user.id}`, phone: '', participant_type: 'RURAL_YOUTH', designation: '', organization_name: '', education_level: '', district: '', state: 'Tamil Nadu', digital_literacy_level: 'BASIC', years_experience: 0, profile_status: 'INCOMPLETE' });

  const canManage = ['NCCT_ADMIN', 'INSTITUTE_ADMIN', 'TRAINER'].includes(user.role);
  const canSubmitNomination = user.role === 'TRAINEE';

  const programmeMap = useMemo(() => new Map(programmes.map(p => [p.id, p])), [programmes]);
  const batchMap = useMemo(() => new Map(batches.map(b => [b.id, b])), [batches]);
  const selectedScheduleBatch = useMemo(() => batchMap.get(Number(scheduleForm.batch_id)), [batchMap, scheduleForm.batch_id]);
  const scheduleCourses = useMemo(() => selectedScheduleBatch ? courses.filter(c => c.programme_id === selectedScheduleBatch.programme_id) : courses, [courses, selectedScheduleBatch]);
  const scheduleModules = useMemo(() => {
    const courseId = Number(scheduleForm.course_id);
    return courseId ? courseModules.filter(m => m.course_id === courseId) : [];
  }, [courseModules, scheduleForm.course_id]);

  async function load() {
    const schedulePromise = (canManage || user.role === 'TRAINEE') ? getTrainingSchedules() : Promise.resolve([] as TrainingSchedule[]);
    const [i, p, b, n, e, participantsData, coursesData, modulesData, lessonsData, schedulesData] = await Promise.all([getInstitutions(), getProgrammes(), getBatches(), getNominations(), getEnrollments(), getParticipants(), getCourses(), getCourseModules(), getCourseLessons(), schedulePromise]);
    setInstitutions(i.filter(x => x.is_active));
    setProgrammes(p); setBatches(b); setNominations(n); setEnrollments(e); setParticipants(participantsData); setCourses(coursesData); setCourseModules(modulesData); setCourseLessons(lessonsData); setSchedules(schedulesData);
    const own = participantsData.find(x => x.user_id === user.id);
    if (own) setParticipantForm({ user_id: own.user_id, participant_code: own.participant_code, phone: own.phone || '', participant_type: own.participant_type, designation: own.designation || '', organization_name: own.organization_name || '', education_level: own.education_level || '', district: own.district || '', state: own.state || '', digital_literacy_level: own.digital_literacy_level, years_experience: own.years_experience, profile_status: own.profile_status });
    setProgrammeForm(current => current.institution_id ? current : { ...current, institution_id: user.institution_id ?? i.find(x => x.is_active)?.id ?? 0 });
    if (!batchForm.programme_id && p[0]) setBatchForm(x => ({ ...x, programme_id: p[0].id }));
    if (!courseForm.programme_id && p[0]) setCourseForm(x => ({ ...x, programme_id: p[0].id }));
    if (!moduleForm.course_id && coursesData[0]) setModuleForm(x => ({ ...x, course_id: coursesData[0].id }));
    if (!lessonForm.module_id && modulesData[0]) setLessonForm(x => ({ ...x, module_id: modulesData[0].id }));
    if (!nominationForm.batch_id && b[0]) setNominationForm(x => ({ ...x, batch_id: b[0].id }));
    if (!scheduleForm.batch_id && b[0]) {
      const firstBatch = b[0];
      const firstCourse = coursesData.find(c => c.programme_id === firstBatch.programme_id);
      const firstModule = firstCourse ? modulesData.find(m => m.course_id === firstCourse.id) : undefined;
      setScheduleForm(x => ({
        ...x,
        batch_id: firstBatch.id,
        course_id: firstCourse?.id ?? 0,
        module_id: firstModule?.id ?? 0,
        trainer_id: firstBatch.trainer_id ? String(firstBatch.trainer_id) : '',
        session_date: firstBatch.start_date,
        venue: firstBatch.venue || '',
      }));
    }
  }

  useEffect(() => { load().catch(e => setMessage(e.response?.data?.detail || 'Unable to load training data')); }, []);

  async function submitProgramme(e: FormEvent) {
    e.preventDefault();
    try {
      if (!programmeForm.institution_id) { setMessage('Select a training provider before creating the programme.'); return; }
      await createProgramme({ ...programmeForm, code: programmeForm.code.trim(), title: programmeForm.title.trim(), category: programmeForm.category.trim() });
      setProgrammeForm(makeEmptyProgramme(programmeForm.institution_id));
      setMessage('Programme created successfully.');
      await load();
    }
    catch (err: any) { setMessage(err.response?.data?.detail || 'Could not create programme'); }
  }

  async function submitBatch(e: FormEvent) {
    e.preventDefault();
    try {
      await createBatch({ ...batchForm, trainer_id: batchForm.trainer_id ? Number(batchForm.trainer_id) : undefined, programme_id: Number(batchForm.programme_id), capacity: Number(batchForm.capacity) });
      setMessage('Batch created successfully.'); await load();
    } catch (err: any) { setMessage(err.response?.data?.detail || 'Could not create batch'); }
  }

  async function submitNomination(e: FormEvent) {
    e.preventDefault();
    const traineeId = user.role === 'TRAINEE' ? user.id : Number(nominationForm.trainee_id);
    if (!traineeId) { setMessage('Enter the trainee user ID before submitting the nomination.'); return; }
    try {
      await createNomination({
        batch_id: Number(nominationForm.batch_id),
        trainee_id: traineeId,
        remarks: nominationForm.remarks || undefined
      });
      setMessage(user.role === 'TRAINEE' ? 'Nomination submitted successfully.' : `Nomination created for trainee #${traineeId}.`);
      setNominationForm(x => ({ ...x, remarks: '', trainee_id: user.role === 'TRAINEE' ? user.id : x.trainee_id }));
      await load();
    }
    catch (err: any) { setMessage(err.response?.data?.detail || 'Could not submit nomination'); }
  }

  async function submitCourse(e: FormEvent) {
    e.preventDefault();
    try { await createCourse({ ...courseForm, programme_id:Number(courseForm.programme_id), duration_hours:Number(courseForm.duration_hours) }); setMessage('Course created successfully.'); setCourseForm(x => ({...x, course_code:'', title:'', description:''})); await load(); }
    catch (err:any) { setMessage(err.response?.data?.detail || 'Could not create course'); }
  }

  async function submitCourseModule(e: FormEvent) {
    e.preventDefault();
    try { await createCourseModule({ ...moduleForm, course_id:Number(moduleForm.course_id), module_number:Number(moduleForm.module_number), duration_minutes:Number(moduleForm.duration_minutes) }); setMessage('Course module created successfully.'); setModuleForm(x=>({...x,module_number:x.module_number+1,title:'',learning_objectives:''})); await load(); }
    catch (err:any) { setMessage(err.response?.data?.detail || 'Could not create course module'); }
  }

  async function submitCourseLesson(e: FormEvent) {
    e.preventDefault();
    try { await createCourseLesson({ ...lessonForm, module_id:Number(lessonForm.module_id), lesson_number:Number(lessonForm.lesson_number), duration_minutes:Number(lessonForm.duration_minutes), content_url:lessonForm.content_url || undefined }); setMessage('Lesson created successfully.'); setLessonForm(x=>({...x,lesson_number:x.lesson_number+1,title:'',content_url:''})); await load(); }
    catch (err:any) { setMessage(err.response?.data?.detail || 'Could not create lesson'); }
  }

  async function submitSchedule(e: FormEvent) {
    e.preventDefault();
    const batch = batchMap.get(Number(scheduleForm.batch_id));
    const course = scheduleForm.course_id ? courses.find(c => c.id === Number(scheduleForm.course_id)) : undefined;
    const module = scheduleForm.module_id ? courseModules.find(m => m.id === Number(scheduleForm.module_id)) : undefined;
    const topic = scheduleForm.topic.trim();

    if (!batch) { setMessage('Select a valid batch before scheduling.'); return; }
    if (!scheduleForm.session_date) { setMessage('Select the session date.'); return; }
    if (scheduleForm.session_date < batch.start_date || scheduleForm.session_date > batch.end_date) {
      setMessage(`Session date must be between ${batch.start_date} and ${batch.end_date} for ${batch.batch_code}.`);
      return;
    }
    if (scheduleForm.end_time <= scheduleForm.start_time) { setMessage('End time must be after start time.'); return; }
    if (course && course.programme_id !== batch.programme_id) { setMessage('Selected course does not belong to the selected batch programme.'); return; }
    if (module && (!course || module.course_id !== course.id)) { setMessage('Selected module does not belong to the selected course.'); return; }
    if (!topic || topic.length < 2) { setMessage('Enter a session topic.'); return; }

    try {
      await createTrainingSchedule({
        batch_id:Number(scheduleForm.batch_id),
        course_id:scheduleForm.course_id ? Number(scheduleForm.course_id) : undefined,
        module_id:scheduleForm.module_id ? Number(scheduleForm.module_id) : undefined,
        trainer_id:scheduleForm.trainer_id ? Number(scheduleForm.trainer_id) : undefined,
        session_date:scheduleForm.session_date, start_time:scheduleForm.start_time, end_time:scheduleForm.end_time,
        topic, venue:scheduleForm.venue || undefined, mode:scheduleForm.mode, status:scheduleForm.status, notes:scheduleForm.notes || undefined,
      });
      setMessage('Training session scheduled successfully.');
      setScheduleForm(x=>({...x,topic:'',notes:''}));
      await load();
    } catch (err:any) { setMessage(err.response?.data?.detail || 'Could not create training schedule'); }
  }

  async function linkAttendance(id:number) {
    try { const result=await createAttendanceForSchedule(id); setMessage(`Attendance session ready. Access code: ${result.access_code}`); await load(); }
    catch (err:any) { setMessage(err.response?.data?.detail || 'Could not create attendance session'); }
  }

  async function submitParticipant(e: FormEvent) {
    e.preventDefault();
    try {
      const existing = participants.find(p => p.user_id === Number(participantForm.user_id));
      const payload = { ...participantForm, user_id: Number(participantForm.user_id), years_experience: Number(participantForm.years_experience) };
      if (existing) await updateParticipant(Number(participantForm.user_id), payload);
      else await createParticipant(payload);
      setMessage(existing ? 'Participant profile updated successfully.' : 'Participant profile created successfully.');
      await load();
    } catch (err: any) { setMessage(err.response?.data?.detail || 'Could not save participant profile'); }
  }

  async function approve(id: number) {
    try { await approveNomination(id); setMessage('Nomination approved and enrollment created.'); await load(); }
    catch (err: any) { setMessage(err.response?.data?.detail || 'Could not approve nomination'); }
  }

  async function reject(id: number) {
    const remarks = window.prompt('Reason for rejection (optional):') || '';
    try { await rejectNomination(id, remarks); setMessage('Nomination rejected.'); await load(); }
    catch (err: any) { setMessage(err.response?.data?.detail || 'Could not reject nomination'); }
  }

  return <div className="module-stack">
    <div className="module-header">
      <div><p className="eyebrow">TRAINING ERP</p><h2>Programme & Enrollment Management</h2><p className="muted">Manage programmes, batches, nominations and enrollments as one end-to-end workflow.</p></div>
      <div className="pill">{user.role.replace('_', ' ')}</div>
    </div>
    {message && <div className="notice">{message}</div>}

    <div className="stat-grid">
      <div className="mini-card"><span>Programmes</span><strong>{programmes.length}</strong></div>
      <div className="mini-card"><span>Open / Planned batches</span><strong>{batches.filter(b => ['OPEN', 'PLANNED'].includes(b.status)).length}</strong></div>
      <div className="mini-card"><span>Pending nominations</span><strong>{nominations.filter(n => n.status === 'SUBMITTED').length}</strong></div>
      <div className="mini-card"><span>Enrollments</span><strong>{enrollments.length}</strong></div>
    </div>

    {canManage && <div className="two-col">
      <form className="panel form-panel" onSubmit={submitProgramme}>
        <div className="panel-title"><h3>Create programme</h3><span>ERP-01</span></div>
        <label>Training provider<select value={programmeForm.institution_id} onChange={e => setProgrammeForm({...programmeForm, institution_id:Number(e.target.value)})} required><option value={0} disabled>Select provider</option>{institutions.map(i => <option key={i.id} value={i.id}>{i.name} — {i.institution_type}</option>)}</select></label>
        <label>Programme code<input value={programmeForm.code} onChange={e => setProgrammeForm({...programmeForm, code:e.target.value})} placeholder="NCCT-COOP-001" required /></label>
        <label>Title<input value={programmeForm.title} onChange={e => setProgrammeForm({...programmeForm, title:e.target.value})} placeholder="Cooperative Digital Management" required /></label>
        <div className="form-row"><label>Category<input value={programmeForm.category} onChange={e => setProgrammeForm({...programmeForm, category:e.target.value})} /></label><label>Mode<select value={programmeForm.mode} onChange={e => setProgrammeForm({...programmeForm, mode:e.target.value})}><option>HYBRID</option><option>ONLINE</option><option>OFFLINE</option></select></label></div>
        <div className="form-row"><label>Duration (days)<input type="number" min="1" value={programmeForm.duration_days} onChange={e => setProgrammeForm({...programmeForm, duration_days:Number(e.target.value)})} /></label><label>Capacity<input type="number" min="1" value={programmeForm.capacity} onChange={e => setProgrammeForm({...programmeForm, capacity:Number(e.target.value)})} /></label></div>
        <label>Description<textarea value={programmeForm.description} onChange={e => setProgrammeForm({...programmeForm, description:e.target.value})} /></label>
        <button className="primary">Create programme</button>
      </form>

      <form className="panel form-panel" onSubmit={submitBatch}>
        <div className="panel-title"><h3>Create batch</h3><span>ERP-02</span></div>
        <label>Programme<select value={batchForm.programme_id} onChange={e => setBatchForm({...batchForm, programme_id:Number(e.target.value)})} required>{programmes.map(p => <option key={p.id} value={p.id}>{p.code} — {p.title}</option>)}</select></label>
        <label>Batch code<input value={batchForm.batch_code} onChange={e => setBatchForm({...batchForm, batch_code:e.target.value})} placeholder="VAMNICOM-2026-A" required /></label>
        <div className="form-row"><label>Start date<input type="date" value={batchForm.start_date} onChange={e => setBatchForm({...batchForm, start_date:e.target.value})} required /></label><label>End date<input type="date" value={batchForm.end_date} onChange={e => setBatchForm({...batchForm, end_date:e.target.value})} required /></label></div>
        <div className="form-row"><label>Trainer ID<input type="number" value={batchForm.trainer_id} onChange={e => setBatchForm({...batchForm, trainer_id:e.target.value})} placeholder="Optional" /></label><label>Capacity<input type="number" min="1" value={batchForm.capacity} onChange={e => setBatchForm({...batchForm, capacity:Number(e.target.value)})} /></label></div>
        <label>Venue<input value={batchForm.venue} onChange={e => setBatchForm({...batchForm, venue:e.target.value})} placeholder="Training Hall" /></label>
        <button className="primary">Create batch</button>
      </form>
    </div>}

    <section className="panel" style={{marginBottom: 0}}>
      <div className="panel-title">
        <div><h3>Participant Management</h3><p className="muted" style={{margin:'4px 0 0',fontSize:12}}>ERP-06 • Maintain the participant master profile used across nominations, training, skills and employment.</p></div>
        <span>ERP-06</span>
      </div>
      <div className="two-col" style={{marginTop:12}}>
        <form className="panel form-panel" onSubmit={submitParticipant}>
          <div className="panel-title"><h3>{participants.some(p => p.user_id === user.id) ? 'Update participant profile' : 'Create participant profile'}</h3><span>PROFILE</span></div>
          <label>User ID<input type="number" min="1" value={participantForm.user_id} disabled={user.role === 'TRAINEE'} onChange={e => setParticipantForm({...participantForm,user_id:Number(e.target.value)})} /></label>
          <label>Participant code<input value={participantForm.participant_code} onChange={e => setParticipantForm({...participantForm,participant_code:e.target.value})} placeholder="NCCT-P-001" required /></label>
          <div className="form-row"><label>Participant type<select value={participantForm.participant_type} onChange={e=>setParticipantForm({...participantForm,participant_type:e.target.value})}><option>RURAL_YOUTH</option><option>COOPERATIVE_PERSONNEL</option><option>PACS_MEMBER</option><option>SHG_MEMBER</option><option>FARMER</option><option>DAIRY_MEMBER</option><option>STUDENT</option><option>OTHER</option></select></label><label>Digital literacy<select value={participantForm.digital_literacy_level} onChange={e=>setParticipantForm({...participantForm,digital_literacy_level:e.target.value})}><option>BASIC</option><option>INTERMEDIATE</option><option>ADVANCED</option></select></label></div>
          <div className="form-row"><label>Phone<input value={participantForm.phone} onChange={e=>setParticipantForm({...participantForm,phone:e.target.value})} placeholder="Optional" /></label><label>Years experience<input type="number" min="0" max="60" value={participantForm.years_experience} onChange={e=>setParticipantForm({...participantForm,years_experience:Number(e.target.value)})} /></label></div>
          <div className="form-row"><label>Designation<input value={participantForm.designation} onChange={e=>setParticipantForm({...participantForm,designation:e.target.value})} placeholder="Secretary / Member / Farmer" /></label><label>Organization<input value={participantForm.organization_name} onChange={e=>setParticipantForm({...participantForm,organization_name:e.target.value})} placeholder="Cooperative / Institution" /></label></div>
          <div className="form-row"><label>Education<input value={participantForm.education_level} onChange={e=>setParticipantForm({...participantForm,education_level:e.target.value})} placeholder="Diploma / UG / PG" /></label><label>District<input value={participantForm.district} onChange={e=>setParticipantForm({...participantForm,district:e.target.value})} /></label></div>
          <div className="form-row"><label>State<input value={participantForm.state} onChange={e=>setParticipantForm({...participantForm,state:e.target.value})} /></label><label>Profile status<select value={participantForm.profile_status} onChange={e=>setParticipantForm({...participantForm,profile_status:e.target.value})}><option>INCOMPLETE</option><option>ACTIVE</option><option>VERIFIED</option></select></label></div>
          <button className="primary">Save participant profile</button>
        </form>
        <div className="panel">
          <div className="panel-title"><h3>Participant register</h3><span>{participants.length}</span></div>
          <div className="table-wrap"><table><thead><tr><th>Code</th><th>Participant</th><th>Type</th><th>Organization</th><th>Location</th><th>Profile</th></tr></thead><tbody>
            {participants.map(p => <tr key={p.id}><td>{p.participant_code}</td><td>{p.user_full_name}<br/><span className="muted">{p.user_email}</span></td><td>{p.participant_type.replaceAll('_',' ')}</td><td>{p.organization_name || '—'}</td><td>{[p.district,p.state].filter(Boolean).join(', ') || '—'}</td><td><span className={`status-badge ${p.profile_status.toLowerCase()}`}>{p.profile_status}</span></td></tr>)}
            {!participants.length && <tr><td colSpan={6} className="empty">No participant profiles yet.</td></tr>}
          </tbody></table></div>
        </div>
      </div>
    </section>

    <section className="panel" style={{marginBottom: 0}}>
      <div className="panel-title">
        <div>
          <h3>Nomination Management</h3>
          <p className="muted" style={{margin:'4px 0 0',fontSize:12}}>ERP-03 • Create and submit trainee nominations for available training batches.</p>
        </div>
        <span>ERP-03</span>
      </div>

      <div className="two-col" style={{marginTop:12}}>
        <form className="panel form-panel" onSubmit={submitNomination}>
          <div className="panel-title"><h3>{canSubmitNomination ? 'Submit my nomination' : 'Create nomination for trainee'}</h3><span>{canSubmitNomination ? 'TRAINEE' : 'MANAGER'}</span></div>
          <p className="muted" style={{margin:'-3px 0 3px',fontSize:12}}>
            {canSubmitNomination
              ? 'Apply for an open training batch. Duplicate applications are blocked and rejected applications can be resubmitted.'
              : 'Managers can nominate a trainee by user ID. The backend verifies that the selected user has the TRAINEE role and that capacity is available.'}
          </p>

          <label>Batch
            <select value={nominationForm.batch_id} onChange={e => setNominationForm({...nominationForm, batch_id:Number(e.target.value)})} required>
              <option value={0} disabled>Select batch</option>
              {batches.filter(b => ['OPEN','PLANNED'].includes(b.status)).map(b => {
                const used=enrollments.filter(e=>e.batch_id===b.id && ['ACTIVE','COMPLETED'].includes(e.status)).length;
                const pending=nominations.filter(n=>n.batch_id===b.id && n.status==='SUBMITTED').length;
                const remaining=Math.max(0,b.capacity-used-pending);
                return <option key={b.id} value={b.id}>{b.batch_code} — {programmeMap.get(b.programme_id)?.title} ({remaining} seats)</option>;
              })}
            </select>
          </label>

          {(() => {
            const b=batchMap.get(nominationForm.batch_id);
            if(!b) return null;
            const used=enrollments.filter(e=>e.batch_id===b.id && ['ACTIVE','COMPLETED'].includes(e.status)).length;
            const pending=nominations.filter(n=>n.batch_id===b.id && n.status==='SUBMITTED').length;
            const remaining=Math.max(0,b.capacity-used-pending);
            return <div className="notice">Selected batch: <strong>{b.batch_code}</strong> · Capacity {b.capacity} · {remaining} seats currently available.</div>;
          })()}

          {canSubmitNomination
            ? <label>Trainee<input value={`${user.full_name} (#${user.id})`} disabled /></label>
            : <label>Trainee User ID<input type="number" min="1" value={nominationForm.trainee_id || ''} onChange={e => setNominationForm({...nominationForm, trainee_id:Number(e.target.value)})} placeholder="e.g. 3" required /></label>}

          <label>Remarks
            <textarea value={nominationForm.remarks} onChange={e => setNominationForm({...nominationForm, remarks:e.target.value})} placeholder="Learning goal, role, cooperative / institution context, or other relevant note" maxLength={1000} />
          </label>
          <button className="primary">{canSubmitNomination ? 'Submit nomination' : 'Create nomination'}</button>
        </form>

        <div className="panel">
          <div className="panel-title"><h3>Nomination Management Queue</h3><span>ERP-04</span></div>
          <div className="table-wrap"><table><thead><tr><th>ID</th><th>Batch</th><th>Trainee</th><th>Remarks</th><th>Status</th>{canManage && <th>Action</th>}</tr></thead><tbody>
            {nominations.map(n => <tr key={n.id}>
              <td>#{n.id}</td>
              <td>{batchMap.get(n.batch_id)?.batch_code || `#${n.batch_id}`}</td>
              <td>#{n.trainee_id}</td>
              <td>{n.remarks || '—'}</td>
              <td><span className={`status-badge ${n.status.toLowerCase()}`}>{n.status}</span></td>
              {canManage && <td>{n.status === 'SUBMITTED'
                ? <span style={{display:'flex',gap:6}}><button className="small-btn" onClick={() => approve(n.id)}>Approve & enroll</button><button className="small-btn" onClick={() => reject(n.id)}>Reject</button></span>
                : n.status === 'REJECTED' ? <span className="muted">Awaiting resubmission</span> : '—'}</td>}
            </tr>)}
            {!nominations.length && <tr><td colSpan={canManage ? 6 : 5} className="empty">No nominations yet.</td></tr>}
          </tbody></table></div>
        </div>
      </div>
    </section>


    <section className="panel" style={{marginBottom: 0}}>
      <div className="panel-title"><div><h3>Course & Curriculum Management</h3><p className="muted" style={{margin:'4px 0 0',fontSize:12}}>ERP-07 • Define courses under programmes, then structure them into modules and lessons for the LMS.</p></div><span>ERP-07</span></div>
      <div className="two-col" style={{marginTop:12}}>
        <div>
          {canManage && <form className="panel form-panel" onSubmit={submitCourse}>
            <div className="panel-title"><h3>Create course</h3><span>COURSE</span></div>
            <label>Programme<select value={courseForm.programme_id} onChange={e=>setCourseForm({...courseForm,programme_id:Number(e.target.value)})} required><option value={0} disabled>Select programme</option>{programmes.map(p=><option key={p.id} value={p.id}>{p.code} — {p.title}</option>)}</select></label>
            <div className="form-row"><label>Course code<input value={courseForm.course_code} onChange={e=>setCourseForm({...courseForm,course_code:e.target.value})} placeholder="COOP-101" required /></label><label>Level<select value={courseForm.level} onChange={e=>setCourseForm({...courseForm,level:e.target.value})}><option>FOUNDATION</option><option>INTERMEDIATE</option><option>ADVANCED</option></select></label></div>
            <label>Course title<input value={courseForm.title} onChange={e=>setCourseForm({...courseForm,title:e.target.value})} placeholder="Cooperative Management Fundamentals" required /></label>
            <div className="form-row"><label>Category<input value={courseForm.category} onChange={e=>setCourseForm({...courseForm,category:e.target.value})} /></label><label>Delivery<select value={courseForm.delivery_mode} onChange={e=>setCourseForm({...courseForm,delivery_mode:e.target.value})}><option>HYBRID</option><option>ONLINE</option><option>OFFLINE</option></select></label></div>
            <div className="form-row"><label>Duration (hours)<input type="number" min="1" value={courseForm.duration_hours} onChange={e=>setCourseForm({...courseForm,duration_hours:Number(e.target.value)})} /></label><label>Status<select value={courseForm.status} onChange={e=>setCourseForm({...courseForm,status:e.target.value})}><option>DRAFT</option><option>PUBLISHED</option><option>ARCHIVED</option></select></label></div>
            <label>Description<textarea value={courseForm.description} onChange={e=>setCourseForm({...courseForm,description:e.target.value})} /></label>
            <button className="primary">Create course</button>
          </form>}

          {canManage && <form className="panel form-panel" onSubmit={submitCourseModule}>
            <div className="panel-title"><h3>Add module</h3><span>MODULE</span></div>
            <label>Course<select value={moduleForm.course_id} onChange={e=>setModuleForm({...moduleForm,course_id:Number(e.target.value)})} required><option value={0} disabled>Select course</option>{courses.map(c=><option key={c.id} value={c.id}>{c.course_code} — {c.title}</option>)}</select></label>
            <div className="form-row"><label>Module no.<input type="number" min="1" value={moduleForm.module_number} onChange={e=>setModuleForm({...moduleForm,module_number:Number(e.target.value)})} /></label><label>Duration (min)<input type="number" min="1" value={moduleForm.duration_minutes} onChange={e=>setModuleForm({...moduleForm,duration_minutes:Number(e.target.value)})} /></label></div>
            <label>Module title<input value={moduleForm.title} onChange={e=>setModuleForm({...moduleForm,title:e.target.value})} required /></label>
            <label>Learning objectives<textarea value={moduleForm.learning_objectives} onChange={e=>setModuleForm({...moduleForm,learning_objectives:e.target.value})} /></label>
            <button className="primary">Add module</button>
          </form>}

          {canManage && <form className="panel form-panel" onSubmit={submitCourseLesson}>
            <div className="panel-title"><h3>Add lesson</h3><span>LESSON</span></div>
            <label>Module<select value={lessonForm.module_id} onChange={e=>setLessonForm({...lessonForm,module_id:Number(e.target.value)})} required><option value={0} disabled>Select module</option>{courseModules.map(m=><option key={m.id} value={m.id}>M{m.module_number} — {m.title}</option>)}</select></label>
            <div className="form-row"><label>Lesson no.<input type="number" min="1" value={lessonForm.lesson_number} onChange={e=>setLessonForm({...lessonForm,lesson_number:Number(e.target.value)})} /></label><label>Duration (min)<input type="number" min="1" value={lessonForm.duration_minutes} onChange={e=>setLessonForm({...lessonForm,duration_minutes:Number(e.target.value)})} /></label></div>
            <label>Lesson title<input value={lessonForm.title} onChange={e=>setLessonForm({...lessonForm,title:e.target.value})} required /></label>
            <div className="form-row"><label>Content type<select value={lessonForm.content_type} onChange={e=>setLessonForm({...lessonForm,content_type:e.target.value})}><option>TEXT</option><option>VIDEO</option><option>PDF</option><option>LINK</option><option>QUIZ</option></select></label><label>Content URL<input value={lessonForm.content_url} onChange={e=>setLessonForm({...lessonForm,content_url:e.target.value})} placeholder="Optional" /></label></div>
            <label style={{display:'flex',gap:8,alignItems:'center'}}><input type="checkbox" checked={lessonForm.is_mandatory} onChange={e=>setLessonForm({...lessonForm,is_mandatory:e.target.checked})} /> Mandatory lesson</label>
            <button className="primary">Add lesson</button>
          </form>}
        </div>
        <div className="panel">
          <div className="panel-title"><h3>Curriculum register</h3><span>{courses.length} courses</span></div>
          {!courses.length ? <div className="empty">No courses created yet.</div> : courses.map(c=>{ const mods=courseModules.filter(m=>m.course_id===c.id); return <div key={c.id} className="panel" style={{marginBottom:10}}><div className="panel-title"><div><strong>{c.course_code} — {c.title}</strong><div className="muted">{programmeMap.get(c.programme_id)?.title || `Programme #${c.programme_id}`} · {c.duration_hours}h · {c.delivery_mode} · {c.level}</div></div><span>{mods.length} modules</span></div>{mods.map(m=>{const lessons=courseLessons.filter(l=>l.module_id===m.id); return <div key={m.id} style={{padding:'10px 0',borderTop:'1px solid var(--border)'}}><strong>Module {m.module_number}: {m.title}</strong><div className="muted">{m.learning_objectives || 'No objectives added'} · {lessons.length} lessons</div>{lessons.map(l=><div key={l.id} style={{padding:'5px 0 0 16px',fontSize:13}}>Lesson {l.lesson_number}: {l.title} <span className="muted">({l.content_type}, {l.duration_minutes} min{l.is_mandatory ? ', mandatory' : ''})</span></div>)}</div>})}</div>})}
        </div>
      </div>
    </section>
    <section className="panel" style={{marginBottom:0}}>
      <div className="panel-title"><div><h3>Timetable & Session Scheduling</h3><p className="muted" style={{margin:'4px 0 0',fontSize:12}}>ERP-08 • Schedule batch sessions and open the linked attendance session when ready.</p></div><span>ERP-08</span></div>
      {canManage && <form className="career-form" onSubmit={submitSchedule} style={{marginTop:12}}>
        <div className="form-row">
          <label>Batch<select value={scheduleForm.batch_id} onChange={e=>{
            const batchId=Number(e.target.value);
            const batch=batches.find(x=>x.id===batchId);
            const firstCourse=batch ? courses.find(c=>c.programme_id===batch.programme_id) : undefined;
            const firstModule=firstCourse ? courseModules.find(m=>m.course_id===firstCourse.id) : undefined;
            setScheduleForm(x=>({...x,batch_id:batchId,course_id:firstCourse?.id??0,module_id:firstModule?.id??0,trainer_id:batch?.trainer_id?String(batch.trainer_id):'',session_date:batch?.start_date??x.session_date,venue:batch?.venue??x.venue}));
          }} required>{batches.map(b=><option key={b.id} value={b.id}>{b.batch_code}</option>)}</select></label>
          <label>Course<select value={scheduleForm.course_id} onChange={e=>{
            const courseId=Number(e.target.value);
            const firstModule=courseModules.find(m=>m.course_id===courseId);
            setScheduleForm(x=>({...x,course_id:courseId,module_id:firstModule?.id??0}));
          }}><option value={0}>No course</option>{scheduleCourses.map(c=><option key={c.id} value={c.id}>{c.course_code} — {c.title}</option>)}</select></label>
        </div>
        <div className="form-row">
          <label>Module<select value={scheduleForm.module_id} onChange={e=>setScheduleForm({...scheduleForm,module_id:Number(e.target.value)})}><option value={0}>No module</option>{scheduleModules.map(m=><option key={m.id} value={m.id}>M{m.module_number} — {m.title}</option>)}</select></label>
          <label>Trainer ID<input type="number" min="1" value={scheduleForm.trainer_id} onChange={e=>setScheduleForm({...scheduleForm,trainer_id:e.target.value})} placeholder="Optional; defaults to batch trainer" /><span className="muted">Leave unchanged to use the batch trainer.</span></label>
        </div>
        <div className="form-row"><label>Date<input type="date" min={selectedScheduleBatch?.start_date} max={selectedScheduleBatch?.end_date} value={scheduleForm.session_date} onChange={e=>setScheduleForm({...scheduleForm,session_date:e.target.value})} required /><span className="muted">Batch: {selectedScheduleBatch?.start_date || "—"} to {selectedScheduleBatch?.end_date || "—"}</span></label><label>Topic<input value={scheduleForm.topic} onChange={e=>setScheduleForm({...scheduleForm,topic:e.target.value})} placeholder="Digital Cooperative Records" required /></label></div>
        <div className="form-row"><label>Start<input type="time" value={scheduleForm.start_time} onChange={e=>setScheduleForm({...scheduleForm,start_time:e.target.value})} required /></label><label>End<input type="time" value={scheduleForm.end_time} onChange={e=>setScheduleForm({...scheduleForm,end_time:e.target.value})} required /></label></div>
        <div className="form-row"><label>Venue<input value={scheduleForm.venue} onChange={e=>setScheduleForm({...scheduleForm,venue:e.target.value})} placeholder="Training Hall 1" /></label><label>Mode<select value={scheduleForm.mode} onChange={e=>setScheduleForm({...scheduleForm,mode:e.target.value})}><option>IN_PERSON</option><option>ONLINE</option><option>HYBRID</option></select></label></div>
        <label>Notes<textarea value={scheduleForm.notes} onChange={e=>setScheduleForm({...scheduleForm,notes:e.target.value})} rows={2} /></label>
        <button className="primary">Schedule session</button>
      </form>}
      <div className="table-wrap" style={{marginTop:12}}><table><thead><tr><th>Date</th><th>Time</th><th>Batch</th><th>Topic</th><th>Course / Module</th><th>Venue</th><th>Trainer</th>{canManage&&<th>Attendance</th>}</tr></thead><tbody>
        {schedules.map(s=><tr key={s.id}><td>{s.session_date}</td><td>{String(s.start_time).slice(0,5)}–{String(s.end_time).slice(0,5)}</td><td>{s.batch_code}</td><td><strong>{s.topic}</strong><div className="muted">{s.mode} · {s.status}</div></td><td>{s.course_title||'—'}{s.module_title&&<div className="muted">{s.module_title}</div>}</td><td>{s.venue||'—'}</td><td>{s.trainer_name||'—'}</td>{canManage&&<td>{s.attendance_session_id?<span className="status-badge present">Linked</span>:<button className="small-btn" onClick={()=>linkAttendance(s.id)}>Open attendance</button>}</td>}</tr>)}
        {!schedules.length&&<tr><td colSpan={canManage?8:7} className="empty">No training sessions scheduled yet.</td></tr>}
      </tbody></table></div>
    </section>
    <div className="panel"><div className="panel-title"><h3>Enrollment register</h3><span>ERP-05</span></div><div className="table-wrap"><table><thead><tr><th>Batch</th><th>Programme</th><th>Trainee</th><th>Status</th><th>Enrolled</th></tr></thead><tbody>{enrollments.map(e => { const b=batchMap.get(e.batch_id); return <tr key={e.id}><td>{b?.batch_code || `#${e.batch_id}`}</td><td>{b ? programmeMap.get(b.programme_id)?.title : '—'}</td><td>#{e.trainee_id}</td><td><span className={`status-badge ${e.status.toLowerCase()}`}>{e.status}</span></td><td>{new Date(e.enrolled_at).toLocaleDateString()}</td></tr>; })}{!enrollments.length && <tr><td colSpan={5} className="empty">No enrollments yet.</td></tr>}</tbody></table></div></div>
  </div>;
}
