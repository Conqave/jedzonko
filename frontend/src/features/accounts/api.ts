import { api } from '@/boot/api';
import type { CurrentUser } from './models';

const NO_SESSION_STATUSES = [401, 403];

export async function fetchCsrfToken(): Promise<void> {
  await api.get('/accounts/csrf/');
}

export async function login(username: string, password: string): Promise<CurrentUser> {
  const response = await api.post<CurrentUser>('/accounts/login/', { username, password });
  return response.data;
}

export async function logout(): Promise<void> {
  await api.post('/accounts/logout/');
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await api.post('/accounts/change-password/', { current_password: currentPassword, new_password: newPassword });
}

export async function fetchCurrentUserIfSignedIn(): Promise<CurrentUser | null> {
  const response = await api.get<CurrentUser>('/accounts/me/', {
    validateStatus: (status) => status === 200 || NO_SESSION_STATUSES.includes(status),
  });
  if (NO_SESSION_STATUSES.includes(response.status)) {
    return null;
  }
  return response.data;
}
