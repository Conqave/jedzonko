<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="drawerOpen = !drawerOpen" />
        <q-toolbar-title>jedzonko</q-toolbar-title>
        <q-select
          v-if="households.hasHousehold"
          :model-value="households.selectedId"
          class="q-mr-md"
          style="min-width: 180px"
          dense
          dark
          standout
          emit-value
          map-options
          option-value="id"
          :options="householdOptions"
          label="Gospodarstwo"
          @update:model-value="households.select"
        />
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
        <q-item clickable :to="{ name: 'inventory' }">
          <q-item-section avatar><q-icon name="kitchen" /></q-item-section>
          <q-item-section>Mam w domu</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'recipes' }">
          <q-item-section avatar><q-icon name="restaurant_menu" /></q-item-section>
          <q-item-section>Przepisy</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'shopping' }">
          <q-item-section avatar><q-icon name="shopping_cart" /></q-item-section>
          <q-item-section>Listy zakupów</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'households' }">
          <q-item-section avatar><q-icon name="groups" /></q-item-section>
          <q-item-section>Gospodarstwa domowe</q-item-section>
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
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { useAccountStore } from '@/features/accounts/store';
import { describeHouseholdError } from '@/features/households/errors';
import { useHouseholdStore } from '@/features/households/store';

const drawerOpen = ref(false);
const accounts = useAccountStore();
const households = useHouseholdStore();
const router = useRouter();
const quasar = useQuasar();

const householdOptions = computed(() =>
  households.households.map((household) => ({ id: household.id, label: household.name })),
);

async function signOut(): Promise<void> {
  await accounts.signOut();
  await router.push({ name: 'login' });
}

onMounted(() => {
  void households.load().catch((error: unknown) => {
    quasar.notify({ type: 'negative', message: describeHouseholdError(error) });
  });
});
</script>
