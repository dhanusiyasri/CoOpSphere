import { useEffect, useRef, useState } from 'react';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { AttendanceRecord, AttendanceSession, checkIn, createSession, getQr, getRoster, getSessions, markAttendance } from './api';
import { AttendanceReports } from './AttendanceReports';

type User={id:number;full_name:string;email:string;role:string};

export function Attendance({user}:{user:User}){
 const manager=['NCCT_ADMIN','INSTITUTE_ADMIN','TRAINER'].includes(user.role);
 const [sessions,setSessions]=useState<AttendanceSession[]>([]); const [selected,setSelected]=useState<AttendanceSession|null>(null); const [roster,setRoster]=useState<AttendanceRecord[]>([]); const [qr,setQr]=useState(''); const [message,setMessage]=useState('');
 const [view,setView]=useState<'operations'|'reports'>('operations');
 const [form,setForm]=useState({batch_id:1,session_date:new Date().toISOString().slice(0,10),start_time:'09:00',end_time:'10:00',topic:'Cooperative training session',notes:'',status:'OPEN'});
 const [code,setCode]=useState('');
 const [scannerOpen,setScannerOpen]=useState(false);
 const [scannerMessage,setScannerMessage]=useState('');
 const scannerRef=useRef<any>(null);
 const scanHandledRef=useRef(false);

 async function load(){try{setSessions(await getSessions())}catch(e:any){setMessage(e.response?.data?.detail||'Could not load attendance sessions')}}
 useEffect(()=>{load()},[]);

 async function select(s:AttendanceSession){setSelected(s);setMessage(''); if(manager){try{setRoster(await getRoster(s.id)); const q=await getQr(s.id); setQr(q.data_url)}catch(e:any){setMessage(e.response?.data?.detail||'Could not load attendance roster')}}}
 async function submit(){try{await createSession(form as any);setMessage('Attendance session created.');await load()}catch(e:any){setMessage(e.response?.data?.detail||'Could not create session')}}
 async function mark(r:AttendanceRecord,status:string){try{const updated=await markAttendance(r.session_id,{trainee_id:r.trainee_id,status});setRoster(xs=>xs.map(x=>x.trainee_id===r.trainee_id?updated:x));setMessage(`${r.trainee_name}: ${status}`)}catch(e:any){setMessage(e.response?.data?.detail||'Could not update attendance')}}

 async function stopScanner(){
  const scanner=scannerRef.current;
  scannerRef.current=null;
  if(scanner){try{await scanner.stop()}catch{} try{scanner.clear()}catch{}}
  setScannerOpen(false);
 }

 useEffect(()=>{
  if(!scannerOpen) return;
  let cancelled=false;
  scanHandledRef.current=false;
  const scanner=new Html5Qrcode('attendance-qr-reader',{formatsToSupport:[Html5QrcodeSupportedFormats.QR_CODE]});
  scannerRef.current=scanner;

  async function start(){
   setScannerMessage('Requesting camera permission…');
   try{
    const cameras=await Html5Qrcode.getCameras();
    if(cancelled) return;
    if(!cameras.length) throw new Error('NO_CAMERA');
    const preferred=cameras.find((c: {label:string})=>/back|rear|environment/i.test(c.label)) || cameras[0];
    await scanner.start(
      preferred.id,
      {fps:10,qrbox:{width:250,height:250},aspectRatio:1.333334},
      async(decodedText: string)=>{
       if(cancelled || scanHandledRef.current) return;
       scanHandledRef.current=true;
       const prefix='NCCT_ATTENDANCE:';
       const detected=decodedText.startsWith(prefix)?decodedText.slice(prefix.length):decodedText;
       setCode(detected.toUpperCase());
       await stopScanner();
       try{const r=await checkIn(detected);setMessage(`Checked in: ${r.status} via ${r.method}`);await load()}catch(e:any){setMessage(e.response?.data?.detail||'Check-in failed')}
      },
      ()=>{}
    );
    if(!cancelled) setScannerMessage('Camera active. Point the camera at the trainer QR code.');
   }catch(e:any){
    if(cancelled) return;
    const detail=e?.name==='NotAllowedError'?'Camera permission was denied. Allow camera access and try again.':e?.message==='NO_CAMERA'?'No camera was detected on this device. Use the access code below.':'Could not start the camera. Use the access code below.';
    setScannerMessage(detail);
   }
  }
  start();
  return ()=>{
   cancelled=true;
   const current=scannerRef.current;
   scannerRef.current=null;
   if(current){current.stop().catch(()=>{}).finally(()=>{try{current.clear()}catch{}})}
  };
 },[scannerOpen]);

 async function selfCheck(){try{const r=await checkIn(code);setMessage(`Checked in: ${r.status} via ${r.method}`);setCode('');await load()}catch(e:any){setMessage(e.response?.data?.detail||'Check-in failed')}}

 return <div className="attendance-shell"><div className="panel attendance-hero"><div><p className="eyebrow">TRAINING OPERATIONS • ATTENDANCE-{view==='reports'?'03':'01'}</p><h2>{view==='reports'?(manager?'Attendance Reports & Analytics':'My Attendance Report'):(manager?'Attendance & Session Register':'My Attendance')}</h2><p className="muted">{view==='reports'?'Session, batch and trainee attendance analytics with exportable reports.':'Track batch sessions and attendance records with an access-code/QR-ready check-in flow.'}</p></div><div className="pill">{user.role}</div></div><div className="attendance-tabs"><button className={view==='operations'?'active':''} onClick={()=>setView('operations')}>Session operations</button><button className={view==='reports'?'active':''} onClick={()=>setView('reports')}>Reports & analytics</button></div>{view==='reports'?<AttendanceReports user={user}/>:<>{message&&<div className="notice">{message}</div>}
 {manager&&<div className="two-col"><form className="panel form-panel" onSubmit={e=>{e.preventDefault();submit()}}><div className="panel-title"><h3>Create session</h3><span>ATT-01</span></div><label>Batch ID<input type="number" min="1" value={form.batch_id} onChange={e=>setForm({...form,batch_id:Number(e.target.value)})}/></label><div className="form-row"><label>Date<input type="date" value={form.session_date} onChange={e=>setForm({...form,session_date:e.target.value})}/></label><label>Status<select value={form.status} onChange={e=>setForm({...form,status:e.target.value})}><option>OPEN</option><option>SCHEDULED</option><option>CLOSED</option></select></label></div><div className="form-row"><label>Start<input type="time" value={form.start_time} onChange={e=>setForm({...form,start_time:e.target.value})}/></label><label>End<input type="time" value={form.end_time} onChange={e=>setForm({...form,end_time:e.target.value})}/></label></div><label>Topic<input value={form.topic} onChange={e=>setForm({...form,topic:e.target.value})}/></label><label>Notes<textarea value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label><button className="primary">Create session</button></form><div className="panel"><div className="panel-title"><h3>Session access</h3><span>QR READY</span></div>{selected?<><p className="muted">Access code: <strong>{selected.access_code}</strong></p>{qr&&<img className="attendance-qr" src={qr} alt="Attendance QR code"/>}<p className="muted">The QR payload is NCCT_ATTENDANCE:{selected.access_code}. Camera scanning is available on supported browsers/devices.</p></>:<p className="muted">Select an attendance session to display its access code and QR.</p>}</div></div>}
 {!manager&&<div className="panel form-panel"><div className="panel-title"><h3>Check in</h3><span>QR / CAMERA / CODE</span></div><p className="muted">Scan the trainer's QR code with your camera or enter the session access code manually. QR check-in is stored as method QR.</p>{scannerOpen&&<div className="attendance-scanner"><div id="attendance-qr-reader" className="attendance-qr-reader"/><div className="button-row"><button type="button" className="secondary" onClick={()=>stopScanner()}>Stop camera</button></div></div>}{scannerMessage&&<div className="notice">{scannerMessage}</div>}<div className="button-row"><button type="button" className="secondary" onClick={()=>{setScannerMessage('');setScannerOpen(true)}} disabled={scannerOpen}>Scan QR with camera</button></div><label>Attendance code<input value={code} onChange={e=>setCode(e.target.value.toUpperCase())} placeholder="8-character code"/></label><button className="primary" onClick={selfCheck}>Check in</button></div>}
 <div className="panel"><div className="panel-title"><h3>{manager?'Attendance sessions':'Available sessions'}</h3><span>{sessions.length}</span></div><div className="attendance-session-list">{sessions.map(s=><button key={s.id} className={selected?.id===s.id?'attendance-session selected':'attendance-session'} onClick={()=>select(s)}><div><strong>{s.topic}</strong><span>Batch #{s.batch_id} • {s.session_date} • {s.start_time}–{s.end_time}</span></div><b>{s.status}</b></button>)}</div></div>
 {manager&&selected&&<><div className="panel attendance-summary"><div className="panel-title"><h3>Attendance summary</h3><span>{roster.length} trainees</span></div><div className="attendance-summary-grid"><div><strong>{roster.filter(r=>r.status==='PRESENT').length}</strong><span>Present</span></div><div><strong>{roster.filter(r=>r.status==='LATE').length}</strong><span>Late</span></div><div><strong>{roster.filter(r=>r.status==='ABSENT').length}</strong><span>Absent</span></div><div><strong>{roster.length?Math.round((roster.filter(r=>['PRESENT','LATE'].includes(r.status)).length/roster.length)*100):0}%</strong><span>Attendance rate</span></div></div></div><div className="panel"><div className="panel-title"><h3>Attendance roster</h3><span>{roster.length}</span></div><div className="attendance-roster">{roster.map(r=><div className="attendance-row" key={r.trainee_id}><div><strong>{r.trainee_name}</strong><span>{r.trainee_email}</span></div><div className="button-row"><b className="status-badge">{r.status}</b><button className="secondary" onClick={()=>mark(r,'PRESENT')}>Present</button><button className="secondary" onClick={()=>mark(r,'LATE')}>Late</button><button className="secondary" onClick={()=>mark(r,'ABSENT')}>Absent</button></div></div>)}</div></div></>}
 </> }</div>
}
