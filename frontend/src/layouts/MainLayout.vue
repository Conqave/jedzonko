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
                <q-item v-close-popup clickable :to="{ name: 'households' }">
                  <q-item-section avatar><q-icon name="home" /></q-item-section>
                  <q-item-section>Dom i członkowie</q-item-section>
                </q-item>
                <q-item
                  v-if="accounts.canViewPromotions"
                  v-close-popup
                  clickable
                  :to="{ name: 'promotions' }"
                >
                  <q-item-section avatar><q-icon name="local_offer" /></q-item-section>
                  <q-item-section>Promocje i sklepy</q-item-section>
                </q-item>
                <q-item v-close-popup clickable @click="openChangePassword">
                  <q-item-section avatar><q-icon name="password" /></q-item-section>
                  <q-item-section>Zmień hasło</q-item-section>
                </q-item>
                <q-separator />
                <q-item v-close-popup clickable @click="signOut">
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
        <q-item clickable :to="{ name: 'products' }">
          <q-item-section avatar><q-icon name="category" /></q-item-section>
          <q-item-section>Produkty</q-item-section>
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
          <q-item clickable @click="openChangePassword">
            <q-item-section avatar><q-icon name="password" /></q-item-section>
            <q-item-section>Zmień hasło</q-item-section>
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
import { useQuasar } from 'quasar';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import ChangePasswordDialog from '@/features/accounts/components/ChangePasswordDialog.vue';
import { useAccountStore } from '@/features/accounts/store';
import { HOUSEHOLD_ERROR_MESSAGES } from '@/features/households/errors';
import { useHouseholdStore } from '@/features/households/store';
import { useApiAction } from '@/shared/useApiAction';

const drawerOpen = ref(false);
const accounts = useAccountStore();
const households = useHouseholdStore();
const router = useRouter();
const quasar = useQuasar();
const { run } = useApiAction(HOUSEHOLD_ERROR_MESSAGES);

const householdOptions = computed(() =>
  households.households.map((household) => ({ id: household.id, label: household.name })),
);

function openChangePassword(): void {
  quasar.dialog({ component: ChangePasswordDialog }).onOk(() => {
    quasar.notify({ type: 'positive', message: 'Hasło zostało zmienione.' });
  });
}

async function signOut(): Promise<void> {
  await accounts.signOut();
  await router.push({ name: 'login' });
}

onMounted(() => {
  void run(() => households.load());
});
</script>
