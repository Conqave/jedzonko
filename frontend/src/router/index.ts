import { defineRouter } from '#q-app';
import { createRouter, createWebHistory } from 'vue-router';

import routes from './routes';

export default defineRouter(() => {
  const history = createWebHistory(import.meta.env.QUASAR_VUE_ROUTER_BASE);
  return createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history,
  });
});
