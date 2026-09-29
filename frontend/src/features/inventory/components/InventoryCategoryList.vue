<template>
  <q-list bordered separator>
    <q-item v-for="category in categories" :key="category.id">
      <q-item-section>{{ category.name }}</q-item-section>
      <q-item-section side>
        <div class="row no-wrap q-gutter-xs">
          <q-btn
            flat
            dense
            round
            icon="edit"
            :aria-label="`Zmień nazwę ${category.name}`"
            @click="emit('rename', category)"
          />
          <q-btn
            flat
            dense
            round
            color="negative"
            icon="delete"
            :aria-label="`Usuń ${category.name}`"
            @click="emit('remove', category)"
          />
        </div>
      </q-item-section>
    </q-item>
    <q-item v-if="categories.length === 0">
      <q-item-section class="text-grey"
        >Brak kategorii. Dodasz je przy pozycji w zapasach.</q-item-section
      >
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import type { InventoryCategory } from '../model';

defineProps<{ categories: InventoryCategory[] }>();

const emit = defineEmits<{
  rename: [category: InventoryCategory];
  remove: [category: InventoryCategory];
}>();
</script>
