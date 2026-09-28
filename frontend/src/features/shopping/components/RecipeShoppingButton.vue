<template>
  <div class="row no-wrap items-center q-gutter-sm">
    <q-select
      v-model="listId"
      class="col"
      dense
      outlined
      emit-value
      map-options
      option-value="id"
      option-label="name"
      label="Lista zakupów"
      :options="lists"
      :loading="busy"
    />
    <q-btn
      color="primary"
      no-caps
      icon="add_shopping_cart"
      label="Dodaj brakujące"
      :disable="listId === null"
      :loading="busy"
      @click="add"
    />
  </div>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref, watch } from 'vue';
import type { RecipeShoppingSource } from '../model';
import { useRecipeShopping } from '../useRecipeShopping';

const props = defineProps<{ householdId: number; source: RecipeShoppingSource }>();

const emit = defineEmits<{ added: [] }>();

const quasar = useQuasar();
const { lists, busy, loadLists, addToList } = useRecipeShopping();
const listId = ref<number | null>(null);

async function loadHouseholdLists(): Promise<void> {
  await loadLists(props.householdId);
  listId.value = lists.value[0]?.id ?? null;
}

async function add(): Promise<void> {
  const chosen = listId.value;
  if (chosen === null) {
    return;
  }
  const isAdded = await addToList(chosen, props.source);
  if (!isAdded) {
    return;
  }
  quasar.notify({ type: 'positive', message: 'Brakujące składniki są na liście zakupów.' });
  emit('added');
}

watch(() => props.householdId, loadHouseholdLists, { immediate: true });
</script>
