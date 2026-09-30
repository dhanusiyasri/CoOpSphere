import { useEffect, useState } from 'react';
import { getIntelligenceOverview, getInstitutions, getProgrammeDetail, getTrainers, IntelligenceOverview, InstitutionSummary, ProgrammeDetail, TrainerSummary } from './api';
import { IntelligenceAssistant } from './Assistant';

type Props={user:{role:string}};
function Metric({label,value}:{label:string;value:string|number}){return <div className="intel-metric"><span>{label}</span><strong>{value}</strong></div>}
export function Intelligence({user}:Props){
 const canViewAnalytics=user.role==='NCCT_ADMIN'||user.role==='INSTITUTE_ADMIN'||user.role==='TRAINER';
 const canUseAssistant=canViewAnalytics||user.role==='TRAINEE';
 const [data,setData]=useState<IntelligenceOverview|null>(null),[institutions,setInstitutions]=useState<InstitutionSummary[]>([]),[trainers,setTrainers]=useState<TrainerSummary[]>([]),[detail,setDetail]=useState<ProgrammeDetail|null>(null),[tab,setTab]=useState<'overview'|'institutions'|'trainers'|'assistant'>(canViewAnalytics?'overview':'assistant'),[loading,setLoading]=useState(canViewAnalytics),[error,setError]=useState('');
 async function load(){
  if(!canViewAnalytics){setLoading(false);return;}
  setLoading(true);setError('');
  try{
   const [o,i,t]=await Promise.all([getIntelligenceOverview(),getInstitutions(),getTrainers()]);
   setData(o);setInstitutions(i);setTrainers(t);
  }catch(e:any){setError(e.response?.data?.detail||'Unable to load intelligence dashboard')}
  finally{setLoading(false)}
 }
 useEffect(()=>{load()},[canViewAnalytics]);
 if(loading)return <section className="panel"><h2>Intelligence & Analytics</h2><p className="muted">Loading operational indicators…</p></section>;
 if(error)return <section className="panel"><h2>Intelligence & Analytics</h2><div className="error">{error}</div><button className="primary" onClick={load}>Retry</button></section>;
 if(!canUseAssistant)return <section className="panel"><h2>Intelligence & Analytics</h2><div className="error">This workspace is not available for your role.</div></section>;
 const statuses=['APPLIED','SHORTLISTED','INTERVIEW','SELECTED','REJECTED'];
 if(!canViewAnalytics) return <section className="intelligence-shell">
  <div className="panel intelligence-hero"><div><p className="eyebrow">NCCT LEARNING & CAREER SUPPORT • INTELLIGENCE-03</p><h2>AI Training & Career Assistant</h2><p className="muted">Ask questions about your NCCT learning, attendance, credentials and employment information.</p></div><div className="intel-role">{user.role}<span>assistant access</span></div></div>
  <IntelligenceAssistant role={user.role}/>
  <div className="intel-footnote">Responses are grounded in the NCCT records available to your account.</div>
 </section>;
 if(!data)return null;
 return <section className="intelligence-shell">
  <div className="panel intelligence-hero"><div><p className="eyebrow">CENTRALIZED INTELLIGENCE • INTELLIGENCE-02</p><h2>Capacity & Employment Intelligence</h2><p className="muted">Operational indicators with institution, trainer and programme drill-downs.</p></div><div className="intel-role">{user.role}<span>analytics access</span></div></div>
  <div className="intel-tabs"><button className={tab==='overview'?'active':''} onClick={()=>setTab('overview')}>Overview</button><button className={tab==='institutions'?'active':''} onClick={()=>setTab('institutions')}>Institutions</button><button className={tab==='trainers'?'active':''} onClick={()=>setTab('trainers')}>Trainers</button><button className={tab==='assistant'?'active':''} onClick={()=>setTab('assistant')}>AI Assistant</button></div>
  {tab==='overview'&&<>
   <div className="intel-grid"><Metric label="Trainees" value={data.trainees}/><Metric label="Programmes" value={data.programmes}/><Metric label="Batches" value={data.batches}/><Metric label="Active enrollments" value={data.active_enrollments}/><Metric label="Courses" value={data.courses}/><Metric label="Credentials issued" value={data.credentials_issued}/></div>
   <div className="intel-two-col"><div className="panel intel-card"><div className="panel-heading"><div><h3>Learning activity</h3><p className="muted">Persisted LMS lesson completion records.</p></div><strong className="intel-big">{data.lesson_activity_rate}%</strong></div><div className="progress-track"><div className="progress-fill" style={{width:`${Math.min(100,data.lesson_activity_rate)}%`}}/></div><div className="intel-inline"><span>{data.completed_lesson_records} completed lesson records</span><span>{data.lessons} lesson definitions</span></div></div><div className="panel intel-card"><div className="panel-heading"><div><h3>Assessment performance</h3><p className="muted">Submitted assessment attempts and pass results.</p></div><strong className="intel-big">{data.assessment_pass_rate}%</strong></div><div className="progress-track"><div className="progress-fill" style={{width:`${Math.min(100,data.assessment_pass_rate)}%`}}/></div><div className="intel-inline"><span>{data.assessment_passes} passes</span><span>{data.assessment_attempts} attempts</span></div></div></div>
   <div className="intel-two-col"><div className="panel intel-card"><div className="panel-heading"><div><h3>Employment pipeline</h3><p className="muted">Current application status counts.</p></div><strong className="intel-big">{data.placement_conversion_rate}%</strong></div><div className="status-list">{statuses.map(s=><div key={s}><span>{s}</span><strong>{data.application_statuses[s]||0}</strong></div>)}</div><div className="intel-inline"><span>{data.published_jobs} published jobs</span><span>{data.job_applications} total applications</span></div></div><div className="panel intel-card"><div className="panel-heading"><div><h3>Programme register</h3><p className="muted">Select a programme for operational drill-down.</p></div></div><div className="intel-table">{data.programme_summary.map(r=><button className="intel-row intel-row-button" key={r.id} onClick={async()=>setDetail(await getProgrammeDetail(r.id))}><div><strong>{r.code}</strong><span>{r.title}</span></div><span>{r.batch_count} batch{r.batch_count===1?'':'es'} →</span></button>)}</div></div></div>
  </>}
  {tab==='institutions'&&<div className="panel intel-card"><div className="panel-heading"><div><h3>Institution drill-down</h3><p className="muted">Training activity grouped by institution.</p></div></div><div className="intel-table">{institutions.map(i=><div className="intel-row" key={i.id}><div><strong>{i.name}</strong><span>{i.institution_type} • {i.state||'State not set'}{i.district?` • ${i.district}`:''}</span></div><span>{i.programme_count} programmes · {i.batch_count} batches · {i.trainee_count} trainees · {i.active_enrollment_count} active</span></div>)}{!institutions.length&&<p className="muted">No institutions found.</p>}</div></div>}
  {tab==='trainers'&&<div className="panel intel-card"><div className="panel-heading"><div><h3>Trainer drill-down</h3><p className="muted">Assigned batches and distinct trainees by trainer.</p></div></div><div className="intel-table">{trainers.map(t=><div className="intel-row" key={t.id}><div><strong>{t.full_name}</strong><span>{t.email}</span></div><span>{t.batch_count} batches · {t.active_batch_count} active · {t.trainee_count} trainees</span></div>)}{!trainers.length&&<p className="muted">No active trainers found.</p>}</div></div>}
  {tab==='assistant'&&<IntelligenceAssistant role={user.role}/>}
  {detail&&<div className="panel intel-card intel-detail"><div className="panel-heading"><div><p className="eyebrow">PROGRAMME DETAIL</p><h3>{detail.code} · {detail.title}</h3><p className="muted">{detail.institution_name} · {detail.category} · {detail.mode}</p></div><button onClick={()=>setDetail(null)}>Close</button></div><div className="intel-grid"><Metric label="Batches" value={detail.batch_count}/><Metric label="Courses" value={detail.course_count}/><Metric label="Trainees" value={detail.trainee_count}/><Metric label="Active enrollments" value={detail.active_enrollment_count}/><Metric label="Completed lessons" value={detail.completed_lesson_records}/><Metric label="Credentials" value={detail.credential_count}/></div><div className="intel-table">{detail.batches.map(b=><div className="intel-row" key={b.id}><div><strong>{b.batch_code}</strong><span>{b.start_date} → {b.end_date} · {b.venue||'Venue not set'}</span></div><span>{b.status} · {b.enrollment_count}/{b.capacity} enrolled</span></div>)}</div></div>}
  <div className="intel-footnote">Metrics are descriptive operational counts from the current NCCT database; they are not forecasts or performance rankings.</div>
 </section>
}
