import { useEffect, useState } from 'react';
import { getDashboardSummary, DashboardSummary } from './api';

type User = { id: number; full_name: string; email: string; role: string };

export function Dashboard({ user, onNavigate }: { user: User; onNavigate?: (section: string) => void }) {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState('');

  async function load() {
    try { setError(''); setData(await getDashboardSummary()); }
    catch (e: any) { setError(e.response?.data?.detail || 'Unable to load dashboard'); }
  }

  useEffect(() => { load(); }, [user.id]);

  if (error) return <section className="panel"><h2>Dashboard</h2><div className="error">{error}</div></section>;
  if (!data) return <section className="panel"><h2>Dashboard</h2><p className="muted">Loading your dashboard…</p></section>;

  const attendance = data.attendance;
  const manager = ['NCCT_ADMIN', 'INSTITUTE_ADMIN', 'TRAINER'].includes(user.role);

  return <div className="dashboard-shell">
    <section className="panel dashboard-hero">
      <div><p className="eyebrow">NCCT CENTRAL WORKSPACE</p><h2>{data.heading}</h2><p className="muted">{data.subtitle}</p></div>
      <div className="dashboard-role"><strong>{data.role}</strong><span>{user.email}</span></div>
    </section>

    <section className="dashboard-metrics">
      {data.metrics.map(m => <div className="dashboard-metric" key={m.label}><span>{m.label}</span><strong>{m.value}{m.label === 'Lesson completion' ? '%' : ''}</strong><small>{m.detail}</small></div>)}
    </section>

    {attendance && <section className="panel dashboard-attendance-card">
      <div className="panel-title">
        <div><h3>Attendance overview</h3><p className="muted">Live attendance figures from the current training records.</p></div>
        <button className="secondary" type="button" onClick={() => onNavigate?.('Attendance')}>View attendance</button>
      </div>
      <div className="dashboard-attendance-grid">
        <div><span>Attendance rate</span><strong>{attendance.attendance_rate}%</strong><small>{attendance.total_sessions} sessions</small></div>
        <div><span>Present</span><strong>{attendance.present}</strong><small>Recorded as present</small></div>
        <div><span>Late</span><strong>{attendance.late}</strong><small>Recorded as late</small></div>
        <div><span>Absent</span><strong>{attendance.absent}</strong><small>Recorded or inferred absent</small></div>
        <div><span>{manager ? 'Low-attendance trainees' : 'Your low-attendance alert'}</span><strong>{attendance.low_attendance_count}</strong><small>Below {attendance.threshold}%</small></div>
      </div>
      {manager && attendance.low_attendance_count > 0 && <div className="notice dashboard-attendance-notice">{attendance.low_attendance_count} trainee{attendance.low_attendance_count === 1 ? '' : 's'} are below the {attendance.threshold}% attendance threshold. Open Attendance to review the detailed report.</div>}
      {!manager && attendance.low_attendance_count > 0 && <div className="notice dashboard-attendance-notice">Your current attendance rate is below the {attendance.threshold}% threshold. Open Attendance to review your sessions.</div>}
    </section>}

    <section className="dashboard-grid">
      <div className="panel">
        <div className="panel-title"><h3>Operational activity</h3><span>Current database</span></div>
        <div className="dashboard-list">{data.items.map(i => <div className="dashboard-row" key={`${i.label}-${i.value}`}><div><strong>{i.label}</strong><span>{i.detail || '—'}</span></div><b>{i.value}</b></div>)}</div>
        {!data.items.length && <div className="empty">No recent activity recorded.</div>}
      </div>
      <div className="panel dashboard-guide">
        <div className="panel-title"><h3>Platform areas</h3><span>NCCT ecosystem</span></div>
        <div className="dashboard-area"><strong>Training ERP</strong><span>Programmes, batches, nominations and enrolments</span></div>
        <div className="dashboard-area"><strong>LMS</strong><span>Courses, lessons, assessments and learning progress</span></div>
        <div className="dashboard-area"><strong>Skills & Credentials</strong><span>Completion credentials and verification</span></div>
        <div className="dashboard-area"><strong>Careers</strong><span>Employment opportunities, profiles and applications</span></div>
        <div className="dashboard-area"><strong>Intelligence</strong><span>Operational analytics and drill-downs</span></div>
      </div>
    </section>
    <p className="dashboard-footnote">Dashboard figures are descriptive operational counts from the current NCCT database; they are not forecasts or performance rankings.</p>
  </div>;
}
