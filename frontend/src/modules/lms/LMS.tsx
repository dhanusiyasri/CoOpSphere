import { Dispatch, SetStateAction, useEffect, useMemo, useState } from 'react';
import {
  Assessment,
  AssessmentAttempt,
  CourseDetail,
  Lesson,
  MyCourse,
  completeLesson,
  getCourse,
  getLatestAssessmentResult,
  getLessonAssessment,
  getMyCourses,
  startLesson,
  submitAssessment,
} from './api';
import { issueCredential } from '../credentials/api';

type User = { id: number; full_name: string; email: string; role: string };

function ProgressBar({ value }: { value: number }) {
  return <div className="progress"><span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>;
}

export function LMS({ user }: { user: User }) {
  const [courses, setCourses] = useState<MyCourse[]>([]);
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [attempt, setAttempt] = useState<AssessmentAttempt | null>(null);
  const [assessmentMode, setAssessmentMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [busyLessonId, setBusyLessonId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [credentialLoading, setCredentialLoading] = useState(false);

  async function loadCourses(preferredId?: number | null) {
    const data = await getMyCourses();
    setCourses(data);
    const id = preferredId ?? selectedCourseId ?? data[0]?.course_id ?? null;
    if (id) await loadCourse(id);
  }

  async function loadCourse(id: number) {
    const data = await getCourse(id);
    setCourse(data);
    setSelectedCourseId(id);
    setSelectedLessonId(current => {
      const available = data.modules.flatMap(m => m.lessons);
      return available.some(l => l.id === current) ? current : available[0]?.id ?? null;
    });
  }

  useEffect(() => {
    if (user.role !== 'TRAINEE') return;
    setLoading(true);
    getMyCourses().then(async data => {
      setCourses(data);
      if (data[0]) await loadCourse(data[0].course_id);
    }).catch(err => setMessage(err.response?.data?.detail || 'Could not load your courses.'))
      .finally(() => setLoading(false));
  }, [user.role]);

  const selectedLesson: Lesson | null = useMemo(() => {
    if (!course || selectedLessonId == null) return null;
    return course.modules.flatMap(m => m.lessons).find(l => l.id === selectedLessonId) || null;
  }, [course, selectedLessonId]);

  async function selectCourse(id: number) {
    setMessage('');
    setAssessment(null); setAttempt(null); setAssessmentMode(false); setAnswers({});
    setSelectedCourseId(id);
    await loadCourse(id);
  }

  async function handleStart() {
    if (!selectedLesson) return;
    setBusyLessonId(selectedLesson.id); setMessage('');
    try {
      await startLesson(selectedLesson.id);
      await loadCourse(course!.id);
      setMessage('Lesson started. Your progress is saved.');
    } catch (err: any) { setMessage(err.response?.data?.detail || 'Could not start the lesson.'); }
    finally { setBusyLessonId(null); }
  }

  async function handleComplete() {
    if (!selectedLesson || !course) return;
    setBusyLessonId(selectedLesson.id); setMessage('');
    try {
      await completeLesson(selectedLesson.id);
      await loadCourse(course.id);
      await loadCourses(course.id);
      setMessage('Lesson completed. Course progress updated.');
    } catch (err: any) { setMessage(err.response?.data?.detail || 'Could not complete the lesson.'); }
    finally { setBusyLessonId(null); }
  }

  async function openAssessment() {
    if (!selectedLesson?.assessment_id) return;
    setAssessmentLoading(true); setMessage(''); setAttempt(null); setAnswers({});
    try {
      const data = await getLessonAssessment(selectedLesson.id);
      setAssessment(data); setAssessmentMode(true);
      try {
        const previous = await getLatestAssessmentResult(data.id);
        setAttempt(previous);
      } catch { /* no prior attempt is expected on first use */ }
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Could not load the assessment.');
    } finally { setAssessmentLoading(false); }
  }

  async function handleClaimCredential() {
    if (!course) return;
    setCredentialLoading(true); setMessage('');
    try {
      const credential = await issueCredential(course.id);
      setMessage(`Credential issued: ${credential.credential_number}. You can view it under Skills & Credentials.`);
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Credential is not yet eligible.');
    } finally { setCredentialLoading(false); }
  }

  async function handleSubmitAssessment() {
    if (!assessment) return;
    setAssessmentLoading(true); setMessage('');
    try {
      const result = await submitAssessment(
        assessment.id,
        assessment.questions.map(q => ({ question_id: q.id, selected_option_id: answers[q.id] }))
      );
      setAttempt(result);
      setMessage('Assessment submitted. Your result has been saved.');
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Could not submit the assessment.');
    } finally { setAssessmentLoading(false); }
  }

  if (user.role !== 'TRAINEE') {
    return <section className="panel"><div className="panel-title"><div><h2>LMS</h2><p className="muted">The LMS learning workspace is available to trainee accounts.</p></div><span>LMS-02</span></div><div className="notice">Sign in with the seeded trainee account to test the learning flow.</div></section>;
  }

  return <section className="lms-shell">
    <div className="panel lms-hero">
      <div><p className="eyebrow">LEARNING MANAGEMENT SYSTEM • LMS-03</p><h2>My Learning</h2><p className="muted">Complete your assigned NCCT courses, track progress and take lesson assessments.</p></div>
      <div className="lms-identity"><strong>{user.full_name}</strong><span>{user.email}</span></div>
    </div>

    {message && <div className="notice">{message}</div>}
    {loading && <div className="panel"><div className="empty">Loading your courses…</div></div>}
    {!loading && !courses.length && <div className="panel empty-state"><h3>No courses assigned yet</h3><p className="muted">Create or publish a course under your enrolled programme in Training ERP, then refresh this page.</p></div>}

    {!loading && courses.length > 0 && <div className="lms-layout">
      <aside className="panel course-list">
        <div className="panel-title"><h3>My Courses</h3><span>{courses.length}</span></div>
        <div className="course-list-items">
          {courses.map(item => <button key={item.course_id} className={`course-card ${selectedCourseId === item.course_id ? 'selected' : ''}`} onClick={() => selectCourse(item.course_id)}>
            <div className="course-card-top"><strong>{item.course_code}</strong><span>{item.progress_percent}%</span></div>
            <div className="course-card-title">{item.title}</div>
            <ProgressBar value={item.progress_percent} />
            <small>{item.completed_lessons} of {item.total_lessons} lessons completed</small>
          </button>)}
        </div>
      </aside>

      {course && <div className="lms-content">
        <div className="panel course-header">
          <div className="course-header-main"><p className="eyebrow">{course.course_code} · {course.level}</p><h2>{course.title}</h2><p className="muted">{course.description || 'NCCT learning course'}</p></div>
          <div className="course-progress-card"><strong>{course.progress_percent}%</strong><span>complete</span><ProgressBar value={course.progress_percent} /><small>{course.completed_lessons}/{course.total_lessons} lessons</small>{course.progress_percent === 100 && <button className="credential-btn" onClick={handleClaimCredential} disabled={credentialLoading}>{credentialLoading ? 'Checking…' : 'Claim completion credential'}</button>}</div>
        </div>

        <div className="lms-workspace">
          <div className="panel module-list">
            <div className="panel-title"><h3>Course content</h3><span>{course.modules.length} modules</span></div>
            {course.modules.map(module => <div className="lms-module" key={module.id}>
              <div className="lms-module-title"><div><strong>Module {module.module_number}: {module.title}</strong><p className="muted">{module.learning_objectives || 'Learning objectives available in this module.'}</p></div><span>{module.duration_minutes} min</span></div>
              <div className="lesson-list">
                {module.lessons.map(lesson => <button key={lesson.id} className={`lesson-item ${selectedLessonId === lesson.id ? 'selected' : ''}`} onClick={() => { setSelectedLessonId(lesson.id); setAssessmentMode(false); setAssessment(null); setAttempt(null); }}>
                  <span className={`lesson-state ${lesson.status.toLowerCase()}`}>{lesson.status === 'COMPLETED' ? '✓' : lesson.status === 'IN_PROGRESS' ? '•' : '○'}</span>
                  <span className="lesson-name"><strong>{lesson.lesson_number}. {lesson.title}</strong><small>{lesson.content_type} · {lesson.duration_minutes} min{lesson.is_mandatory ? ' · Mandatory' : ''}{lesson.assessment_id ? ` · ${lesson.assessment_question_count} Q assessment` : ''}</small></span>
                </button>)}
                {!module.lessons.length && <div className="empty">No lessons in this module.</div>}
              </div>
            </div>)}
          </div>

          <div className="panel lesson-viewer">
            {!selectedLesson ? <div className="empty">Select a lesson to begin.</div> : assessmentMode && assessment ? <AssessmentPanel assessment={assessment} answers={answers} setAnswers={setAnswers} attempt={attempt} onSubmit={handleSubmitAssessment} loading={assessmentLoading} onBack={() => setAssessmentMode(false)} /> : <>
              <div className="lesson-viewer-head"><div><p className="eyebrow">LESSON {selectedLesson.lesson_number}</p><h3>{selectedLesson.title}</h3><p className="muted">{selectedLesson.content_type} · {selectedLesson.duration_minutes} minutes</p></div><span className={`status-badge ${selectedLesson.status.toLowerCase()}`}>{selectedLesson.status.replace('_', ' ')}</span></div>
              <div className="lesson-body">
                {selectedLesson.content_url ? <a className="content-link" href={selectedLesson.content_url} target="_blank" rel="noreferrer">Open lesson resource ↗</a> : <><div className="lesson-placeholder-icon">LMS</div><h3>Learning activity</h3><p className="muted">This lesson supports progress tracking and, where configured, a knowledge assessment.</p></>}
              </div>
              <div className="lesson-actions">
                {selectedLesson.status !== 'COMPLETED' && <button className="primary" disabled={busyLessonId === selectedLesson.id} onClick={handleStart}>{busyLessonId === selectedLesson.id ? 'Saving…' : selectedLesson.status === 'IN_PROGRESS' ? 'Resume lesson' : 'Start lesson'}</button>}
                {selectedLesson.status !== 'COMPLETED' && <button className="small-btn" disabled={busyLessonId === selectedLesson.id} onClick={handleComplete}>Mark complete</button>}
                {selectedLesson.status === 'COMPLETED' && <div className="completion-note">✓ Completed and saved to your LMS record.</div>}
                {selectedLesson.assessment_id && <button className="assessment-btn" onClick={openAssessment} disabled={assessmentLoading}>{assessmentLoading ? 'Loading…' : `Take assessment (${selectedLesson.assessment_question_count} Q)`}</button>}
              </div>
            </>}
          </div>
        </div>
      </div>}
    </div>}
  </section>;
}

function AssessmentPanel({
  assessment, answers, setAnswers, attempt, onSubmit, loading, onBack,
}: {
  assessment: Assessment;
  answers: Record<number, number>;
  setAnswers: Dispatch<SetStateAction<Record<number, number>>>;
  attempt: AssessmentAttempt | null;
  onSubmit: () => void;
  loading: boolean;
  onBack: () => void;
}) {
  return <div className="assessment-panel">
    <div className="assessment-head"><div><p className="eyebrow">ASSESSMENT</p><h3>{assessment.title}</h3><p className="muted">{assessment.question_count} questions · Pass mark {assessment.pass_mark}%</p></div><button className="small-btn" onClick={onBack}>Back to lesson</button></div>
    {assessment.instructions && <div className="assessment-instructions">{assessment.instructions}</div>}
    {attempt && <div className={`assessment-result ${attempt.result.toLowerCase()}`}><strong>{attempt.result === 'PASS' ? 'Passed' : 'Not passed'}</strong><span>{attempt.percentage}% · {attempt.score}/{attempt.max_score} marks · Attempt {attempt.attempt_number}</span></div>}
    <div className="assessment-questions">
      {assessment.questions.map(q => <div className="assessment-question" key={q.id}>
        <div className="question-title"><strong>{q.question_number}. {q.question_text}</strong><span>{q.marks} mark{q.marks === 1 ? '' : 's'}</span></div>
        <div className="assessment-options">
          {q.options.map(option => <label className="assessment-option" key={option.id}><input type="radio" name={`q-${q.id}`} checked={answers[q.id] === option.id} onChange={() => setAnswers(prev => ({ ...prev, [q.id]: option.id }))} /><span>{String.fromCharCode(64 + option.option_number)}. {option.option_text}</span></label>)}
        </div>
      </div>)}
    </div>
    <div className="assessment-actions"><button className="primary" onClick={onSubmit} disabled={loading}>{loading ? 'Submitting…' : 'Submit assessment'}</button><span className="muted">Unanswered questions receive 0 marks.</span></div>
  </div>;
}
