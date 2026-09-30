import { api } from '../training/api';

export type Job = {
  id:number; employer_id:number; title:string; organization_name:string; description:string;
  location:string; employment_type:string; skills?:string; minimum_education?:string;
  minimum_experience_years:number; salary_range?:string; closing_date?:string; status:string; created_at:string;
};
export type Application = { id:number; job_id:number; trainee_id:number; job_title:string; organization_name:string; status:string; cover_note?:string; applied_at:string; updated_at?:string; interview_scheduled_at?:string; interview_mode?:string; interview_location_or_link?:string; interview_notes?:string; offer_status?:string; offer_offered_at?:string; offer_expires_at?:string; offer_salary?:string; offer_employment_type?:string; offer_notes?:string; offer_responded_at?:string };

export type CareerProfile = {
  id:number; trainee_id:number; headline?:string; professional_summary?:string; skills?:string;
  preferred_locations?:string; preferred_employment_types?:string; resume_text?:string;
  profile_visibility:string; updated_at:string;
};

export type RecommendedJob = {
  job_id:number; title:string; organization_name:string; location:string; employment_type:string;
  skills?:string; minimum_education?:string; minimum_experience_years:number; salary_range?:string;
  match_score:number; matched_skills:string[]; reasons:string[];
};

export type CandidateProfile = {
  trainee_id:number; full_name:string; email:string; participant_code?:string; phone?:string;
  designation?:string; organization_name?:string; education_level?:string; district?:string; state?:string;
  digital_literacy_level?:string; years_experience:number; headline?:string; professional_summary?:string;
  skills?:string; preferred_locations?:string; preferred_employment_types?:string; resume_text?:string;
};

export async function getJobs(){ return (await api.get<Job[]>('/careers/jobs')).data; }
export async function createJob(payload: Omit<Job,'id'|'employer_id'|'status'|'created_at'> & {status?:string}){ return (await api.post<Job>('/careers/jobs',payload)).data; }
export async function applyToJob(jobId:number, cover_note?:string){ return (await api.post<Application>(`/careers/jobs/${jobId}/apply`,{cover_note})).data; }
export async function getMyApplications(){ return (await api.get<Application[]>('/careers/my-applications')).data; }
export async function getEmployerApplications(){ return (await api.get<Application[]>('/careers/employer-applications')).data; }
export async function updateApplicationStatus(id:number,status:string){ return (await api.post<Application>(`/careers/applications/${id}/status`,{status})).data; }
export async function getCareerProfile(){ return (await api.get<CareerProfile>('/careers/profile')).data; }
export async function updateCareerProfile(payload: Omit<CareerProfile,'id'|'trainee_id'|'updated_at'>){ return (await api.put<CareerProfile>('/careers/profile',payload)).data; }
export async function getRecommendedJobs(){ return (await api.get<RecommendedJob[]>('/careers/recommended-jobs')).data; }
export async function getCandidateProfile(applicationId:number){ return (await api.get<CandidateProfile>(`/careers/applications/${applicationId}/candidate-profile`)).data; }

export type CandidateSearchResult = {
  trainee_id:number; full_name:string; headline?:string; email:string; phone?:string;
  education_level?:string; years_experience:number; district?:string; state?:string;
  skills?:string; digital_literacy_level?:string; credential_count:number; profile_visibility:string;
};

export async function downloadMyResume(){
  return (await api.get('/careers/profile/resume.pdf',{responseType:'blob'})).data as Blob;
}
export async function searchCandidates(params:{query?:string;skill?:string;location?:string;min_experience?:number;education?:string;limit?:number}){
  return (await api.get<CandidateSearchResult[]>('/careers/candidate-search',{params})).data;
}
export async function getSearchedCandidateProfile(traineeId:number){
  return (await api.get<CandidateProfile>(`/careers/candidate-search/${traineeId}`)).data;
}

export async function scheduleInterview(id:number,payload:{scheduled_at:string;mode:string;location_or_link:string;notes?:string}){ return (await api.post<Application>(`/careers/applications/${id}/interview`,payload)).data; }
export async function cancelInterview(id:number,reason?:string){ return (await api.post<Application>(`/careers/applications/${id}/interview/cancel`,{reason})).data; }

export async function sendOffer(id:number,payload:{expires_at?:string;salary?:string;employment_type?:string;notes?:string}){ return (await api.post<Application>(`/careers/applications/${id}/offer`,payload)).data; }
export async function respondToOffer(id:number,decision:'ACCEPT'|'DECLINE'){ return (await api.post<Application>(`/careers/applications/${id}/offer/respond`,{decision})).data; }


export type Placement = {
  id:number; application_id:number; trainee_id:number; employer_id:number; job_id:number;
  job_title:string; organization_name:string; status:string; joining_date?:string; notes?:string; updated_at:string;
};
export type PlacementSummary = { total:number; pending_joining:number; joined:number; not_joined:number };
export async function updatePlacement(id:number,payload:{status:string;joining_date?:string;notes?:string}){ return (await api.post<Placement>(`/careers/applications/${id}/placement`,payload)).data; }
export async function getPlacements(){ return (await api.get<Placement[]>('/careers/placements')).data; }
export async function getPlacementSummary(){ return (await api.get<PlacementSummary>('/careers/placement-summary')).data; }
export async function getMyPlacements(){ return (await api.get<Placement[]>('/careers/my-placement')).data; }


export type PlacementAnalytics = {
  jobs_total:number; jobs_published:number; applications_total:number;
  applications_shortlisted:number; applications_interview:number; applications_selected:number; applications_rejected:number;
  offers_pending:number; offers_accepted:number; offers_declined:number;
  placements_total:number; pending_joining:number; joined:number; not_joined:number; placement_join_rate:number;
};
export async function getPlacementAnalytics(){ return (await api.get<PlacementAnalytics>('/careers/placement-analytics')).data; }


export type EmploymentFollowUp = {
  id:number; placement_id:number; trainee_id:number; employer_id:number; checkpoint:string; status:string;
  notes?:string; employer_feedback?:string; trainee_feedback?:string; checked_at:string; updated_at:string;
};
export async function getPlacementFollowUps(placementId:number){ return (await api.get<EmploymentFollowUp[]>(`/careers/placements/${placementId}/follow-ups`)).data; }
export async function savePlacementFollowUp(placementId:number,payload:{checkpoint:string;status:string;notes?:string;employer_feedback?:string;trainee_feedback?:string}){ return (await api.post<EmploymentFollowUp>(`/careers/placements/${placementId}/follow-ups`,payload)).data; }
export async function getMyPlacementFollowUps(){ return (await api.get<EmploymentFollowUp[]>('/careers/my-placement-follow-ups')).data; }
