import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ncct_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export type Institution = { id: number; name: string; institution_type: string; state?: string; district?: string; is_active: boolean; };

export type Programme = {
  id: number; institution_id: number; code: string; title: string; description?: string;
  category: string; mode: string; duration_days: number; capacity: number; status: string; created_at: string;
};
export type Batch = {
  id: number; programme_id: number; batch_code: string; start_date: string; end_date: string;
  trainer_id?: number; venue?: string; capacity: number; status: string; created_at: string;
};
export type Nomination = {
  id: number; batch_id: number; trainee_id: number; nominated_by_id: number;
  status: string; remarks?: string; created_at: string;
};
export type ParticipantProfile = {
  id: number; user_id: number; participant_code: string; phone?: string; participant_type: string;
  designation?: string; organization_name?: string; education_level?: string; district?: string; state?: string;
  digital_literacy_level: string; years_experience: number; profile_status: string; user_full_name: string; user_email: string;
  created_at: string; updated_at: string;
};

export type Course = { id:number; programme_id:number; course_code:string; title:string; description?:string; category:string; delivery_mode:string; duration_hours:number; level:string; status:string; created_at:string; };
export type CourseModule = { id:number; course_id:number; module_number:number; title:string; learning_objectives?:string; duration_minutes:number; created_at:string; };
export type CourseLesson = { id:number; module_id:number; lesson_number:number; title:string; content_type:string; content_url?:string; duration_minutes:number; is_mandatory:boolean; created_at:string; };

export type Enrollment = {
  id: number; batch_id: number; trainee_id: number; nomination_id?: number;
  status: string; enrolled_at: string;
};

export async function getInstitutions() { return (await api.get<Institution[]>('/institutions')).data; }
export async function getProgrammes() { return (await api.get<Programme[]>('/training/programmes')).data; }
export async function getBatches() { return (await api.get<Batch[]>('/training/batches')).data; }
export async function getNominations() { return (await api.get<Nomination[]>('/training/nominations')).data; }
export async function getEnrollments() { return (await api.get<Enrollment[]>('/training/enrollments')).data; }
export async function getParticipants() { return (await api.get<ParticipantProfile[]>('/training/participants')).data; }
export async function getCourses() { return (await api.get<Course[]>('/training/courses')).data; }
export async function getCourseModules() { return (await api.get<CourseModule[]>('/training/course-modules')).data; }
export async function getCourseLessons() { return (await api.get<CourseLesson[]>('/training/course-lessons')).data; }

export async function createProgramme(payload: Omit<Programme, 'id' | 'created_at'>) {
  return (await api.post<Programme>('/training/programmes', payload)).data;
}
export async function createBatch(payload: Omit<Batch, 'id' | 'created_at'>) {
  return (await api.post<Batch>('/training/batches', payload)).data;
}
export async function createNomination(payload: { batch_id: number; trainee_id: number; remarks?: string }) {
  return (await api.post<Nomination>('/training/nominations', payload)).data;
}
export async function approveNomination(id: number) {
  return (await api.post<Enrollment>(`/training/nominations/${id}/approve`)).data;
}
export async function rejectNomination(id: number, remarks?: string) {
  return (await api.post<Nomination>(`/training/nominations/${id}/reject`, { remarks })).data;
}

export async function createParticipant(payload: Omit<ParticipantProfile, 'id' | 'user_full_name' | 'user_email' | 'created_at' | 'updated_at'>) {
  return (await api.post<ParticipantProfile>('/training/participants', payload)).data;
}
export async function updateParticipant(userId: number, payload: Omit<ParticipantProfile, 'id' | 'user_full_name' | 'user_email' | 'created_at' | 'updated_at'>) {
  return (await api.put<ParticipantProfile>(`/training/participants/${userId}`, payload)).data;
}

export async function createCourse(payload: Omit<Course, 'id'|'created_at'>) { return (await api.post<Course>('/training/courses', payload)).data; }
export async function createCourseModule(payload: Omit<CourseModule, 'id'|'created_at'>) { return (await api.post<CourseModule>('/training/course-modules', payload)).data; }
export async function createCourseLesson(payload: Omit<CourseLesson, 'id'|'created_at'>) { return (await api.post<CourseLesson>('/training/course-lessons', payload)).data; }

