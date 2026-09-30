import axios from 'axios';

export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const credentialsApi = axios.create({ baseURL: API });
credentialsApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('ncct_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export type Credential = {
  id: number;
  trainee_id: number;
  course_id: number;
  credential_number: string;
  title: string;
  course_title: string;
  status: string;
  score_percentage: number;
  completed_lessons: number;
  total_lessons: number;
  issued_at: string;
};

export type CredentialEligibility = {
  course_id: number;
  eligible: boolean;
  total_lessons: number;
  completed_lessons: number;
  score_percentage: number;
  reason?: string;
};

export async function getMyCredentials() {
  return (await credentialsApi.get<Credential[]>('/credentials/my-credentials')).data;
}

export async function getCredentialEligibility(courseId: number) {
  return (await credentialsApi.get<CredentialEligibility>(`/credentials/courses/${courseId}/eligibility`)).data;
}

export async function issueCredential(courseId: number) {
  return (await credentialsApi.post<Credential>(`/credentials/courses/${courseId}/issue`)).data;
}


export type CredentialVerification = {
  valid: boolean;
  credential_number: string;
  title: string;
  course_title: string;
  trainee_name: string;
  score_percentage: number;
  completed_lessons: number;
  total_lessons: number;
  issued_at: string;
  status: string;
  revoked_at?: string | null;
  revocation_reason?: string | null;
};

export async function verifyCredential(credentialNumber: string) {
  return (await credentialsApi.get<CredentialVerification>(`/credentials/verify/${encodeURIComponent(credentialNumber)}`)).data;
}

export async function downloadCredentialCertificate(credentialId: number) {
  const response = await credentialsApi.get(`/credentials/${credentialId}/certificate.pdf`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'NCCT-certificate.pdf';
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}


export type CredentialRegistryItem = Credential & {
  trainee_name: string;
  trainee_email: string;
  institution_id?: number | null;
  institution_name?: string | null;
  revoked_at?: string | null;
  revoked_by_id?: number | null;
  issued_by_id?: number | null;
  revocation_reason?: string | null;
};

export async function getCredentialRegistry() {
  return (await credentialsApi.get<CredentialRegistryItem[]>('/credentials/registry')).data;
}

export async function revokeCredential(credentialId: number, reason: string) {
  return (await credentialsApi.post<CredentialRegistryItem>(`/credentials/${credentialId}/revoke`, { reason })).data;
}


export type CredentialReadiness = {
  trainee_id: number;
  trainee_name: string;
  trainee_email: string;
  course_id: number;
  course_code: string;
  course_title: string;
  batch_id: number;
  batch_code: string;
  lesson_completion_percent: number;
  completed_lessons: number;
  total_lessons: number;
  assessment_passed: boolean;
  assessment_score: number;
  attendance_percent?: number | null;
  attendance_threshold: number;
  eligible: boolean;
  reason?: string | null;
  credential_id?: number | null;
  credential_number?: string | null;
  credential_status?: string | null;
};

export async function getCredentialReadiness(attendanceThreshold = 75, courseId?: number) {
  const params: Record<string, number> = { attendance_threshold: attendanceThreshold };
  if (courseId) params.course_id = courseId;
  return (await credentialsApi.get<CredentialReadiness[]>('/credentials/readiness', { params })).data;
}


export async function issueCredentialFromReadiness(traineeId: number, courseId: number) {
  return (await credentialsApi.post<Credential>(`/credentials/readiness/${traineeId}/${courseId}/issue`)).data;
}
