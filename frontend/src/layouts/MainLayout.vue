<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="drawerOpen = !drawerOpen" />
        <q-toolbar-title>jedzonko</q-toolbar-title>
        <q-btn flat dense no-caps :label="accounts.user?.username ?? ''" icon="account_circle">
          <q-menu>
            <q-list style="min-width: 160px">
              <q-item clickable v-close-popup @click="signOut">
                <q-item-section avatar><q-icon name="logout" /></q-item-section>
                <q-item-section>Wyloguj</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawerOpen" show-if-above bordered>
      <q-list>
        <q-item-label header>Nawigacja</q-item-label>
        <q-item clickable :to="{ name: 'home' }" exact>
          <q-item-section avatar><q-icon name="home" /></q-item-section>
          <q-item-section>Start</q-item-section>
        </q-item>
        <q-item v-if="accounts.canViewPromotions" clickable :to="{ name: 'promotions' }">
          <q-item-section avatar><q-icon name="local_offer" /></q-item-section>
          <q-item-section>Promocje</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAccountStore } from '@/features/accounts/store';

const drawerOpen = ref(false);
const accounts = useAccountStore();
const router = useRouter();

async function signOut(): Promise<void> {
  await accounts.signOut();
  await router.push({ name: 'login' });
}
</script>
