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
      <template #body-cell-photo="props">
        <q-td :props="props">
          <q-avatar rounded size="40px" color="grey-3" text-color="grey-7">
            <img v-if="props.row.photo_url !== null" :src="props.row.photo_url" alt="Zdjęcie" />
            <span v-else :aria-label="props.row.product_name" :title="props.row.product_name">{{
              productEmoji(props.row.product_name)
            }}</span>
          </q-avatar>
        </q-td>
      </template>
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
          {{ formatQuantity(props.row.quantity) }} {{ props.row.unit_code }}
          <q-popup-edit
            #default="scope"
            :model-value="formatQuantity(props.row.quantity)"
            buttons
            label-set="Zapisz"
            label-cancel="Anuluj"
            @save="(value) => saveQuantity(props.row, String(value))"
          >
            <q-input v-model="scope.value" dense autofocus type="text" label="Ilość" />
          </q-popup-edit>
        </q-td>
      </template>
      <template #body-cell-category_name="props">
        <q-td :props="props">
          {{ props.row.category_name ?? '—' }}
          <q-popup-edit
            #default="scope"
            :model-value="props.row.category_id"
            buttons
            label-set="Zapisz"
            label-cancel="Anuluj"
            @save="(value) => saveCategory(props.row, value as number | null)"
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
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            flat
            dense
            round
            icon="edit"
            aria-label="Edytuj"
            @click="openEditDialog(props.row)"
          />
          <q-btn
            flat
            dense
            round
            icon="photo_camera"
            aria-label="Zdjęcie"
            @click="openPhotoDialog(props.row)"
          />
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
            <q-select
              v-model="form.categoryId"
              dense
              outlined
              clearable
              emit-value
              map-options
              use-input
              new-value-mode="add-unique"
              option-value="id"
              option-label="name"
              :options="categories"
              label="Kategoria (opcjonalnie)"
              hint="Wpisz nazwę i naciśnij Enter, aby dodać nową kategorię."
              @new-value="addCategory"
            />
            <q-input
              v-model="form.minimumQuantity"
              dense
              outlined
              label="Minimalna ilość (opcjonalnie)"
            />
            <q-file
              v-model="form.photo"
              dense
              outlined
              clearable
              accept="image/jpeg,image/png,image/webp"
              label="Zdjęcie (opcjonalnie)"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat label="Anuluj" no-caps />
            <q-btn type="submit" color="primary" label="Dodaj" no-caps :loading="saving" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="editDialogOpen">
      <q-card style="min-width: 340px">
        <q-card-section class="text-h6">Edytuj pozycję</q-card-section>
        <q-form @submit.prevent="submitEdit">
          <q-card-section class="q-gutter-sm">
            <q-input
              v-model="editForm.productName"
              dense
              outlined
              label="Nazwa produktu"
              :rules="[(value) => !!String(value).trim() || 'Podaj nazwę']"
            />
            <q-input
              v-model="editForm.quantity"
              dense
              outlined
              label="Ilość"
              :rules="[(value) => !!String(value).trim() || 'Podaj ilość']"
            />
            <q-select
              v-model="editForm.unitCode"
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
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat label="Anuluj" no-caps />
            <q-btn type="submit" color="primary" label="Zapisz" no-caps :loading="editSaving" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="photoDialogOpen">
      <q-card style="min-width: 320px">
        <q-card-section class="text-h6">Zdjęcie produktu</q-card-section>
        <q-card-section class="q-gutter-sm">
          <q-img
            v-if="photoItem !== null && photoItem.photo_url !== null"
            :src="photoItem.photo_url"
            style="max-height: 220px"
          />
          <div v-else class="text-center text-h2">
            {{ photoItem === null ? '📦' : productEmoji(photoItem.product_name) }}
          </div>
          <q-file
            v-model="photoFile"
            dense
            outlined
            clearable
            accept="image/jpeg,image/png,image/webp"
            label="Wybierz zdjęcie"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn
            v-if="photoItem !== null && photoItem.photo_url !== null"
            flat
            color="negative"
            label="Usuń zdjęcie"
            no-caps
            :loading="photoSaving"
            @click="removePhoto"
          />
          <q-btn v-close-popup flat label="Zamknij" no-caps />
          <q-btn
            color="primary"
            label="Zapisz"
            no-caps
            :disable="photoFile === null"
            :loading="photoSaving"
            @click="savePhoto"
          />
        </q-card-actions>
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
  createInventoryCategory,
  deleteInventoryItem,
  deleteInventoryItemPhoto,
  fetchInventory,
  fetchInventoryCategories,
  setInventoryItemCategory,
  updateInventoryItem,
  uploadInventoryItemPhoto,
} from '@/features/inventory/api';
import { describeInventoryError } from '@/features/inventory/errors';
import type { InventoryCategory, InventoryItem } from '@/features/inventory/models';
import { useHouseholdStore } from '@/features/households/store';
import { formatQuantity } from '@/features/shared/formatQuantity';
import { productEmoji } from '@/features/shared/productEmoji';

const quasar = useQuasar();
const households = useHouseholdStore();

const columns: QTableColumn<InventoryItem>[] = [
  { name: 'photo', label: '', field: 'photo_url', align: 'left' },
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
    field: (row) => (row.minimum_quantity === null ? '—' : formatQuantity(row.minimum_quantity)),
    align: 'left',
  },
  { name: 'actions', label: '', field: 'id', align: 'right' },
];

const MOBILE_COLUMNS = ['photo', 'product_name', 'quantity', 'actions'];

