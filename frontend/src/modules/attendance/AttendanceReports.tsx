import { useEffect, useState } from 'react';
import { AttendanceReport, LowAttendanceAlert, getAttendanceReport, getLowAttendanceAlerts } from './api';

type User={id:number;full_name:string;email:string;role:string};

function csvCell(value:unknown){
 const text=String(value ?? '');
 return /[",\n]/.test(text) ? `"${text.replace(/"/g,'""')}"` : text;
}

function downloadCsv(filename:string, rows:string[][]){
 const csv=rows.map(row=>row.map(csvCell).join(',')).join('\n');
 const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob);
 const a=document.createElement('a'); a.href=url; a.download=filename; a.click(); URL.revokeObjectURL(url);
}

export function AttendanceReports({user}:{user:User}){
 const manager=['NCCT_ADMIN','INSTITUTE_ADMIN','TRAINER'].includes(user.role);
 const [fromDate,setFromDate]=useState('');
 const [toDate,setToDate]=useState('');
 const [batchId,setBatchId]=useState('');
 const [report,setReport]=useState<AttendanceReport|null>(null);
 const [loading,setLoading]=useState(false);
 const [message,setMessage]=useState('');
 const [threshold,setThreshold]=useState('75');
 const [alerts,setAlerts]=useState<LowAttendanceAlert[]>([]);
 const [alertsLoading,setAlertsLoading]=useState(false);

 async function load(){
  setLoading(true); setMessage('');
  try{
   setReport(await getAttendanceReport({from_date:fromDate||undefined,to_date:toDate||undefined,batch_id:batchId?Number(batchId):undefined},!manager));
   if(manager){
    setAlertsLoading(true);
    try{const a=await getLowAttendanceAlerts({threshold:Number(threshold)||75,from_date:fromDate||undefined,to_date:toDate||undefined,batch_id:batchId?Number(batchId):undefined});setAlerts(a.alerts)}finally{setAlertsLoading(false)}
   }
  } catch(e:any){
   const status=e.response?.status;
   setMessage(status===404?'Attendance Reports API is not loaded in the running backend. Restart the backend, then refresh this page.':e.response?.data?.detail||'Could not load attendance report');
  }
  finally{setLoading(false)}
 }
 useEffect(()=>{load()},[]);

 function exportTrainees(){
  if(!report)return;
  downloadCsv('ncct-attendance-trainee-report.csv',[
   ['Trainee ID','Trainee Name','Email','Sessions','Present','Late','Absent','Excused','Attendance Rate %','Last Check-in'],
   ...report.trainees.map(r=>[String(r.trainee_id),r.trainee_name,r.trainee_email,String(r.total_sessions),String(r.present),String(r.late),String(r.absent),String(r.excused),String(r.attendance_rate),r.last_check_in_at||''])
  ]);
 }
 function exportSessions(){
  if(!report)return;
  downloadCsv('ncct-attendance-session-report.csv',[
   ['Session ID','Batch','Date','Start','End','Topic','Status','Roster','Present','Late','Absent','Excused','Attendance Rate %'],
   ...report.sessions.map(r=>[String(r.session_id),r.batch_code,r.session_date,r.start_time,r.end_time,r.topic,r.status,String(r.roster_count),String(r.present),String(r.late),String(r.absent),String(r.excused),String(r.attendance_rate)])
  ]);
 }
 return <div className="attendance-reports">
  <div className="panel attendance-report-filter">
   <div className="panel-heading"><div><h3>{manager?'Attendance reports & analytics':'My attendance report'}</h3><p className="muted">{manager?'Review attendance by batch, session and trainee, with CSV export.':'Review your attendance history and export your personal report.'}</p></div><span className="pill">ATT-03</span></div>
   <div className="attendance-report-filters">
    <label>From date<input type="date" value={fromDate} onChange={e=>setFromDate(e.target.value)}/></label>
    <label>To date<input type="date" value={toDate} onChange={e=>setToDate(e.target.value)}/></label>
    {manager&&<label>Batch ID<input type="number" min="1" placeholder="All batches" value={batchId} onChange={e=>setBatchId(e.target.value)}/></label>}
    <div className="button-row attendance-report-actions"><button className="primary" type="button" onClick={load} disabled={loading}>{loading?'Loading…':'Apply filters'}</button>{report&&<><button className="secondary" type="button" onClick={exportSessions}>Export sessions CSV</button><button className="secondary" type="button" onClick={exportTrainees}>Export trainee CSV</button></>}</div>
   </div>
   {message&&<div className="notice">{message}</div>}
  </div>
  {report&&<>
   <div className="attendance-summary-grid attendance-report-summary">
    <div><strong>{report.summary.attendance_rate}%</strong><span>Attendance rate</span></div>
    <div><strong>{report.summary.total_sessions}</strong><span>Sessions</span></div>
    <div><strong>{report.summary.present}</strong><span>Present</span></div>
    <div><strong>{report.summary.late}</strong><span>Late</span></div>
    <div><strong>{report.summary.absent}</strong><span>Absent</span></div>
    <div><strong>{report.summary.exceptions}</strong><span>Exceptions</span></div>
   </div>
   {manager&&<div className="panel"><div className="panel-title"><h3>Batch performance</h3><span>{report.batches.length}</span></div><div className="attendance-report-table"><div className="attendance-report-table-head"><span>Batch</span><span>Sessions</span><span>Trainees</span><span>Present</span><span>Late</span><span>Absent</span><span>Rate</span></div>{report.batches.map(b=><div className="attendance-report-table-row" key={b.batch_id}><strong>{b.batch_code}</strong><span>{b.total_sessions}</span><span>{b.enrolled_trainees}</span><span>{b.present}</span><span>{b.late}</span><span>{b.absent}</span><b>{b.attendance_rate}%</b></div>)}</div></div>}
   <div className="panel"><div className="panel-title"><h3>{manager?'Trainee attendance':'My attendance'}</h3><span>{report.trainees.length}</span></div><div className="attendance-report-table"><div className="attendance-report-table-head"><span>Trainee</span><span>Sessions</span><span>Present</span><span>Late</span><span>Absent</span><span>Excused</span><span>Rate</span></div>{report.trainees.map(t=><div className="attendance-report-table-row" key={t.trainee_id}><div><strong>{t.trainee_name}</strong><small>{t.trainee_email}</small></div><span>{t.total_sessions}</span><span>{t.present}</span><span>{t.late}</span><span>{t.absent}</span><span>{t.excused}</span><b>{t.attendance_rate}%</b></div>)}</div></div>
   {manager&&<div className="panel"><div className="panel-title"><div><h3>Low-attendance alerts</h3><p className="muted">Trainees below the selected attendance threshold.</p></div><div className="attendance-alert-controls"><label>Threshold %<input type="number" min="0" max="100" value={threshold} onChange={e=>setThreshold(e.target.value)}/></label><button className="secondary" type="button" onClick={load} disabled={alertsLoading}>{alertsLoading?'Checking…':'Refresh alerts'}</button></div></div>{alerts.length===0?<div className="notice">No trainees are below {Number(threshold)||75}% for the selected filters.</div>:<div className="attendance-report-table"><div className="attendance-report-table-head"><span>Trainee</span><span>Batch</span><span>Sessions</span><span>Present</span><span>Late</span><span>Absent</span><span>Rate</span></div>{alerts.map(a=><div className="attendance-report-table-row" key={`${a.trainee_id}-${a.batch_id}`}><div><strong>{a.trainee_name}</strong><small>{a.trainee_email}</small></div><span>{a.batch_code}</span><span>{a.total_sessions}</span><span>{a.present}</span><span>{a.late}</span><span>{a.absent}</span><b>{a.attendance_rate}%</b></div>)}</div>}</div>}
   <div className="panel"><div className="panel-title"><h3>Session report</h3><span>{report.sessions.length}</span></div><div className="attendance-report-table attendance-session-report"><div className="attendance-report-table-head"><span>Session</span><span>Date</span><span>Batch</span><span>Present</span><span>Late</span><span>Absent</span><span>Rate</span></div>{report.sessions.map(s=><div className="attendance-report-table-row" key={s.session_id}><div><strong>{s.topic}</strong><small>{s.start_time}–{s.end_time} • {s.status}</small></div><span>{s.session_date}</span><span>{s.batch_code}</span><span>{s.present}</span><span>{s.late}</span><span>{s.absent}</span><b>{s.attendance_rate}%</b></div>)}</div></div>
  </>}
 </div>
}