export type TrainingSchedule = {
  id:number; batch_id:number; course_id?:number|null; module_id?:number|null; trainer_id?:number|null;
  session_date:string; start_time:string; end_time:string; topic:string; venue?:string|null; mode:string; status:string;
  notes?:string|null; attendance_session_id?:number|null; created_by_id:number; created_at:string;
  batch_code:string; programme_title:string; course_title?:string|null; module_title?:string|null; trainer_name?:string|null;
};

export async function getTrainingSchedules(params?:{batch_id?:number;from_date?:string;to_date?:string}) {
  const q=new URLSearchParams();
  if(params?.batch_id) q.set('batch_id',String(params.batch_id));
  if(params?.from_date) q.set('from_date',params.from_date);
  if(params?.to_date) q.set('to_date',params.to_date);
  return (await api.get<TrainingSchedule[]>(`/training/schedules${q.toString()?`?${q.toString()}`:''}`)).data;
}
export async function createTrainingSchedule(payload:Omit<TrainingSchedule,'id'|'attendance_session_id'|'created_by_id'|'created_at'|'batch_code'|'programme_title'|'course_title'|'module_title'|'trainer_name'>){
  return (await api.post<TrainingSchedule>('/training/schedules',payload)).data;
}
export async function createAttendanceForSchedule(id:number){
  return (await api.post<{schedule_id:number;attendance_session_id:number;access_code:string}>(`/training/schedules/${id}/attendance`)).data;
}


export type LogisticsPlan = {
  id:number; batch_id:number; batch_code:string; programme_title:string;
  hostel_required:boolean; hostel_name?:string|null; rooms_available:number;
  meals_included:boolean; meal_notes?:string|null; transport_required:boolean;
  pickup_point?:string|null; transport_notes?:string|null;
  coordinator_name?:string|null; coordinator_phone?:string|null; notes?:string|null;
  allocated_count:number; created_by_id:number; created_at:string;
};
export type EligibleTrainee = {
  trainee_id:number; full_name:string; email:string; enrollment_id:number; enrollment_status:string;
};

export async function getEligibleTrainees(batchId:number){
  return (await api.get<EligibleTrainee[]>(`/training/logistics/eligible-trainees?batch_id=${batchId}`)).data;
}

export type AccommodationAllocation = {
  id:number; batch_id:number; trainee_id:number; trainee_name:string; trainee_email:string;
  room_number:string; bed_number?:string|null; status:string; notes?:string|null;
  allocated_by_id:number; allocated_at:string;
};
export async function getLogisticsPlans(){ return (await api.get<LogisticsPlan[]>('/training/logistics/plans')).data; }
export async function saveLogisticsPlan(payload:Omit<LogisticsPlan,'id'|'batch_code'|'programme_title'|'allocated_count'|'created_by_id'|'created_at'>){ return (await api.post<LogisticsPlan>('/training/logistics/plans',payload)).data; }
export async function getAccommodationAllocations(batchId?:number){ return (await api.get<AccommodationAllocation[]>(`/training/logistics/allocations${batchId?`?batch_id=${batchId}`:''}`)).data; }
export async function saveAccommodationAllocation(payload:Omit<AccommodationAllocation,'id'|'trainee_name'|'trainee_email'|'allocated_by_id'|'allocated_at'>){ return (await api.post<AccommodationAllocation>('/training/logistics/allocations',payload)).data; }

export type TrainingFeedback = { id:number; schedule_id:number; batch_id:number; trainee_id:number; trainee_name:string; submitted_at:string; content_rating:number; trainer_rating:number; venue_rating:number; overall_rating:number; comments?:string|null; };
export type TrainingFeedbackSummary = { schedule_id:number; topic:string; session_date:string; batch_code:string; responses:number; average_content:number; average_trainer:number; average_venue:number; average_overall:number; };
export async function getTrainingFeedback(params?:{batch_id?:number;schedule_id?:number}) { const q=new URLSearchParams(); if(params?.batch_id)q.set('batch_id',String(params.batch_id)); if(params?.schedule_id)q.set('schedule_id',String(params.schedule_id)); return (await api.get<TrainingFeedback[]>(`/training/evaluations${q.toString()?`?${q.toString()}`:''}`)).data; }
export async function submitTrainingFeedback(payload:{schedule_id:number;content_rating:number;trainer_rating:number;venue_rating:number;overall_rating:number;comments?:string}) { return (await api.post<TrainingFeedback>('/training/evaluations',payload)).data; }
export async function getTrainingFeedbackSummary(batchId?:number) { return (await api.get<TrainingFeedbackSummary[]>(`/training/evaluations/summary${batchId?`?batch_id=${batchId}`:''}`)).data; }