const visibleColumns = computed(() =>
  quasar.screen.lt.md ? MOBILE_COLUMNS : columns.map((column) => column.name),
);

const items = ref<InventoryItem[]>([]);
const categories = ref<InventoryCategory[]>([]);
const loading = ref(false);
const units = ref<MeasurementUnit[]>([]);
const addDialogOpen = ref(false);
const saving = ref(false);
const photoDialogOpen = ref(false);
const photoItem = ref<InventoryItem | null>(null);
const photoFile = ref<File | null>(null);
const photoSaving = ref(false);
const editDialogOpen = ref(false);
const editSaving = ref(false);
const editItem = ref<InventoryItem | null>(null);
const editForm = ref<{ productName: string; quantity: string; unitCode: string }>({
  productName: '',
  quantity: '',
  unitCode: '',
});

const form = ref<{
  product: Product | null;
  quantity: string;
  unitCode: string;
  minimumQuantity: string;
  categoryId: number | null;
  photo: File | null;
}>({
  product: null,
  quantity: '',
  unitCode: '',
  minimumQuantity: '',
  categoryId: null,
  photo: null,
});

function notifyError(error: unknown): void {
  quasar.notify({ type: 'negative', message: describeInventoryError(error) });
}

function replaceItem(updated: InventoryItem): void {
  items.value = items.value.map((entry) => (entry.id === updated.id ? updated : entry));
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

async function loadCategories(): Promise<void> {
  if (households.selectedId === null) {
    categories.value = [];
    return;
  }
  try {
    categories.value = await fetchInventoryCategories(households.selectedId);
  } catch (error) {
    categories.value = [];
    notifyError(error);
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
  form.value = {
    product: null,
    quantity: '',
    unitCode: '',
    minimumQuantity: '',
    categoryId: null,
    photo: null,
  };
  addDialogOpen.value = true;
}

function addCategory(name: string, done: (value: number) => void): void {
  const trimmed = name.trim();
  if (households.selectedId === null || trimmed === '') {
    return;
  }
  void createCategory(households.selectedId, trimmed, done);
}

async function createCategory(
  householdId: number,
  name: string,
  done: (value: number) => void,
): Promise<void> {
  try {
    const category = await createInventoryCategory(householdId, name);
    categories.value = [...categories.value, category];
    done(category.id);
  } catch (error) {
    notifyError(error);
  }
}

async function submitItem(): Promise<void> {
  const product = form.value.product;
  if (households.selectedId === null || product === null) {
    return;
  }
  saving.value = true;
  try {
    const minimum = form.value.minimumQuantity.trim();
    const categoryId = form.value.categoryId;
    const item = await addInventoryItem({
      household_id: households.selectedId,
      product_id: product.id,
      quantity: form.value.quantity.trim(),
      unit_code: form.value.unitCode,
      ...(minimum === '' ? {} : { minimum_quantity: minimum }),
      ...(categoryId === null ? {} : { category_id: categoryId }),
    });
    const photo = form.value.photo;
    const created = photo === null ? item : await uploadInventoryItemPhoto(item.id, photo);
    items.value = [...items.value, created];
    addDialogOpen.value = false;
  } catch (error) {
    notifyError(error);
    await loadItems();
  } finally {
    saving.value = false;
  }
}

async function saveQuantity(item: InventoryItem, quantity: string): Promise<void> {
  try {
    replaceItem(await updateInventoryItem(item.id, { quantity: quantity.trim() }));
  } catch (error) {
    notifyError(error);
    await loadItems();
  }
}

function openEditDialog(item: InventoryItem): void {
  editItem.value = item;
  editForm.value = {
    productName: item.product_name,
    quantity: formatQuantity(item.quantity),
    unitCode: item.unit_code,
  };
  editDialogOpen.value = true;
}

async function submitEdit(): Promise<void> {
  const item = editItem.value;
  if (item === null) {
    return;
  }
  editSaving.value = true;
  try {
    replaceItem(
      await updateInventoryItem(item.id, {
        product_name: editForm.value.productName.trim(),
        quantity: editForm.value.quantity.trim(),
        unit_code: editForm.value.unitCode,
      }),
    );
    editDialogOpen.value = false;
  } catch (error) {
    notifyError(error);
  } finally {
    editSaving.value = false;
  }
}

async function saveCategory(item: InventoryItem, categoryId: number | null): Promise<void> {
  try {
    replaceItem(await setInventoryItemCategory(item.id, categoryId));
  } catch (error) {
    notifyError(error);
    await loadItems();
  }
}

function openPhotoDialog(item: InventoryItem): void {
  photoItem.value = item;
  photoFile.value = null;
  photoDialogOpen.value = true;
}

async function savePhoto(): Promise<void> {
  const item = photoItem.value;
  const photo = photoFile.value;
  if (item === null || photo === null) {
    return;
  }
  photoSaving.value = true;
  try {
    const updated = await uploadInventoryItemPhoto(item.id, photo);
    replaceItem(updated);
    photoItem.value = updated;
    photoFile.value = null;
  } catch (error) {
    notifyError(error);
  } finally {
    photoSaving.value = false;
  }
}

async function removePhoto(): Promise<void> {
  const item = photoItem.value;
  if (item === null) {
    return;
  }
  photoSaving.value = true;
  try {
    const updated = await deleteInventoryItemPhoto(item.id);
    replaceItem(updated);
    photoItem.value = updated;
  } catch (error) {
    notifyError(error);
  } finally {
    photoSaving.value = false;
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
  void loadCategories();
});

watch(
  () => households.selectedId,
  () => {
    void loadItems();
    void loadCategories();
  },
);
</script>
