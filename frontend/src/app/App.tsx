import { LanguageProvider } from './i18n/LanguageContext';
import { FormEvent, useEffect, useState } from 'react';
import axios from 'axios';
import { api } from '../modules/training/api';
import { TrainingERP } from '../modules/training/TrainingERP';
import { LMS } from '../modules/lms/LMS';
import { SkillsCredentials } from '../modules/credentials/SkillsCredentials';
import { VerifyCredential } from '../modules/credentials/VerifyCredential';
import { Careers } from '../modules/careers/Careers';
import { Intelligence } from '../modules/intelligence/Intelligence';
import { Dashboard } from '../modules/dashboard/Dashboard';
import { Administration } from '../modules/administration/Administration';
import { Attendance } from '../modules/attendance/Attendance';
import { TrainingLogistics } from '../modules/training/TrainingLogistics';
import { TrainingEvaluation } from '../modules/training/TrainingEvaluation';
import { DigitalLiteracy } from '../modules/skills/DigitalLiteracy';
import { SkillPassport } from '../modules/skills/SkillPassport';
import { SkillRecommendations } from '../modules/skills/SkillRecommendations';
import { Notifications } from '../modules/notifications/Notifications';

const ROOT = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/api\/v1$/, '');

type User = { id: number; full_name: string; email: string; role: string; institution_id?: number };

function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [email, setEmail] = useState('admin@ncct.local');
  const [password, setPassword] = useState('Admin@123');
  const [error, setError] = useState('');
  async function submit(e: FormEvent) {
    e.preventDefault(); setError('');
    try {
      const token = (await axios.post(`${ROOT}/api/v1/auth/login`, { email, password })).data.access_token;
      localStorage.setItem('ncct_token', token);
      const user = (await axios.get(`${ROOT}/api/v1/auth/me`, { headers: { Authorization: `Bearer ${token}` } })).data;
      onLogin(user);
    } catch (err: any) { setError(err.response?.data?.detail || 'Login failed'); }
  }
  return <LanguageProvider><div className="login-shell"><form className="login-card" onSubmit={submit}><div className="brand dark">NCCT<span>•</span></div><p className="subtitle dark-sub">Cooperative Ecosystem</p><p className="eyebrow">LOCAL DEMO LOGIN</p><h1>Sign in to the platform</h1><p className="muted">Use a seeded demo account to access the Training ERP.</p><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required /></label>{error && <div className="error">{error}</div>}<button className="primary full">Sign in</button><div className="demo-hint">Admin: admin@ncct.local / Admin@123<br/>Trainer: trainer@ncct.local / Trainer@123<br/>Trainee: trainee@ncct.local / Trainee@123<br/>Employer: employer@ncct.local / Employer@123</div></form></div></LanguageProvider>;
}

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [section, setSection] = useState('Dashboard');
  const [status, setStatus] = useState('Checking backend...');
  const [apiVersion, setApiVersion] = useState('');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    axios.get(`${ROOT}/health`).then(() => { setStatus('Backend connected'); return axios.get(`${ROOT}`); }).then(res => setApiVersion(res.data.version)).catch(() => setStatus('Backend not running'));
    const token = localStorage.getItem('ncct_token');
    if (token) api.get('/auth/me').then(r => setUser(r.data)).catch(() => localStorage.removeItem('ncct_token'));
  }, []);

  const verifyMatch = window.location.pathname.match(/^\/verify\/(.+)$/);
  if (verifyMatch) return <VerifyCredential credentialNumber={decodeURIComponent(verifyMatch[1])} />;

  if (!user) return <Login onLogin={setUser} />;

  const nav = ['Dashboard', 'Notifications', 'Training ERP', 'Training Logistics', 'Training Evaluation', 'Attendance', 'LMS', 'Skills & Credentials', 'Digital Literacy', 'Skill Passport', 'Skill Recommendations', 'Careers', 'Intelligence', 'Administration'];
  const navIcons: Record<string, string> = {
    'Dashboard': '⌂', 'Notifications': '•', 'Training ERP': '▦', 'Training Logistics': '◫', 'Training Evaluation': '✓',
    'Attendance': '◷', 'LMS': '▤', 'Skills & Credentials': '◇', 'Digital Literacy': '⌁',
    'Skill Passport': '▱', 'Skill Recommendations': '⌘', 'Careers': '↗', 'Intelligence': '◌', 'Administration': '⚙',
  };
  const navigate = (item: string) => { setSection(item); setMobileNavOpen(false); };
  return <div className="shell">
    <div className={`sidebar-backdrop ${mobileNavOpen ? 'show' : ''}`} onClick={() => setMobileNavOpen(false)} />
    <aside className={`sidebar ${mobileNavOpen ? 'open' : ''}`}>
      <div className="sidebar-top">
        <div className="brand">NCCT<span>•</span></div>
        <div className="subtitle">Cooperative Ecosystem</div>
      </div>
      <div className="nav-label">WORKSPACE</div>
      <nav>{nav.map(item => <button className={section === item ? 'nav active' : 'nav'} key={item} onClick={() => navigate(item)}><span className="nav-icon" aria-hidden="true">{navIcons[item]}</span><span>{item}</span>{section === item && <span className="nav-active-dot" />}</button>)}</nav>
      <div className="sidebar-user">
        <div className="user-avatar">{user.full_name.split(' ').map(x => x[0]).slice(0,2).join('')}</div>
        <div className="user-copy"><strong>{user.full_name}</strong><span>{user.role.replace(/_/g, ' ')}</span></div>
        <button className="signout" aria-label="Sign out" onClick={() => { localStorage.removeItem('ncct_token'); setUser(null); }}>↪</button>
      </div>
    </aside>
    <main className="main">
      <header className="topbar">
        <div className="topbar-title"><button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileNavOpen(true)}>☰</button><div><p className="eyebrow">NATIONAL COUNCIL FOR COOPERATIVE TRAINING</p><h1>Cooperative Capacity Platform</h1><p className="muted">Local development environment <span className="api-version">• API {apiVersion || '—'}</span></p></div></div><div className={`status ${status === 'Backend connected' ? 'online' : status === 'Backend not running' ? 'offline' : ''}`}><span className="dot" />{status}</div>
      </header>
      {section === 'Dashboard' ? <Dashboard user={user} onNavigate={navigate} /> : section === 'Notifications' ? <Notifications user={user} onNavigate={navigate} /> : section === 'Training ERP' ? <TrainingERP user={user} /> : section === 'Training Logistics' ? <TrainingLogistics user={user} /> : section === 'Training Evaluation' ? <TrainingEvaluation user={user} /> : section === 'Attendance' ? <Attendance user={user} /> : section === 'LMS' ? <LMS user={user} /> : section === 'Skills & Credentials' ? <SkillsCredentials user={user} /> : section === 'Digital Literacy' ? <DigitalLiteracy user={user} /> : section === 'Skill Passport' ? <SkillPassport user={user} /> : section === 'Skill Recommendations' ? <SkillRecommendations user={user} /> : section === 'Careers' ? <Careers user={user} /> : section === 'Intelligence' ? <Intelligence user={user} /> : section === 'Administration' ? <Administration user={user} /> : <section className="panel dashboard-placeholder"><h2>{section}</h2><p className="muted">This module is reserved for the next implementation slice.</p></section>}
    </main>
  </div>;
}


if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}
