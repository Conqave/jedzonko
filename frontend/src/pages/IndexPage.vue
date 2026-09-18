<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Witaj, {{ accounts.user?.username }}</div>

    <q-banner v-if="households.loaded && !households.hasHousehold" class="bg-grey-3 q-mb-md">
      Nie masz jeszcze gospodarstwa domowego.
      <template #action>
        <q-btn flat no-caps color="primary" label="Utwórz" :to="{ name: 'households' }" />
      </template>
    </q-banner>

    <q-list bordered separator>
      <q-item clickable :to="{ name: 'inventory' }">
        <q-item-section avatar><q-icon name="kitchen" /></q-item-section>
        <q-item-section>
          <q-item-label>Mam w domu</q-item-label>
          <q-item-label caption>Zapasy gospodarstwa domowego</q-item-label>
        </q-item-section>
      </q-item>
      <q-item clickable :to="{ name: 'recipes' }">
        <q-item-section avatar><q-icon name="restaurant_menu" /></q-item-section>
        <q-item-section>
          <q-item-label>Przepisy</q-item-label>
          <q-item-label caption>Propozycje z tego, co masz w domu</q-item-label>
        </q-item-section>
      </q-item>
      <q-item clickable :to="{ name: 'shopping' }">
        <q-item-section avatar><q-icon name="shopping_cart" /></q-item-section>
        <q-item-section>
          <q-item-label>Listy zakupów</q-item-label>
          <q-item-label caption>Brakujące produkty i zakupy</q-item-label>
        </q-item-section>
      </q-item>
      <q-item clickable :to="{ name: 'households' }">
        <q-item-section avatar><q-icon name="groups" /></q-item-section>
        <q-item-section>
          <q-item-label>Gospodarstwa domowe</q-item-label>
          <q-item-label caption>Członkowie i wybór gospodarstwa</q-item-label>
        </q-item-section>
      </q-item>
      <q-item v-if="accounts.canViewPromotions" clickable :to="{ name: 'promotions' }">
        <q-item-section avatar><q-icon name="local_offer" /></q-item-section>
        <q-item-section>
          <q-item-label>Promocje</q-item-label>
          <q-item-label caption>Wyszukiwanie promocji i porównanie sklepów</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { useAccountStore } from '@/features/accounts/store';
import { useHouseholdStore } from '@/features/households/store';

const accounts = useAccountStore();
const households = useHouseholdStore();
</script>
