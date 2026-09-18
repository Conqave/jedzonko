import { defineBoot } from '#q-app';
import { useAccountStore } from '@/features/accounts/store';

export default defineBoot(async ({ router, store }) => {
  const accounts = useAccountStore(store);
  await accounts.resolveSession();

  router.beforeEach((to) => {
    if (to.meta.requiresAuth === true && !accounts.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } };
    }
    if (to.name === 'login' && accounts.isAuthenticated) {
      return { name: 'home' };
    }
    if (to.meta.requiresPromotions === true && !accounts.canViewPromotions) {
      return { name: 'home' };
    }
    return true;
  });
});
