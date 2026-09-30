<template>
  <q-banner v-if="pendingItems.length === 0 && purchasedItems.length === 0" class="bg-grey-3">
    Lista jest pusta.
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
      @click="buySelected"
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
        </q-item-label>
      </q-item-section>
      <q-item-section side>{{ describeQuantity(item) }}</q-item-section>
      <q-item-section side>
        <q-btn
          v-if="item.subject.kind === 'ingredient'"
          flat
          dense
          round
          icon="inventory_2"
          :aria-label="`Wybierz produkt dla ${item.name}`"
          @click="emit('choose-product', item)"
        />
      </q-item-section>
      <q-item-section side>
        <q-btn
          flat
          dense
          round
          color="negative"
          icon="delete"
          :aria-label="`Usuń ${item.name}`"
          @click="emit('remove', item)"
        />
      </q-item-section>
    </q-item>
    <q-expansion-item
      v-if="purchasedItems.length > 0"
      icon="check_circle"
      :label="`Kupione (${purchasedItems.length})`"
      header-class="text-grey-8"
    >
      <div class="q-px-md q-pt-sm text-caption text-grey-7">
        Kupione produkty trafiły do zapasów.
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
          <q-item-label caption>{{ describeQuantity(item) }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { formatQuantity } from '@/shared/formatQuantity';
import type { ShoppingItem } from '../model';

const props = defineProps<{
  pendingItems: ShoppingItem[];
  purchasedItems: ShoppingItem[];
  describeUnitQuantity: (quantity: string, unitCode: string) => string;
  findProductTags: (productId: number) => string[];
  isTagging: boolean;
}>();

const emit = defineEmits<{
  buy: [itemIds: number[]];
  restore: [item: ShoppingItem];
  'choose-product': [item: ShoppingItem];
  tag: [];
  remove: [item: ShoppingItem];
}>();

const selectedIds = ref<number[]>([]);

watch(
  () => props.pendingItems,
  (pending) => {
    const pendingIds = new Set(pending.map((item) => item.id));
    selectedIds.value = selectedIds.value.filter((id) => pendingIds.has(id));
  },
);

function buySelected(): void {
  emit('buy', [...selectedIds.value]);
}

function findItemTags(item: ShoppingItem): string[] {
  if (item.subject.kind === 'product') {
    return props.findProductTags(item.subject.productId);
  }
  if (item.subject.kind === 'ingredient') {
    return [item.name];
  }
  return [];
}

function describeQuantity(item: ShoppingItem): string {
  return item.unitCode === null
    ? formatQuantity(item.quantity)
    : props.describeUnitQuantity(item.quantity, item.unitCode);
}
</script>

<style scoped>
.shopping-tag {
  height: auto;
  max-width: 100%;
}

.shopping-tag :deep(.q-chip__content) {
  white-space: normal;
  overflow-wrap: anywhere;
}
</style>
