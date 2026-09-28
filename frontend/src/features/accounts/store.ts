import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { findCurrentUser, logIn, logOut, requestCsrfToken } from './api';
import type { CurrentUser } from './model';

export const useAccountStore = defineStore('accounts', () => {
  const user = ref<CurrentUser | null>(null);

  const isAuthenticated = computed(() => user.value !== null);
  const canViewPromotions = computed(() => user.value?.canViewPromotions === true);

  async function resolveSession(): Promise<void> {
    await requestCsrfToken();
    user.value = await findCurrentUser();
  }

  async function signIn(username: string, password: string): Promise<void> {
    user.value = await logIn(username, password);
  }

  async function signOut(): Promise<void> {
    await logOut();
    user.value = null;
  }

  return { user, isAuthenticated, canViewPromotions, resolveSession, signIn, signOut };
});
