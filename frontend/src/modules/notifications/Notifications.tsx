import { useEffect, useState } from 'react';
import { api } from '../training/api';

type User={id:number;full_name:string;email:string;role:string};
type Notice={id:string;kind:string;title:string;message:string;priority:'HIGH'|'MEDIUM'|'INFO';action?:string|null};

export function Notifications({user,onNavigate}:{user:User;onNavigate:(section:string)=>void}){
 const [items,setItems]=useState<Notice[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState('');
 async function load(){setLoading(true);setError('');try{setItems((await api.get<Notice[]>('/notifications')).data);}catch(e:any){setError(e.response?.data?.detail||'Could not load action center');}finally{setLoading(false);}}
 useEffect(()=>{load();},[user.id]);
 const high=items.filter(x=>x.priority==='HIGH').length;
 return <section className="notifications-shell">
  <section className="panel notifications-hero"><div><p className="eyebrow">NCCT ACTION CENTER</p><h2>Notifications & Action Center</h2><p className="muted">Role-aware reminders and actions generated from your current training, attendance, learning and employment activity.</p></div><div className="career-stat"><strong>{high||items.length}</strong><span>{high?'priority actions':'active notices'}</span></div></section>
  {error&&<div className="error">{error}</div>}
  <section className="panel"><div className="section-heading"><div><h3>Needs your attention</h3><p className="muted">Select an action to jump directly to the relevant workspace.</p></div><button className="secondary" onClick={load} disabled={loading}>Refresh</button></div>
   {loading?<div className="empty">Loading your action center…</div>:!items.length?<div className="empty-state"><h3>You're all caught up</h3><p className="muted">No current alerts or actions were generated for your role.</p></div>:<div className="notification-list">{items.map(n=><div className={`notification-card priority-${n.priority.toLowerCase()}`} key={n.id}><div className="notification-icon">{n.kind==='ATTENDANCE'?'◷':n.kind==='LEARNING'?'▤':n.kind==='CAREER'?'↗':n.kind==='SESSION'?'◫':n.kind==='NOMINATION'?'✓':n.kind==='PLACEMENT'?'◇':'•'}</div><div className="notification-copy"><div className="notification-top"><strong>{n.title}</strong><span className="status-badge">{n.priority}</span></div><p>{n.message}</p>{n.action&&n.action!=='Notifications'&&<button className="secondary" onClick={()=>onNavigate(n.action!)}>Open {n.action}</button>}</div></div>)}</div>}
  </section>
 </section>;
}
