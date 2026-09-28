<template>
  <q-page padding>
    <div class="row items-center q-mb-md q-col-gutter-sm">
      <div class="text-h5 col">Zapasy</div>
      <q-btn
        color="primary"
        icon="add"
        label="Dodaj produkt"
        no-caps
        :disable="households.selectedId === null"
        @click="openAddDialog"
      />
    </div>

    <q-banner v-if="belowMinimumItems.length > 0" class="bg-orange-1 q-mb-md">
      <div class="text-weight-medium">
        Kończą się {{ belowMinimumItems.length }}
        {{ belowMinimumItems.length === 1 ? 'produkt' : 'produkty' }}
      </div>
      <div class="text-caption q-mt-xs">
        {{ belowMinimumItems.map((item) => item.product_name).join(', ') }}
      </div>
      <template #action>
        <q-btn flat no-caps color="primary" label="Dodaj do zakupów" :to="{ name: 'shopping' }" />
      </template>
    </q-banner>

    <q-card v-if="proposals.length > 0" flat bordered class="q-mb-md">
      <q-card-section class="text-subtitle1">Propozycje dopasowania składników</q-card-section>
      <q-separator />
      <q-list separator>
        <q-item v-for="proposal in proposals" :key="proposal.id">
          <q-item-section>
            <q-item-label>
              Czy «{{ proposal.product_name }}» to «{{ proposal.requirement_name }}»?
            </q-item-label>
            <q-item-label caption>Sprawdź i zatwierdź mapowanie produktu.</q-item-label>
          </q-item-section>
          <q-item-section side>
            <div class="q-gutter-sm">
              <q-btn
                color="positive"
                icon="check"
                label="Tak"
                no-caps
                dense
                :loading="resolvingId === proposal.id"
                @click="acceptProposal(proposal)"
              />
              <q-btn
                flat
                color="negative"
                icon="close"
                label="Nie"
                no-caps
                dense
                :loading="resolvingId === proposal.id"
                @click="rejectProposal(proposal)"
              />
            </div>
          </q-item-section>
        </q-item>
      </q-list>
    </q-card>

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
          <div class="quantity-control row items-center no-wrap">
            <q-btn
              round
              dense
              flat
              icon="remove"
              color="primary"
              aria-label="Odejmij ilość"
              :disable="quantitySavingId === props.row.id || Number(props.row.quantity) <= 0"
              :loading="quantitySavingId === props.row.id && quantitySavingDelta < 0"
              @click="adjustQuantity(props.row, -1)"
            />
            <span class="quantity-value text-center">
              {{ formatQuantity(props.row.quantity) }} {{ props.row.unit_code }}
            </span>
            <q-btn
              round
              dense
              flat
              icon="add"
              color="primary"
              aria-label="Dodaj ilość"
              :disable="quantitySavingId === props.row.id"
              :loading="quantitySavingId === props.row.id && quantitySavingDelta > 0"
              @click="adjustQuantity(props.row, 1)"
            />
          </div>
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
      <template #body-cell-tags="props">
        <q-td :props="props">
          <q-chip v-for="tag in props.row.tags" :key="tag" dense square color="grey-3">
            {{ tag }}
          </q-chip>
          <span v-if="props.row.tags.length === 0">—</span>
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
          <q-btn flat dense round icon="more_vert" aria-label="Więcej">
            <q-menu>
              <q-list style="min-width: 160px">
                <q-item clickable v-close-popup @click="openPhotoDialog(props.row)">
                  <q-item-section avatar><q-icon name="photo_camera" /></q-item-section>
                  <q-item-section>Zdjęcie</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="reanalyzeProductTag(props.row)">
                  <q-item-section avatar><q-icon name="refresh" color="primary" /></q-item-section>
                  <q-item-section>Ponów analizę tagu</q-item-section>
                </q-item>
                <q-item
                  clickable
                  v-close-popup
                  class="text-negative"
                  @click="confirmDelete(props.row)"
                >
                  <q-item-section avatar><q-icon name="delete" color="negative" /></q-item-section>
                  <q-item-section>Usuń produkt</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
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
            <q-select
              v-model="editForm.tags"
              dense
              outlined
              multiple
              use-input
              use-chips
              label="Tagi produktu"
              hint="Wybierz wyłącznie tag z katalogu Ania Gotuje"
              :options="tagOptions"
              @filter="filterTagOptions"
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
import {
  addProductTag,
  acceptTagProposal,
  fetchTagProposals,
  fetchProductTags,
  deleteProductTag,
  searchProductTags,
  fetchTagAnalysisStatus,
  startTagAnalysis,
  fetchUnits,
  rejectTagProposal,
} from '@/features/products/api';
import type { TagProposal, MeasurementUnit, Product } from '@/features/products/models';
import { describeProductError } from '@/features/products/errors';
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
  { name: 'tags', label: 'Tagi', field: 'tags', align: 'left' },
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

const PRIMARY_COLUMNS = ['photo', 'product_name', 'tags', 'quantity', 'actions'];

const visibleColumns = computed(() => PRIMARY_COLUMNS);

