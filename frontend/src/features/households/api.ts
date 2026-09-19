import { api } from '@/boot/api';
import type { Household, HouseholdMember } from './models';

export async function fetchHouseholds(): Promise<Household[]> {
  const response = await api.get<Household[]>('/households/');
  return response.data;
}

export async function createHousehold(name: string): Promise<Household> {
  const response = await api.post<Household>('/households/', { name });
  return response.data;
}

export async function renameHousehold(householdId: number, name: string): Promise<Household> {
  const response = await api.patch<Household>(`/households/${householdId}/`, { name });
  return response.data;
}

export async function fetchMembers(householdId: number): Promise<HouseholdMember[]> {
  const response = await api.get<HouseholdMember[]>(`/households/${householdId}/members/`);
  return response.data;
}

export async function addMember(householdId: number, username: string): Promise<HouseholdMember> {
  const response = await api.post<HouseholdMember>(`/households/${householdId}/members/`, {
    username,
  });
  return response.data;
}

export async function removeMember(householdId: number, userId: number): Promise<void> {
  await api.delete(`/households/${householdId}/members/${userId}/`);
}
