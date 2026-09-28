<template>
  <q-banner v-if="items.length > 0" class="bg-orange-1 q-mb-md">
    <div class="text-weight-medium">Kończą się produkty: {{ items.length }}</div>
    <div class="text-caption q-mt-xs">{{ names }}</div>
    <template #action>
      <q-btn flat no-caps color="primary" label="Przejdź do zakupów" :to="{ name: 'shopping' }" />
    </template>
  </q-banner>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { InventoryItem } from '../model';

const props = defineProps<{ items: InventoryItem[] }>();

const names = computed(() => props.items.map((item) => item.productName).join(', '));
</script>
