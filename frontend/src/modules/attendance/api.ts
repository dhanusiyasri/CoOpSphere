import axios from 'axios';
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export const attendanceApi = axios.create({ baseURL: API });
attendanceApi.interceptors.request.use((config) => { const token=localStorage.getItem('ncct_token'); if(token) config.headers.Authorization=`Bearer ${token}`; return config; });
export type AttendanceSession={id:number;batch_id:number;session_date:string;start_time:string;end_time:string;topic:string;notes?:string;status:string;access_code:string;created_by_id:number;created_at:string};
export type AttendanceRecord={id:number;session_id:number;trainee_id:number;status:string;method:string;check_in_at?:string;marked_by_id?:number;remarks?:string;trainee_name:string;trainee_email:string};
export async function getSessions(){return (await attendanceApi.get<AttendanceSession[]>('/attendance/sessions')).data}
export async function createSession(p:Omit<AttendanceSession,'id'|'access_code'|'created_by_id'|'created_at'>){return (await attendanceApi.post<AttendanceSession>('/attendance/sessions',p)).data}
export async function getRoster(id:number){return (await attendanceApi.get<AttendanceRecord[]>(`/attendance/sessions/${id}/roster`)).data}
export async function markAttendance(id:number,p:{trainee_id:number;status:string;remarks?:string}){return (await attendanceApi.post<AttendanceRecord>(`/attendance/sessions/${id}/mark`,p)).data}
export async function checkIn(code:string){return (await attendanceApi.post<AttendanceRecord>('/attendance/check-in',{access_code:code})).data}
export async function getQr(id:number){return (await attendanceApi.get<{session_id:number;access_code:string;data_url:string}>(`/attendance/sessions/${id}/qr`)).data}

export type AttendanceReportSummary={total_sessions:number;enrolled_trainees:number;attendance_slots:number;present:number;late:number;absent:number;excused:number;attendance_rate:number;qr_checkins:number;manual_marks:number;exceptions:number};
export type AttendanceReportBatch={batch_id:number;batch_code:string;total_sessions:number;enrolled_trainees:number;attendance_slots:number;present:number;late:number;absent:number;excused:number;attendance_rate:number};
export type AttendanceReportSession={session_id:number;batch_id:number;batch_code:string;session_date:string;start_time:string;end_time:string;topic:string;status:string;roster_count:number;present:number;late:number;absent:number;excused:number;attendance_rate:number};
export type AttendanceReportTrainee={trainee_id:number;trainee_name:string;trainee_email:string;total_sessions:number;present:number;late:number;absent:number;excused:number;attendance_rate:number;last_check_in_at?:string|null};
export type AttendanceReport={from_date?:string|null;to_date?:string|null;batch_id?:number|null;summary:AttendanceReportSummary;batches:AttendanceReportBatch[];sessions:AttendanceReportSession[];trainees:AttendanceReportTrainee[]};
export async function getAttendanceReport(params:{from_date?:string;to_date?:string;batch_id?:number},mine=false){
 const query=new URLSearchParams();
 if(params.from_date) query.set('from_date',params.from_date);
 if(params.to_date) query.set('to_date',params.to_date);
 if(params.batch_id) query.set('batch_id',String(params.batch_id));
 const path=mine?'/attendance/reports/my':'/attendance/reports';
 return (await attendanceApi.get<AttendanceReport>(`${path}${query.toString()?`?${query.toString()}`:''}`)).data;
}

export type LowAttendanceAlert={trainee_id:number;trainee_name:string;trainee_email:string;batch_id:number;batch_code:string;total_sessions:number;present:number;late:number;absent:number;excused:number;attendance_rate:number;threshold:number};
export type LowAttendanceAlertResponse={threshold:number;alerts:LowAttendanceAlert[]};
export async function getLowAttendanceAlerts(params:{threshold?:number;from_date?:string;to_date?:string;batch_id?:number}){
 const query=new URLSearchParams();
 if(params.threshold!==undefined) query.set('threshold',String(params.threshold));
 if(params.from_date) query.set('from_date',params.from_date);
 if(params.to_date) query.set('to_date',params.to_date);
 if(params.batch_id) query.set('batch_id',String(params.batch_id));
 return (await attendanceApi.get<LowAttendanceAlertResponse>(`/attendance/alerts/low-attendance${query.toString()?`?${query.toString()}`:''}`)).data;
}