const items = ref<InventoryItem[]>([]);
const belowMinimumItems = computed(() => items.value.filter((item) => item.below_minimum));
const proposals = ref<TagProposal[]>([]);
const resolvingId = ref<number | null>(null);
const quantitySavingId = ref<number | null>(null);
const quantitySavingDelta = ref(0);
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
const editForm = ref<{ productName: string; quantity: string; unitCode: string; tags: string[] }>({
  productName: '',
  quantity: '',
  unitCode: '',
  tags: [],
});
const tagOptions = ref<string[]>([]);
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

async function loadProposals(): Promise<void> {
  if (households.selectedId === null) {
    proposals.value = [];
    return;
  }
  try {
    proposals.value = await fetchTagProposals(households.selectedId);
  } catch (error) {
    proposals.value = [];
    notifyError(error);
  }
}

function dropProposal(proposalId: number): void {
  proposals.value = proposals.value.filter((entry) => entry.id !== proposalId);
}

async function acceptProposal(proposal: TagProposal): Promise<void> {
  resolvingId.value = proposal.id;
  try {
    await acceptTagProposal(proposal.id);
    dropProposal(proposal.id);
    await loadItems();
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeProductError(error) });
  } finally {
    resolvingId.value = null;
  }
}

async function rejectProposal(proposal: TagProposal): Promise<void> {
  resolvingId.value = proposal.id;
  try {
    await rejectTagProposal(proposal.id);
    dropProposal(proposal.id);
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeProductError(error) });
  } finally {
    resolvingId.value = null;
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
    void analyzeProductTag(created);
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

async function analyzeProductTag(item: InventoryItem): Promise<void> {
  if (households.selectedId === null) return;
  try {
    const jobId = await startTagAnalysis(households.selectedId, item.product_id);
    const progress = quasar.notify({
      type: 'info',
      message: `Analiza tagu: ${item.product_name}…`,
      timeout: 0,
      group: 'inventory-tag-analysis',
      actions: [{ label: 'Zamknij', color: 'white', handler: () => undefined }],
    });
    let status = await fetchTagAnalysisStatus(jobId);
    while (status.status === 'running') {
      await new Promise((resolve) => window.setTimeout(resolve, 400));
      status = await fetchTagAnalysisStatus(jobId);
    }
    progress();
    if (status.status === 'completed') {
      await loadItems();
      quasar.notify({
        type: 'positive',
        message: `Zakończono analizę tagu: ${item.product_name}.`,
      });
    } else {
      quasar.notify({
        type: 'negative',
        message: `Analiza tagu nie powiodła się: ${item.product_name}.`,
      });
    }
  } catch (error) {
    notifyError(error);
  }
}

function reanalyzeProductTag(item: InventoryItem): void {
  void analyzeProductTag(item);
}

async function adjustQuantity(item: InventoryItem, direction: -1 | 1): Promise<void> {
  const current = Number(item.quantity);
  if (!Number.isFinite(current)) {
    return;
  }
  const step = item.unit_code === 'szt' || item.unit_code === 'opak' ? 1 : 0.1;
  const next = Math.max(0, Math.round((current + direction * step) * 1000) / 1000);
  quantitySavingId.value = item.id;
  quantitySavingDelta.value = direction;
  try {
    replaceItem(await updateInventoryItem(item.id, { quantity: String(next) }));
  } catch (error) {
    notifyError(error);
    await loadItems();
  } finally {
    quantitySavingId.value = null;
    quantitySavingDelta.value = 0;
  }
}

function openEditDialog(item: InventoryItem): void {
  editItem.value = item;
  editForm.value = {
    productName: item.product_name,
    quantity: formatQuantity(item.quantity),
    unitCode: item.unit_code,
    tags: [],
  };
  void fetchProductTags(item.product_id).then((tags) => {
    editForm.value.tags = tags.map((tag) => tag.name);
  });
  editDialogOpen.value = true;
}

function filterTagOptions(value: string, update: (callback: () => void) => void): void {
  if (households.selectedId === null) return;
  void searchProductTags(households.selectedId, value).then((tags) => {
    update(() => {
      tagOptions.value = tags;
    });
  });
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
    const desiredTags = editForm.value.tags.map((tag) => tag.trim()).filter(Boolean);
    const currentTags = await fetchProductTags(item.product_id);
    for (const tag of desiredTags) {
      if (!currentTags.some((current) => current.name === tag)) {
        await addProductTag(item.product_id, tag);
      }
    }
    for (const tag of currentTags) {
      if (!desiredTags.includes(tag.name)) await deleteProductTag(tag.id);
    }
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
  void loadProposals();
});

watch(
  () => households.selectedId,
  () => {
    void loadItems();
    void loadCategories();
    void loadProposals();
  },
);
</script>

<style scoped>
.quantity-control {
  min-width: 150px;
}

.quantity-value {
  min-width: 76px;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 599px) {
  .quantity-control {
    min-width: 138px;
  }

  .quantity-control :deep(.q-btn) {
    min-width: 42px;
    min-height: 42px;
  }
}
</style>
