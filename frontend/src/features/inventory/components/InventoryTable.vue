<template>
  <q-table
    :rows="items"
    :columns="COLUMNS"
    row-key="id"
    :loading="busy"
    flat
    bordered
    :rows-per-page-options="[0]"
    no-data-label="Brak produktów w zapasach."
  >
    <template #body-cell-photo="cell">
      <q-td :props="cell">
        <q-avatar rounded size="40px" color="grey-3" text-color="grey-7">
          <img v-if="cell.row.photoUrl !== null" :src="cell.row.photoUrl" alt="Zdjęcie" />
          <span v-else :title="cell.row.productName">{{ productEmoji(cell.row.productName) }}</span>
        </q-avatar>
      </q-td>
    </template>
    <template #body-cell-productName="cell">
      <q-td :props="cell">
        {{ cell.row.productName }}
        <q-badge v-if="cell.row.isBelowMinimum" color="negative" class="q-ml-sm">
          poniżej minimum
        </q-badge>
      </q-td>
    </template>
    <template #body-cell-quantity="cell">
      <q-td :props="cell">
        <div class="row items-center no-wrap">
          <q-btn
            round
            dense
            flat
            icon="remove"
            color="primary"
            aria-label="Odejmij ilość"
            :disable="savingItemId === cell.row.id || isEmpty(cell.row.quantity)"
            @click="emit('step', cell.row, -1)"
          />
          <span class="q-px-sm">
            {{ formatQuantity(cell.row.quantity) }} {{ findUnitName(cell.row.unitCode) }}
          </span>
          <q-btn
            round
            dense
            flat
            icon="add"
            color="primary"
            aria-label="Dodaj ilość"
            :disable="savingItemId === cell.row.id"
            @click="emit('step', cell.row, 1)"
          />
        </div>
      </q-td>
    </template>
    <template #body-cell-categoryName="cell">
      <q-td :props="cell">
        {{ cell.row.categoryName ?? '—' }}
        <q-popup-edit
          #default="scope"
          :model-value="cell.row.categoryId"
          buttons
          label-set="Zapisz"
          label-cancel="Anuluj"
          @save="(value: number | null) => emit('set-category', cell.row, value)"
        >
          <q-select
            v-model="scope.value"
            dense
            autofocus
            clearable
            emit-value
            map-options
            option-value="id"
            option-label="name"
            :options="categories"
            label="Kategoria"
          />
        </q-popup-edit>
      </q-td>
    </template>
    <template #body-cell-actions="cell">
      <q-td :props="cell">
        <q-btn flat dense round icon="edit" aria-label="Edytuj" @click="emit('edit', cell.row)" />
        <q-btn flat dense round icon="more_vert" aria-label="Więcej">
          <q-menu>
            <q-list style="min-width: 160px">
              <q-item v-close-popup clickable @click="emit('photo', cell.row)">
                <q-item-section avatar><q-icon name="photo_camera" /></q-item-section>
                <q-item-section>Zdjęcie</q-item-section>
              </q-item>
              <q-item
                v-close-popup
                clickable
                class="text-negative"
                @click="emit('remove', cell.row)"
              >
                <q-item-section avatar><q-icon name="delete" color="negative" /></q-item-section>
                <q-item-section>Usuń z zapasów</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-td>
    </template>
  </q-table>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';
import { formatQuantity } from '@/shared/formatQuantity';
import { productEmoji } from '@/shared/productEmoji';
import {
  isEmpty,
  type InventoryCategory,
  type InventoryItem,
  type QuantityDirection,
} from '../model';

const COLUMNS: QTableColumn<InventoryItem>[] = [
  { name: 'photo', label: '', field: 'photoUrl', align: 'left' },
  { name: 'productName', label: 'Produkt', field: 'productName', align: 'left', sortable: true },
  { name: 'quantity', label: 'Ilość', field: 'quantity', align: 'left' },
  {
    name: 'categoryName',
    label: 'Kategoria',
    field: 'categoryName',
    align: 'left',
    sortable: true,
  },
  { name: 'actions', label: '', field: 'id', align: 'right' },
];

defineProps<{
  items: InventoryItem[];
  categories: InventoryCategory[];
  busy: boolean;
  savingItemId: number | null;
  findUnitName: (code: string) => string;
}>();

const emit = defineEmits<{
  step: [item: InventoryItem, direction: QuantityDirection];
  'set-category': [item: InventoryItem, categoryId: number | null];
  edit: [item: InventoryItem];
  photo: [item: InventoryItem];
  remove: [item: InventoryItem];
}>();
</script>
