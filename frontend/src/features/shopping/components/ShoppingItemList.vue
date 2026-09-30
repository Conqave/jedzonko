<template>
  <q-banner v-if="pendingItems.length === 0 && purchasedItems.length === 0" class="bg-grey-3">
    {{ isFiltered ? NO_MATCHES_LABEL : 'Lista jest pusta.' }}
  </q-banner>
  <div v-else-if="pendingItems.length > 0" class="row justify-end q-gutter-sm q-mb-sm">
    <q-btn
      flat
      no-caps
      color="primary"
      icon="auto_awesome"
      label="Otaguj listę"
      :loading="isTagging"
      @click="emit('tag')"
    />
    <q-btn
      color="positive"
      icon="done_all"
      no-caps
      :label="`Kupiono (${selectedIds.length})`"
      :disable="selectedIds.length === 0"
      @click="emit('buy', findSelectedItems())"
    />
    <q-btn
      outline
      color="negative"
      icon="delete"
      no-caps
      :label="`Usuń (${selectedIds.length})`"
      :disable="selectedIds.length === 0"
      @click="emit('remove-items', findSelectedItems())"
    />
  </div>
  <q-list v-if="pendingItems.length > 0 || purchasedItems.length > 0" bordered separator>
    <q-item v-for="item in pendingItems" :key="item.id">
      <q-item-section side>
        <q-checkbox v-model="selectedIds" :val="item.id" :aria-label="`Zaznacz: ${item.name}`" />
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ item.name }}</q-item-label>
        <q-item-label caption class="row wrap items-center">
          <q-chip
            v-for="tag in findItemTags(item)"
            :key="tag"
            dense
            square
            color="primary"
            text-color="white"
            class="q-ml-none shopping-tag"
            >{{ tag }}</q-chip
          >
          <span v-if="findItemTags(item).length === 0" class="text-grey-7">Bez tagu</span>
          <span v-if="!reachesPantry(item)" class="text-orange-9 q-ml-sm">
            <q-icon name="info" /> Nie trafi do zapasów
          </span>
        </q-item-label>
      </q-item-section>
      <q-item-section side class="shopping-quantity">
        {{ hasAmount(item) ? describeQuantity(item) : '' }}
      </q-item-section>
      <q-item-section side>
        <q-btn flat dense round icon="more_vert" :aria-label="`Więcej: ${item.name}`">
          <q-menu>
            <q-list style="min-width: 200px">
              <q-item v-close-popup clickable @click="emit('tag-item', item)">
                <q-item-section avatar><q-icon name="sell" /></q-item-section>
                <q-item-section>{{
                  item.subject.kind === 'text' ? 'Otaguj' : 'Zmień tag'
                }}</q-item-section>
              </q-item>
              <q-item
                v-if="item.subject.kind === 'ingredient'"
                v-close-popup
                clickable
                @click="emit('choose-product', item)"
              >
                <q-item-section avatar><q-icon name="inventory_2" /></q-item-section>
                <q-item-section>Wybierz produkt</q-item-section>
              </q-item>
              <q-item v-close-popup clickable class="text-negative" @click="emit('remove', item)">
                <q-item-section avatar><q-icon name="delete" color="negative" /></q-item-section>
                <q-item-section>Usuń</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-item-section>
    </q-item>
    <q-expansion-item
      v-if="purchasedItems.length > 0"
      icon="check_circle"
      :label="`Kupione (${purchasedItems.length})`"
      header-class="text-grey-8"
    >
      <div class="q-px-md q-pt-sm text-caption text-grey-7">
        Do zapasów trafiły pozycje z produktem lub tagiem. Pozycje bez tagu nie trafiły.
      </div>
      <q-item v-for="item in purchasedItems" :key="item.id">
        <q-item-section side>
          <q-checkbox
            :model-value="true"
            :aria-label="`Przywróć: ${item.name}`"
            @update:model-value="emit('restore', item)"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label class="text-strike text-grey">{{ item.name }}</q-item-label>
          <q-item-label v-if="hasAmount(item)" caption>{{ describeQuantity(item) }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { formatQuantity } from '@/shared/formatQuantity';
import { NO_MATCHES_LABEL } from '@/shared/listView';
import {
  findShoppingItemTags,
  findVisibleSelection,
  hasAmount,
  reachesPantry,
  type ShoppingItem,
} from '../model';

const props = defineProps<{
  pendingItems: ShoppingItem[];
  purchasedItems: ShoppingItem[];
  describeUnitQuantity: (quantity: string, unitCode: string) => string;
  findProductTags: (productId: number) => string[];
  isTagging: boolean;
  isFiltered: boolean;
}>();

const emit = defineEmits<{
  buy: [items: ShoppingItem[]];
  restore: [item: ShoppingItem];
  'choose-product': [item: ShoppingItem];
  'tag-item': [item: ShoppingItem];
  tag: [];
  remove: [item: ShoppingItem];
  'remove-items': [items: ShoppingItem[]];
}>();

const selectedIds = ref<number[]>([]);

watch(
  () => props.pendingItems,
  (visiblePending) => {
    const kept = findVisibleSelection(visiblePending, selectedIds.value);
    selectedIds.value = kept.map((item) => item.id);
  },
);

function findSelectedItems(): ShoppingItem[] {
  return findVisibleSelection(props.pendingItems, selectedIds.value);
}

function findItemTags(item: ShoppingItem): string[] {
  return findShoppingItemTags(item, props.findProductTags);
}

function describeQuantity(item: ShoppingItem): string {
  return item.unitCode === null
    ? formatQuantity(item.quantity)
    : props.describeUnitQuantity(item.quantity, item.unitCode);
}
</script>

<style scoped>
.shopping-quantity {
  min-width: 5.5rem;
  align-items: flex-end;
}

.shopping-tag {
  height: auto;
  max-width: 100%;
}

.shopping-tag :deep(.q-chip__content) {
  white-space: normal;
  overflow-wrap: anywhere;
}
</style>
