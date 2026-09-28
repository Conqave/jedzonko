<template>
  <div class="row no-wrap items-center q-gutter-sm q-mb-md">
    <q-select
      class="col"
      :model-value="selectedListId"
      dense
      outlined
      emit-value
      map-options
      option-value="id"
      option-label="name"
      :options="lists"
      label="Lista"
      :loading="busy"
      @update:model-value="(value: number) => emit('select', value)"
    >
      <template #option="scope">
        <q-item v-bind="scope.itemProps">
          <q-item-section>
            <q-item-label>{{ scope.opt.name }}</q-item-label>
            <q-item-label caption>
              <template v-if="scope.opt.isPrimary">Główna · </template>Pozycje:
              {{ scope.opt.itemCount }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </q-select>
    <q-btn flat round icon="more_vert" aria-label="Opcje listy">
      <q-menu>
        <q-list style="min-width: 240px">
          <q-item v-close-popup clickable @click="emit('create')">
            <q-item-section avatar><q-icon name="add" /></q-item-section>
            <q-item-section>Utwórz nową listę</q-item-section>
          </q-item>
          <q-item v-close-popup clickable @click="emit('refill')">
            <q-item-section avatar><q-icon name="sync" /></q-item-section>
            <q-item-section>Uzupełnij minimalne zapasy</q-item-section>
          </q-item>
          <template v-if="selectedList !== null">
            <q-item v-close-popup clickable @click="emit('rename', selectedList)">
              <q-item-section avatar><q-icon name="edit" /></q-item-section>
              <q-item-section>Zmień nazwę</q-item-section>
            </q-item>
            <q-item v-if="canSplit" v-close-popup clickable @click="emit('split')">
              <q-item-section avatar><q-icon name="local_offer" /></q-item-section>
              <q-item-section>Podziel według promocji</q-item-section>
            </q-item>
            <q-separator />
            <q-item
              v-close-popup
              clickable
              class="text-negative"
              :disable="selectedList.isPrimary"
              @click="emit('remove', selectedList)"
            >
              <q-item-section avatar><q-icon name="delete" color="negative" /></q-item-section>
              <q-item-section>Usuń listę</q-item-section>
            </q-item>
          </template>
        </q-list>
      </q-menu>
    </q-btn>
  </div>
</template>

<script setup lang="ts">
import type { ShoppingList } from '../model';

defineProps<{
  lists: ShoppingList[];
  selectedListId: number | null;
  selectedList: ShoppingList | null;
  canSplit: boolean;
  busy: boolean;
}>();

const emit = defineEmits<{
  select: [listId: number];
  create: [];
  refill: [];
  rename: [list: ShoppingList];
  split: [];
  remove: [list: ShoppingList];
}>();
</script>
