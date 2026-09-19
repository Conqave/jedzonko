import type { RouteRecordRaw } from 'vue-router';

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    requiresPromotions?: boolean;
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [{ path: '', name: 'login', component: () => import('@/pages/LoginPage.vue') }],
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'home', component: () => import('@/pages/IndexPage.vue') },
      {
        path: 'households',
        name: 'households',
        component: () => import('@/pages/HouseholdsPage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'inventory',
        name: 'inventory',
        component: () => import('@/pages/InventoryPage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'recipes',
        name: 'recipes',
        component: () => import('@/pages/RecipesPage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'recipes/new',
        name: 'recipe-new',
        component: () => import('@/pages/RecipeFormPage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'recipes/:id/edit',
        name: 'recipe-edit',
        component: () => import('@/pages/RecipeFormPage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'recipes/:id',
        name: 'recipe-detail',
        component: () => import('@/pages/RecipeDetailPage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'shopping',
        name: 'shopping',
        component: () => import('@/pages/ShoppingPage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'promotions',
        name: 'promotions',
        component: () => import('@/pages/PromotionsPage.vue'),
        meta: { requiresPromotions: true },
      },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [
      { path: '', name: 'not-found', component: () => import('@/pages/ErrorNotFound.vue') },
    ],
  },
];

export default routes;
