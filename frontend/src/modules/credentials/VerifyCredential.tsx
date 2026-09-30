import { useEffect, useState } from 'react';
import { verifyCredential, CredentialVerification } from './api';

export function VerifyCredential({ credentialNumber }: { credentialNumber: string }) {
  const [data, setData] = useState<CredentialVerification | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    verifyCredential(credentialNumber)
      .then(setData)
      .catch((err: any) => setError(err.response?.data?.detail || 'Credential could not be verified.'))
      .finally(() => setLoading(false));
  }, [credentialNumber]);

  return <div className="verify-shell">
    <div className="panel verify-card">
      <p className="eyebrow">NATIONAL COUNCIL FOR COOPERATIVE TRAINING</p>
      <h1>Credential Verification</h1>
      {loading && <p className="muted">Checking credential…</p>}
      {!loading && error && <div className="error">{error}</div>}
      {!loading && data && <>
        <div className={data.valid ? 'verify-valid' : 'verify-revoked'}>{data.valid ? '✓ Valid NCCT credential' : '✕ Credential is revoked and is not currently valid'}</div>
        <div className="verify-grid">
          <div><span>Credential holder</span><strong>{data.trainee_name}</strong></div>
          <div><span>Course</span><strong>{data.course_title}</strong></div>
          <div><span>Credential number</span><strong>{data.credential_number}</strong></div>
          <div><span>Completion</span><strong>{data.completed_lessons}/{data.total_lessons} lessons</strong></div>
          <div><span>Assessment score</span><strong>{data.score_percentage}%</strong></div>
          <div><span>Issued</span><strong>{new Date(data.issued_at).toLocaleDateString()}</strong></div>
          {data.revoked_at && <div><span>Revoked</span><strong>{new Date(data.revoked_at).toLocaleDateString()}</strong></div>}
          {data.revocation_reason && <div><span>Revocation reason</span><strong>{data.revocation_reason}</strong></div>}
        </div>
      </>}
    </div>
  </div>;
}
