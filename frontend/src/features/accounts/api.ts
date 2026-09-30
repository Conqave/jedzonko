import { z } from 'zod';
import { http } from '@/shared/http';
import type { CurrentUser } from './model';

const NO_SESSION_STATUSES = [401, 403];

const currentUserSchema = z
  .object({
    id: z.number().int(),
    username: z.string(),
    can_view_promotions: z.boolean(),
  })
  .transform((user): CurrentUser => ({
    id: user.id,
    username: user.username,
    canViewPromotions: user.can_view_promotions,
  }));

export async function requestCsrfToken(): Promise<void> {
  await http.get('/accounts/csrf/');
}

export async function logIn(username: string, password: string): Promise<CurrentUser> {
  const response = await http.post('/accounts/login/', { username, password });
  return currentUserSchema.parse(response.data);
}

export async function logOut(): Promise<void> {
  await http.post('/accounts/logout/');
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const payload = { current_password: currentPassword, new_password: newPassword };
  await http.post('/accounts/change-password/', payload);
}

export async function findCurrentUser(): Promise<CurrentUser | null> {
  const response = await http.get('/accounts/me/', {
    validateStatus: (status) => status === 200 || NO_SESSION_STATUSES.includes(status),
  });
  if (NO_SESSION_STATUSES.includes(response.status)) {
    return null;
  }
  return currentUserSchema.parse(response.data);
}
