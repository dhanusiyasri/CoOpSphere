import { api } from '../training/api';

export type IntelligenceOverview = {
  trainees:number; programmes:number; batches:number; active_enrollments:number; courses:number; lessons:number;
  completed_lesson_records:number; lesson_activity_rate:number; assessment_attempts:number; assessment_passes:number;
  assessment_pass_rate:number; credentials_issued:number; published_jobs:number; job_applications:number;
  selected_applications:number; placement_conversion_rate:number; application_statuses:Record<string,number>;
  programme_summary:Array<{id:number;code:string;title:string;status:string;batch_count:number}>;
};
export type InstitutionSummary={id:number;name:string;institution_type:string;state?:string;district?:string;programme_count:number;batch_count:number;trainee_count:number;active_enrollment_count:number};
export type TrainerSummary={id:number;full_name:string;email:string;institution_id?:number;batch_count:number;active_batch_count:number;trainee_count:number};
export type ProgrammeDetail={id:number;code:string;title:string;description?:string;category:string;mode:string;duration_days:number;capacity:number;status:string;institution_name:string;batch_count:number;course_count:number;trainee_count:number;active_enrollment_count:number;completed_lesson_records:number;credential_count:number;batches:Array<{id:number;batch_code:string;start_date:string;end_date:string;venue?:string;status:string;capacity:number;enrollment_count:number;trainer_id?:number}>};
export async function getIntelligenceOverview(){return (await api.get<IntelligenceOverview>('/intelligence/overview')).data;}
export async function getInstitutions(){return (await api.get<InstitutionSummary[]>('/intelligence/institutions')).data;}
export async function getTrainers(){return (await api.get<TrainerSummary[]>('/intelligence/trainers')).data;}
export async function getProgrammeDetail(id:number){return (await api.get<ProgrammeDetail>(`/intelligence/programmes/${id}`)).data;}
export type AssistantResponse={answer:string;intent:string;sources:string[];suggestions:string[]};
export async function askIntelligenceAssistant(message:string){return (await api.post<AssistantResponse>('/intelligence/assistant',{message})).data;}
