import { z } from 'zod';
import { http } from '@/shared/http';
import type { DeletedHousehold, Household, HouseholdMember } from './model';

const householdFields = {
  id: z.number().int(),
  name: z.string(),
  member_count: z.number().int(),
};

const householdSchema = z.object(householdFields).transform((household): Household => ({
  id: household.id,
  name: household.name,
  memberCount: household.member_count,
}));

const deletedHouseholdSchema = z
  .object({
    ...householdFields,
    deleted_at: z.iso.datetime({ offset: true }),
    purge_after: z.iso.datetime({ offset: true }),
  })
  .transform((household): DeletedHousehold => ({
    id: household.id,
    name: household.name,
    memberCount: household.member_count,
    deletedAt: new Date(household.deleted_at),
    purgeAfter: new Date(household.purge_after),
  }));

const memberSchema = z
  .object({ user_id: z.number().int(), username: z.string() })
  .transform((member): HouseholdMember => ({ userId: member.user_id, username: member.username }));

export async function fetchHouseholds(): Promise<Household[]> {
  const response = await http.get('/households/');
  return householdSchema.array().parse(response.data);
}

export async function createHousehold(name: string): Promise<Household> {
  const response = await http.post('/households/', { name });
  return householdSchema.parse(response.data);
}

export async function renameHousehold(householdId: number, name: string): Promise<Household> {
  const response = await http.patch(`/households/${householdId}/`, { name });
  return householdSchema.parse(response.data);
}

export async function deleteHousehold(householdId: number): Promise<void> {
  await http.delete(`/households/${householdId}/`);
}

export async function fetchDeletedHouseholds(): Promise<DeletedHousehold[]> {
  const response = await http.get('/households/deleted/');
  return deletedHouseholdSchema.array().parse(response.data);
}

export async function restoreHousehold(householdId: number): Promise<Household> {
  const response = await http.post(`/households/${householdId}/restore/`);
  return householdSchema.parse(response.data);
}

export async function fetchMembers(householdId: number): Promise<HouseholdMember[]> {
  const response = await http.get(`/households/${householdId}/members/`);
  return memberSchema.array().parse(response.data);
}

export async function addMember(householdId: number, username: string): Promise<HouseholdMember> {
  const response = await http.post(`/households/${householdId}/members/`, { username });
  return memberSchema.parse(response.data);
}

export async function removeMember(householdId: number, userId: number): Promise<void> {
  await http.delete(`/households/${householdId}/members/${userId}/`);
}
