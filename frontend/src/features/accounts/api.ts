import { api } from '@/boot/api';
import type { CurrentUser } from './models';

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

export async function fetchCurrentUser(): Promise<CurrentUser> {
  const response = await api.get<CurrentUser>('/accounts/me/');
  return response.data;
}
