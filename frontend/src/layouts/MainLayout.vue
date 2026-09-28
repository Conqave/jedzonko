<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="drawerOpen = !drawerOpen" />
        <q-toolbar-title>jedzonko</q-toolbar-title>
        <template v-if="quasar.screen.gt.sm">
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
                <q-item clickable v-close-popup :to="{ name: 'households' }">
                  <q-item-section avatar><q-icon name="home" /></q-item-section>
                  <q-item-section>Dom i członkowie</q-item-section>
                </q-item>
                <q-item
                  v-if="accounts.canViewPromotions"
                  clickable
                  v-close-popup
                  :to="{ name: 'promotions' }"
                >
                  <q-item-section avatar><q-icon name="local_offer" /></q-item-section>
                  <q-item-section>Promocje i sklepy</q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable v-close-popup @click="signOut">
                  <q-item-section avatar><q-icon name="logout" /></q-item-section>
                  <q-item-section>Wyloguj</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </template>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawerOpen" show-if-above bordered :width="280">
      <q-list>
        <template v-if="!quasar.screen.gt.sm">
          <q-item v-if="households.hasHousehold">
            <q-item-section>
              <q-select
                :model-value="households.selectedId"
                dense
                outlined
                emit-value
                map-options
                option-value="id"
                :options="householdOptions"
                label="Gospodarstwo"
                @update:model-value="households.select"
              />
            </q-item-section>
          </q-item>
          <q-separator />
        </template>

        <q-item-label header>Nawigacja</q-item-label>
        <q-item clickable :to="{ name: 'inventory' }">
          <q-item-section avatar><q-icon name="kitchen" /></q-item-section>
          <q-item-section>Zapasy</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'recipes' }">
          <q-item-section avatar><q-icon name="restaurant_menu" /></q-item-section>
          <q-item-section>Przepisy</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'shopping' }">
          <q-item-section avatar><q-icon name="shopping_cart" /></q-item-section>
          <q-item-section>Zakupy</q-item-section>
        </q-item>
        <q-item v-if="accounts.canViewPromotions" clickable :to="{ name: 'promotions' }">
          <q-item-section avatar><q-icon name="local_offer" /></q-item-section>
          <q-item-section>Promocje i sklepy</q-item-section>
        </q-item>
        <template v-if="!quasar.screen.gt.sm">
          <q-separator class="q-my-sm" />
          <q-item-label header>{{ accounts.user?.username ?? '' }}</q-item-label>
          <q-item clickable :to="{ name: 'households' }">
            <q-item-section avatar><q-icon name="home" /></q-item-section>
            <q-item-section>Dom i członkowie</q-item-section>
          </q-item>
          <q-item clickable @click="signOut">
            <q-item-section avatar><q-icon name="logout" /></q-item-section>
            <q-item-section>Wyloguj</q-item-section>
          </q-item>
        </template>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>

    <q-footer v-if="!quasar.screen.gt.sm" bordered class="bg-white text-primary">
      <q-tabs no-caps active-color="primary" indicator-color="primary" align="justify">
        <q-route-tab name="inventory" icon="kitchen" label="Zapasy" :to="{ name: 'inventory' }" />
        <q-route-tab
          name="recipes"
          icon="restaurant_menu"
          label="Przepisy"
          :to="{ name: 'recipes' }"
        />
        <q-route-tab
          name="shopping"
          icon="shopping_cart"
          label="Zakupy"
          :to="{ name: 'shopping' }"
        />
      </q-tabs>
    </q-footer>
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
