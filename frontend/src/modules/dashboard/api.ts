import { api } from '../training/api';

export type DashboardMetric = { label: string; value: number; detail: string };
export type DashboardItem = { label: string; value: string; detail?: string };
export type DashboardAttendance = { attendance_rate: number; total_sessions: number; present: number; late: number; absent: number; low_attendance_count: number; threshold: number };
export type DashboardSummary = { role: string; heading: string; subtitle: string; metrics: DashboardMetric[]; items: DashboardItem[]; attendance?: DashboardAttendance | null };

export async function getDashboardSummary() {
  return (await api.get<DashboardSummary>('/dashboard/summary')).data;
}
