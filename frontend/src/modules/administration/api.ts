import { api } from '../training/api';

export type AdminUser = {
  id: number; full_name: string; email: string; role: string;
  institution_id?: number | null; institution_name?: string | null; is_active: boolean;
};
export type Institution = {
  id: number; name: string; institution_type: string; state?: string; district?: string; is_active: boolean;
};

export async function getAdminUsers() { return (await api.get<AdminUser[]>('/users')).data; }
export async function updateAdminUser(id: number, payload: Partial<Pick<AdminUser, 'role'|'institution_id'|'is_active'>>) {
  return (await api.patch<AdminUser>(`/users/${id}`, payload)).data;
}
export async function getInstitutions() { return (await api.get<Institution[]>('/institutions')).data; }
export async function createInstitution(payload: {name:string; institution_type:string; state?:string; district?:string}) {
  return (await api.post<Institution>('/institutions', payload)).data;
}
