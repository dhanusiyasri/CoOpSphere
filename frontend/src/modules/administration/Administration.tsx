import { useEffect, useMemo, useState } from 'react';
import { createInstitution, getAdminUsers, getInstitutions, updateAdminUser, AdminUser, Institution } from './api';

type User = { id:number; full_name:string; email:string; role:string; institution_id?:number };
const roles = ['NCCT_ADMIN','INSTITUTE_ADMIN','TRAINER','TRAINEE','EMPLOYER'];

export function Administration({ user }: { user: User }) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [tab, setTab] = useState<'users'|'institutions'>('users');
  const [query, setQuery] = useState('');
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({name:'', institution_type:'COOPERATIVE TRAINING INSTITUTE', state:'', district:''});

  async function refresh() {
    if (user.role !== 'NCCT_ADMIN') return;
    const [u, i] = await Promise.all([getAdminUsers(), getInstitutions()]);
    setUsers(u); setInstitutions(i);
  }
  useEffect(() => { refresh().catch(e => setMessage(e.response?.data?.detail || 'Could not load administration data')); }, []);

  const filtered = useMemo(() => users.filter(u => `${u.full_name} ${u.email} ${u.role} ${u.institution_name || ''}`.toLowerCase().includes(query.toLowerCase())), [users, query]);

  async function saveUser(id:number, patch:Partial<AdminUser>) {
    try { await updateAdminUser(id, patch); setMessage('User updated.'); await refresh(); }
    catch(e:any) { setMessage(e.response?.data?.detail || 'User update failed'); }
  }
  async function addInstitution(e:React.FormEvent) {
    e.preventDefault();
    try { await createInstitution(form); setForm({name:'', institution_type:'COOPERATIVE TRAINING INSTITUTE', state:'', district:''}); setMessage('Institution created.'); await refresh(); }
    catch(e:any) { setMessage(e.response?.data?.detail || 'Institution creation failed'); }
  }

  if (user.role !== 'NCCT_ADMIN') return <section className="panel"><p className="eyebrow">ADMINISTRATION</p><h2>Administration access</h2><p className="muted">User and institution administration is restricted to NCCT administrators.</p></section>;

  return <section>
    <div className="panel">
      <div className="section-head"><div><p className="eyebrow">PLATFORM GOVERNANCE • ADMIN-01</p><h2>Administration</h2><p className="muted">Manage platform users, roles, account status and NCCT training institutions.</p></div><div className="metric"><strong>{users.length}</strong><span>users</span></div></div>
      {message && <div className="notice">{message}</div>}
      <div className="tabs"><button className={tab==='users'?'tab active':'tab'} onClick={()=>setTab('users')}>Users</button><button className={tab==='institutions'?'tab active':'tab'} onClick={()=>setTab('institutions')}>Institutions</button></div>
    </div>

    {tab==='users' ? <div className="panel">
      <div className="section-head"><div><h3>User directory</h3><p className="muted">Change role, institution assignment or active status.</p></div><input placeholder="Search users" value={query} onChange={e=>setQuery(e.target.value)} /></div>
      <div className="table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Institution</th><th>Status</th><th>Actions</th></tr></thead><tbody>
      {filtered.map(u=><tr key={u.id}><td><strong>{u.full_name}</strong><br/><span className="muted">{u.email}</span></td>
        <td><select value={u.role} onChange={e=>saveUser(u.id,{role:e.target.value})}>{roles.map(r=><option key={r}>{r}</option>)}</select></td>
        <td><select value={u.institution_id ?? ''} onChange={e=>saveUser(u.id,{institution_id:e.target.value ? Number(e.target.value) : null})}><option value="">Unassigned</option>{institutions.filter(i=>i.is_active).map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select></td>
        <td><span className={u.is_active?'status-pill':'status-pill muted-pill'}>{u.is_active?'ACTIVE':'INACTIVE'}</span></td>
        <td><button className="secondary" onClick={()=>saveUser(u.id,{is_active:!u.is_active})}>{u.is_active?'Deactivate':'Activate'}</button></td>
      </tr>)}
      </tbody></table></div>
    </div> : <div className="grid-2">
      <div className="panel"><h3>Add institution</h3><form onSubmit={addInstitution} className="form-grid"><label>Name<input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label>Type<input required value={form.institution_type} onChange={e=>setForm({...form,institution_type:e.target.value})}/></label><label>State<input value={form.state} onChange={e=>setForm({...form,state:e.target.value})}/></label><label>District<input value={form.district} onChange={e=>setForm({...form,district:e.target.value})}/></label><button className="primary">Create institution</button></form></div>
      <div className="panel"><h3>Institution register</h3>{institutions.map(i=><div className="list-row" key={i.id}><div><strong>{i.name}</strong><div className="muted">{i.institution_type} • {i.district || 'District not set'}, {i.state || 'State not set'}</div></div><span className="status-pill">{i.is_active?'ACTIVE':'INACTIVE'}</span></div>)}</div>
    </div>}
  </section>;
}
