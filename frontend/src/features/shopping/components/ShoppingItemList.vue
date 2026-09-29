<template>
  <q-banner v-if="pendingItems.length === 0 && purchasedItems.length === 0" class="bg-grey-3">
    Lista jest pusta.
  </q-banner>
  <q-list v-else bordered separator>
    <q-item v-for="item in pendingItems" :key="item.id">
      <q-item-section side>
        <q-checkbox
          :model-value="false"
          :aria-label="`Kupione: ${item.name}`"
          @update:model-value="emit('buy', item)"
        />
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ item.name }}</q-item-label>
        <q-item-label caption>{{ SUBJECT_LABELS[item.subject.kind] }}</q-item-label>
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
import { formatQuantity } from '@/shared/formatQuantity';
import type { ShoppingItem, ShoppingSubject } from '../model';

const SUBJECT_LABELS: Readonly<Record<ShoppingSubject['kind'], string>> = {
  product: 'Produkt',
  ingredient: 'Dowolny produkt z tym składnikiem',
  text: 'Tekst własny',
};

const props = defineProps<{
  pendingItems: ShoppingItem[];
  purchasedItems: ShoppingItem[];
  findUnitName: (code: string) => string;
}>();

const emit = defineEmits<{
  buy: [item: ShoppingItem];
  restore: [item: ShoppingItem];
  'choose-product': [item: ShoppingItem];
  remove: [item: ShoppingItem];
}>();

function describeQuantity(item: ShoppingItem): string {
  const amount = formatQuantity(item.quantity);
  return item.unitCode === null ? amount : `${amount} ${props.findUnitName(item.unitCode)}`;
}
</script>
