import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import * as accountsApi from './api';
import type { CurrentUser } from './models';

export const useAccountStore = defineStore('accounts', () => {
  const user = ref<CurrentUser | null>(null);
  const isResolved = ref(false);

  const isAuthenticated = computed(() => user.value !== null);
  const canViewPromotions = computed(() => user.value?.can_view_promotions === true);

  async function resolveSession(): Promise<void> {
    await accountsApi.fetchCsrfToken();
    user.value = await accountsApi.fetchCurrentUserIfSignedIn();
    isResolved.value = true;
  }

  async function signIn(username: string, password: string): Promise<void> {
    user.value = await accountsApi.login(username, password);
  }

  async function signOut(): Promise<void> {
    await accountsApi.logout();
    user.value = null;
  }

  return { user, isResolved, isAuthenticated, canViewPromotions, resolveSession, signIn, signOut };
});
