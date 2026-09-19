<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5 col">Mam w domu</div>
      <q-btn
        color="primary"
        icon="add"
        label="Dodaj produkt"
        no-caps
        :disable="households.selectedId === null"
        @click="openAddDialog"
      />
    </div>

    <q-banner v-if="households.selectedId === null" class="bg-grey-3">
      Wybierz gospodarstwo domowe, aby zobaczyć zapasy.
    </q-banner>

    <q-table
      v-else
      :rows="items"
      :columns="columns"
      :visible-columns="visibleColumns"
      row-key="id"
      :loading="loading"
      flat
      bordered
      :rows-per-page-options="[0]"
      no-data-label="Brak produktów w zapasach."
    >
      <template #body-cell-product_name="props">
        <q-td :props="props">
          {{ props.row.product_name }}
          <q-badge v-if="props.row.below_minimum" color="negative" class="q-ml-sm">
            poniżej minimum
          </q-badge>
        </q-td>
      </template>
      <template #body-cell-quantity="props">
        <q-td :props="props">
          {{ props.row.quantity }} {{ props.row.unit_code }}
          <q-popup-edit
            #default="scope"
            :model-value="props.row.quantity"
            buttons
            label-set="Zapisz"
            label-cancel="Anuluj"
            @save="(value) => saveQuantity(props.row, String(value))"
          >
            <q-input v-model="scope.value" dense autofocus type="text" label="Ilość" />
          </q-popup-edit>
        </q-td>
      </template>
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            flat
            dense
            round
            color="negative"
            icon="delete"
            aria-label="Usuń"
            @click="confirmDelete(props.row)"
          />
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="addDialogOpen">
      <q-card style="min-width: 340px">
        <q-card-section class="text-h6">Dodaj produkt</q-card-section>
        <q-form @submit.prevent="submitItem">
          <q-card-section class="q-gutter-sm">
            <product-picker
              v-if="households.selectedId !== null"
              v-model="form.product"
              :household-id="households.selectedId"
              :units="units"
              :rules="[(value) => value !== null || 'Wybierz produkt']"
              @update:model-value="applyDefaultUnit"
            />
            <q-input
              v-model="form.quantity"
              dense
              outlined
              label="Ilość"
              :rules="[(value) => !!value || 'Podaj ilość']"
            />
            <q-select
              v-model="form.unitCode"
              dense
              outlined
              label="Jednostka"
              emit-value
              map-options
              option-value="code"
              option-label="name"
              :options="units"
              :rules="[(value) => !!value || 'Wybierz jednostkę']"
            />
            <q-input
              v-model="form.minimumQuantity"
              dense
              outlined
              label="Minimalna ilość (opcjonalnie)"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat label="Anuluj" no-caps />
            <q-btn type="submit" color="primary" label="Dodaj" no-caps :loading="saving" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useQuasar, type QTableColumn } from 'quasar';
import { fetchUnits } from '@/features/products/api';
import type { MeasurementUnit, Product } from '@/features/products/models';
import ProductPicker from '@/features/products/ProductPicker.vue';
import {
  addInventoryItem,
  deleteInventoryItem,
  fetchInventory,
  updateInventoryQuantity,
} from '@/features/inventory/api';
import { describeInventoryError } from '@/features/inventory/errors';
import type { InventoryItem } from '@/features/inventory/models';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const households = useHouseholdStore();

const columns: QTableColumn<InventoryItem>[] = [
  {
    name: 'product_name',
    label: 'Produkt',
    field: 'product_name',
    align: 'left',
    sortable: true,
  },
  { name: 'quantity', label: 'Ilość', field: 'quantity', align: 'left' },
  {
    name: 'category_name',
    label: 'Kategoria',
    field: (row) => row.category_name ?? '—',
    align: 'left',
    sortable: true,
  },
  {
    name: 'minimum_quantity',
    label: 'Minimum',
    field: (row) => row.minimum_quantity ?? '—',
    align: 'left',
  },
  { name: 'actions', label: '', field: 'id', align: 'right' },
];

const MOBILE_COLUMNS = ['product_name', 'quantity', 'actions'];

const visibleColumns = computed(() =>
  quasar.screen.lt.md ? MOBILE_COLUMNS : columns.map((column) => column.name),
);

const items = ref<InventoryItem[]>([]);
const loading = ref(false);
const units = ref<MeasurementUnit[]>([]);
const addDialogOpen = ref(false);
const saving = ref(false);

const form = ref<{
  product: Product | null;
  quantity: string;
  unitCode: string;
  minimumQuantity: string;
}>({ product: null, quantity: '', unitCode: '', minimumQuantity: '' });

function notifyError(error: unknown): void {
  quasar.notify({ type: 'negative', message: describeInventoryError(error) });
}

async function loadItems(): Promise<void> {
  if (households.selectedId === null) {
    items.value = [];
    return;
  }
  loading.value = true;
  try {
    items.value = await fetchInventory(households.selectedId);
  } catch (error) {
    items.value = [];
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

async function loadUnits(): Promise<void> {
  try {
    units.value = await fetchUnits();
  } catch (error) {
    notifyError(error);
  }
}

function applyDefaultUnit(product: Product | null): void {
  if (product !== null && form.value.unitCode === '') {
    form.value.unitCode = product.default_unit_code;
  }
}

function openAddDialog(): void {
  form.value = { product: null, quantity: '', unitCode: '', minimumQuantity: '' };
  addDialogOpen.value = true;
}

async function submitItem(): Promise<void> {
  const product = form.value.product;
  if (households.selectedId === null || product === null) {
    return;
  }
  saving.value = true;
  try {
    const minimum = form.value.minimumQuantity.trim();
    const item = await addInventoryItem({
      household_id: households.selectedId,
      product_id: product.id,
      quantity: form.value.quantity.trim(),
      unit_code: form.value.unitCode,
      ...(minimum === '' ? {} : { minimum_quantity: minimum }),
    });
    items.value = [...items.value, item];
    addDialogOpen.value = false;
  } catch (error) {
    notifyError(error);
  } finally {
    saving.value = false;
  }
}

async function saveQuantity(item: InventoryItem, quantity: string): Promise<void> {
  try {
    const updated = await updateInventoryQuantity(item.id, quantity.trim());
    items.value = items.value.map((entry) => (entry.id === updated.id ? updated : entry));
  } catch (error) {
    notifyError(error);
    await loadItems();
  }
}

function confirmDelete(item: InventoryItem): void {
  quasar
    .dialog({
      title: 'Usunąć produkt?',
      message: `Czy usunąć ${item.product_name} z zapasów?`,
      cancel: true,
      persistent: true,
    })
    .onOk(() => {
      void doDelete(item);
    });
}

async function doDelete(item: InventoryItem): Promise<void> {
  try {
    await deleteInventoryItem(item.id);
    items.value = items.value.filter((entry) => entry.id !== item.id);
  } catch (error) {
    notifyError(error);
  }
}

onMounted(() => {
  void loadUnits();
  void loadItems();
});

watch(
  () => households.selectedId,
  () => {
    void loadItems();
  },
);
</script>
