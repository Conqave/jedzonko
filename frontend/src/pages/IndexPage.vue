<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Witaj, {{ accounts.user?.username }}</div>
    <q-list bordered separator>
      <q-item>
        <q-item-section>Dostęp do promocji</q-item-section>
        <q-item-section side>
          <q-badge :color="accounts.canViewPromotions ? 'positive' : 'grey'">
            {{ accounts.canViewPromotions ? 'tak' : 'nie' }}
          </q-badge>
        </q-item-section>
      </q-item>
      <q-item>
        <q-item-section>Konto administratora</q-item-section>
        <q-item-section side>
          <q-badge :color="accounts.user?.is_staff ? 'positive' : 'grey'">
            {{ accounts.user?.is_staff ? 'tak' : 'nie' }}
          </q-badge>
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { useAccountStore } from '@/features/accounts/store';

const accounts = useAccountStore();
</script>
