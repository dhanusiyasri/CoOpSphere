import { useEffect, useState } from 'react';
import { API, Credential, CredentialReadiness, CredentialRegistryItem, downloadCredentialCertificate, getCredentialReadiness, getCredentialRegistry, getMyCredentials, issueCredentialFromReadiness, revokeCredential } from './api';

type User = { id: number; full_name: string; email: string; role: string };

export function SkillsCredentials({ user }: { user: User }) {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [registry, setRegistry] = useState<CredentialRegistryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [downloading, setDownloading] = useState<number | null>(null);
  const [revoking, setRevoking] = useState<number | null>(null);
  const [readiness, setReadiness] = useState<CredentialReadiness[]>([]);
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [readinessThreshold, setReadinessThreshold] = useState(75);
  const [activeManagerTab, setActiveManagerTab] = useState<'registry' | 'readiness'>('registry');
  const [issuing, setIssuing] = useState<string | null>(null);

  async function loadTrainee() {
    setLoading(true); setError('');
    try { setCredentials(await getMyCredentials()); }
    catch (err: any) { setError(err.response?.data?.detail || 'Could not load credentials.'); }
    finally { setLoading(false); }
  }

  async function loadRegistry() {
    setLoading(true); setError('');
    try { setRegistry(await getCredentialRegistry()); }
    catch (err: any) { setError(err.response?.data?.detail || 'Could not load the credential registry.'); }
    finally { setLoading(false); }
  }

  async function loadReadiness() {
    setReadinessLoading(true); setError('');
    try { setReadiness(await getCredentialReadiness(readinessThreshold)); }
    catch (err: any) { setError(err.response?.data?.detail || 'Could not load credential readiness.'); }
    finally { setReadinessLoading(false); }
  }

  useEffect(() => { user.role === 'TRAINEE' ? loadTrainee() : loadRegistry(); }, [user.role]);

  async function download(credential: Credential) {
    setDownloading(credential.id); setError('');
    try { await downloadCredentialCertificate(credential.id); }
    catch (err: any) { setError(err.response?.data?.detail || 'Could not download certificate.'); }
    finally { setDownloading(null); }
  }

  async function issueReady(item: CredentialReadiness) {
    const key = `${item.trainee_id}-${item.course_id}`;
    const confirmed = window.confirm(`Issue the NCCT credential for ${item.trainee_name} — ${item.course_title}?\n\nAttendance is ${item.attendance_percent == null ? 'not available' : `${item.attendance_percent}%`} and remains advisory; it will not block issuance.`);
    if (!confirmed) return;
    setIssuing(key); setError(''); setMessage('');
    try {
      const credential = await issueCredentialFromReadiness(item.trainee_id, item.course_id);
      setMessage(`Credential ${credential.credential_number} issued for ${item.trainee_name}.`);
      await Promise.all([loadRegistry(), loadReadiness()]);
      setActiveManagerTab('registry');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Could not issue credential.');
    } finally { setIssuing(null); }
  }

  async function revoke(item: CredentialRegistryItem) {
    const reason = window.prompt(`Reason for revoking ${item.credential_number}:`, 'Credential issued in error');
    if (reason === null) return;
    if (reason.trim().length < 5) { setError('Revocation reason must be at least 5 characters.'); return; }
    setRevoking(item.id); setError(''); setMessage('');
    try {
      await revokeCredential(item.id, reason.trim());
      setMessage(`Credential ${item.credential_number} was revoked. Public verification will no longer validate it.`);
      await loadRegistry();
    } catch (err: any) { setError(err.response?.data?.detail || 'Could not revoke credential.'); }
    finally { setRevoking(null); }
  }

  if (user.role === 'TRAINEE') {
    return <section className="credentials-shell">
      <div className="panel credentials-hero">
        <div><p className="eyebrow">SKILLS & CREDENTIALS • CERT-01</p><h2>My Credentials</h2><p className="muted">Verified NCCT course completion records issued after training and assessment requirements are met.</p></div>
        <div className="credential-count"><strong>{credentials.length}</strong><span>issued</span></div>
      </div>
      {error && <div className="error">{error}</div>}
      {loading && <div className="panel empty">Loading credentials…</div>}
      {!loading && !credentials.length && <div className="panel empty-state"><h3>No credentials issued yet</h3><p className="muted">Complete all lessons and pass every published assessment in an enrolled course. Eligible courses will let you claim the completion credential from the LMS.</p></div>}
      {!loading && credentials.length > 0 && <div className="credential-grid">
        {credentials.map(credential => <article className="panel credential-card" key={credential.id}>
          <div className="credential-badge">NCCT</div>
          <div className="credential-main"><p className="eyebrow">{credential.status}</p><h3>{credential.title}</h3><h4>{credential.course_title}</h4><p className="muted">Credential number: <strong>{credential.credential_number}</strong></p>{credential.status === 'ISSUED' && <button className="credential-btn" onClick={() => download(credential)} disabled={downloading === credential.id}>{downloading === credential.id ? 'Preparing certificate…' : 'Download certificate PDF'}</button>}<div className="credential-wallet-actions">
                {credential.status === 'ISSUED' && <img className="credential-qr" src={`${API}/credentials/verify/${encodeURIComponent(credential.credential_number)}/qr`} alt="Credential verification QR code" />}
                <div className="credential-wallet-links">
                  <p className="muted credential-verify-link">Verification: <a href={`/verify/${encodeURIComponent(credential.credential_number)}`} target="_blank" rel="noreferrer">Open public verification</a></p>
                  {credential.status === 'ISSUED' && <button className="small-btn" onClick={() => navigator.clipboard?.writeText(`${window.location.origin}/verify/${encodeURIComponent(credential.credential_number)}`)}>Copy verification link</button>}
                </div>
              </div></div>
          <div className="credential-meta"><div><span>Completion</span><strong>{credential.completed_lessons}/{credential.total_lessons} lessons</strong></div><div><span>Assessment score</span><strong>{credential.score_percentage}%</strong></div><div><span>Issued</span><strong>{new Date(credential.issued_at).toLocaleDateString()}</strong></div></div>
        </article>)}
      </div>}
    </section>;
  }

  const active = registry.filter(item => item.status === 'ISSUED').length;
  const revoked = registry.filter(item => item.status === 'REVOKED').length;
  const readyCount = readiness.filter(item => item.eligible && !item.credential_id).length;
  const attentionCount = readiness.filter(item => !item.eligible && !item.credential_id).length;
  return <section className="credentials-shell">
    <div className="panel credentials-hero">
      <div><p className="eyebrow">SKILLS & CREDENTIALS • CERT-01</p><h2>Credential Registry</h2><p className="muted">Review issued credentials within your role scope and revoke credentials that should no longer validate.</p></div>
      <div className="credential-count"><strong>{registry.length}</strong><span>records</span></div>
    </div>
    {message && <div className="notice">{message}</div>}
    {error && <div className="error">{error}</div>}
    <div className="credential-tabs"><button className={activeManagerTab === 'registry' ? 'active' : ''} onClick={() => setActiveManagerTab('registry')}>Registry</button><button className={activeManagerTab === 'readiness' ? 'active' : ''} onClick={() => { setActiveManagerTab('readiness'); if (!readiness.length) loadReadiness(); }}>Credential readiness</button></div>
    {activeManagerTab === 'registry' ? <>
      <div className="credential-stats"><div className="panel"><strong>{registry.length}</strong><span>Total credentials</span></div><div className="panel"><strong>{active}</strong><span>Active</span></div><div className="panel"><strong>{revoked}</strong><span>Revoked</span></div></div>
      {loading && <div className="panel empty">Loading credential registry…</div>}
      {!loading && !registry.length && <div className="panel empty-state"><h3>No credentials in scope</h3><p className="muted">Credentials will appear here after trainees complete eligible courses and claim their credentials.</p></div>}
      {!loading && registry.length > 0 && <div className="panel credential-registry"><div className="panel-title"><h3>Credential records</h3><span>{registry.length}</span></div><div className="table-wrap"><table><thead><tr><th>Trainee</th><th>Course</th><th>Credential</th><th>Status</th><th>Score</th><th>Issued</th><th>Action</th></tr></thead><tbody>{registry.map(item => <tr key={item.id}><td><strong>{item.trainee_name}</strong><small>{item.trainee_email}</small></td><td>{item.course_title}</td><td>{item.credential_number}</td><td><span className={`credential-status ${item.status.toLowerCase()}`}>{item.status}</span>{item.revocation_reason && <small>{item.revocation_reason}</small>}</td><td>{item.score_percentage}%</td><td>{new Date(item.issued_at).toLocaleDateString()}</td><td>{item.status === 'ISSUED' ? <button className="small-btn danger-btn" onClick={() => revoke(item)} disabled={revoking === item.id}>{revoking === item.id ? 'Revoking…' : 'Revoke'}</button> : <span className="muted">Revoked</span>}</td></tr>)}</tbody></table></div></div>}
    </> : <>
      <div className="panel readiness-controls"><div><h3>Credential readiness queue</h3><p className="muted">Review lesson completion and assessment readiness before trainees claim their credentials. Attendance is shown as an advisory signal.</p></div><label>Attendance threshold <input type="number" min="0" max="100" value={readinessThreshold} onChange={e => setReadinessThreshold(Number(e.target.value))} /></label><button className="small-btn" onClick={loadReadiness}>Refresh</button></div>
      <div className="credential-stats"><div className="panel"><strong>{readiness.length}</strong><span>Trainee-course records</span></div><div className="panel"><strong>{readyCount}</strong><span>Ready to claim</span></div><div className="panel"><strong>{attentionCount}</strong><span>Needs action</span></div></div>
      {readinessLoading && <div className="panel empty">Loading credential readiness…</div>}
      {!readinessLoading && !readiness.length && <div className="panel empty-state"><h3>No readiness records</h3><p className="muted">Active or completed trainee-course enrolments will appear here.</p></div>}
      {!readinessLoading && readiness.length > 0 && <div className="panel credential-registry"><div className="panel-title"><h3>Readiness queue</h3><span>{readiness.length}</span></div><div className="table-wrap"><table><thead><tr><th>Trainee</th><th>Course / Batch</th><th>Lessons</th><th>Assessment</th><th>Attendance</th><th>Readiness</th><th>Warning / action</th></tr></thead><tbody>{readiness.map(item => <tr key={`${item.trainee_id}-${item.course_id}`}><td><strong>{item.trainee_name}</strong><small>{item.trainee_email}</small></td><td><strong>{item.course_code}</strong><small>{item.course_title} · {item.batch_code}</small></td><td>{item.completed_lessons}/{item.total_lessons}<small>{item.lesson_completion_percent}% complete</small></td><td>{item.assessment_passed ? <span className="credential-status issued">Passed</span> : <span className="credential-status revoked">Pending</span>}<small>{item.assessment_score}%</small></td><td>{item.attendance_percent == null ? 'No sessions' : `${item.attendance_percent}%`}<small>Advisory ≥ {item.attendance_threshold}%</small></td><td><span className={`credential-status ${item.eligible ? 'issued' : 'revoked'}`}>{item.eligible ? 'READY' : 'NOT READY'}</span></td><td>{item.credential_id ? <><div>Credential already issued: <strong>{item.credential_number}</strong></div><span className="muted">Status: {item.credential_status}</span></> : item.eligible ? <><div>{item.attendance_percent != null && item.attendance_percent < item.attendance_threshold ? `Attendance warning: ${item.attendance_percent}% is below the ${item.attendance_threshold}% advisory threshold.` : 'All credential requirements met.'}</div><button className="small-btn" onClick={() => issueReady(item)} disabled={issuing === `${item.trainee_id}-${item.course_id}`}>{issuing === `${item.trainee_id}-${item.course_id}` ? 'Issuing…' : 'Issue credential'}</button></> : <span>{item.reason || 'Complete the outstanding requirements.'}</span>}</td></tr>)}</tbody></table></div></div>}
    </>}
  </section>;
}
