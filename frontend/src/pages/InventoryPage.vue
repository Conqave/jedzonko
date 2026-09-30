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

    <q-banner v-if="households.selectedId === null" class="bg-grey-3 q-mb-md">
      Nie masz jeszcze gospodarstwa domowego albo żadne nie jest wybrane. Utwórz dom, aby zacząć.
      <template #action>
        <q-btn flat no-caps color="primary" label="Utwórz dom" :to="{ name: 'households' }" />
      </template>
    </q-banner>
    <template v-else>
      <LowStockBanner :items="belowMinimumItems" />
      <ListFilterBar
        v-model:search="search"
        v-model:sort="sort"
        v-model:is-reversed="isReversed"
        search-label="Szukaj po produkcie lub tagu"
        :sorts="INVENTORY_SORTS"
        :sort-labels="INVENTORY_SORT_LABELS"
      >
        <ChoiceToggle
          v-model="tag"
          :choices="TAG_FILTERS"
          :labels="TAG_FILTER_LABELS"
          label="Tag"
        />
        <q-toggle v-model="isBelowMinimumOnly" dense label="Poniżej minimum" />
      </ListFilterBar>
      <InventoryTable
        :items="visibleItems"
        :is-filtered="isFiltered"
        :find-tags="findTags"
        :find-proposal-count="findProposalCount"
        :busy="busy"
        :saving-item-id="savingItemId"
        :describe-unit-quantity="describeUnitQuantity"
        @step="stepItem"
        @edit="openEditDialog"
        @photo="openPhotoDialog"
        @remove="confirmRemove"
      />
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { toRef } from 'vue';
import { TAG_FILTER_LABELS, TAG_FILTERS, type ProductListing } from '@/features/catalog/model';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useProductCatalog } from '@/features/catalog/useProductCatalog';
import { useHouseholdStore } from '@/features/households/store';
import AddInventoryItemDialog from '@/features/inventory/components/AddInventoryItemDialog.vue';
import EditInventoryItemDialog from '@/features/inventory/components/EditInventoryItemDialog.vue';
import InventoryPhotoDialog from '@/features/inventory/components/InventoryPhotoDialog.vue';
import InventoryTable from '@/features/inventory/components/InventoryTable.vue';
import LowStockBanner from '@/features/inventory/components/LowStockBanner.vue';
import {
  INVENTORY_SORT_LABELS,
  INVENTORY_SORTS,
  stepQuantity,
  type InventoryItem,
  type PantryItemEdit,
  type NewInventoryEntry,
  type QuantityDirection,
} from '@/features/inventory/model';
import { useInventory } from '@/features/inventory/useInventory';
import { useInventoryView } from '@/features/inventory/useInventoryView';
import ChoiceToggle from '@/shared/components/ChoiceToggle.vue';
import ListFilterBar from '@/shared/components/ListFilterBar.vue';
import { useDialogs } from '@/shared/useDialogs';

const quasar = useQuasar();
const households = useHouseholdStore();
const selectedId = toRef(households, 'selectedId');
const dialogs = useDialogs();
const { units, describeUnitQuantity } = useMeasurementUnits();
const {
  items,
  belowMinimumItems,
  busy,
  savingItemId,
  add,
  update,
  edit,
  remove,
  setPhoto,
  removePhoto,
  load: reloadItems,
} = useInventory(selectedId);
const { listings, load: loadProducts, update: updateProduct } = useProductCatalog(selectedId);

function openAddDialog(): void {
  const householdId = households.selectedId;
  if (householdId === null) {
    return;
  }
  const componentProps = {
    householdId,
    units: units.value,
  };
  quasar
    .dialog({ component: AddInventoryItemDialog, componentProps })
    .onOk((entry: NewInventoryEntry) => {
      void add(entry);
    });
}

function findListing(productId: number): ProductListing | undefined {
  return listings.value.find((listing) => listing.product.id === productId);
}

function findTags(productId: number): string[] {
  const listing = findListing(productId);
  if (listing === undefined) {
    return [];
  }
  return listing.tags.map((tag) => tag.name);
}

const { search, tag, isBelowMinimumOnly, sort, isReversed, visibleItems, isFiltered } =
  useInventoryView(items, findTags, units);

function findProposalCount(productId: number): number {
  const listing = findListing(productId);
  return listing === undefined ? 0 : listing.openProposalCount;
}

function openEditDialog(item: InventoryItem): void {
  const listing = findListing(item.productId);
  if (listing === undefined) {
    return;
  }
  const componentProps = { item, product: listing.product, units: units.value };
  quasar
    .dialog({ component: EditInventoryItemDialog, componentProps })
    .onOk((pantryEdit: PantryItemEdit) => {
      void savePantryItem(item, pantryEdit);
    })
    .onCancel(() => {
      void reloadCatalogAndItems();
    });
}

async function savePantryItem(item: InventoryItem, pantryEdit: PantryItemEdit): Promise<void> {
  const isProductSaved = await updateProduct(item.productId, pantryEdit.product);
  if (isProductSaved) {
    await edit(item, pantryEdit.item);
  }
  await reloadCatalogAndItems();
}

async function reloadCatalogAndItems(): Promise<void> {
  await loadProducts();
  await reloadItems();
}

function openPhotoDialog(item: InventoryItem): void {
  quasar
    .dialog({ component: InventoryPhotoDialog, componentProps: { item } })
    .onOk((photo: File | null) => {
      void (photo === null ? removePhoto(item.id) : setPhoto(item.id, photo));
    });
}

async function stepItem(item: InventoryItem, direction: QuantityDirection): Promise<void> {
  const unit = units.value.find((candidate) => candidate.code === item.unitCode);
  if (unit === undefined) {
    return;
  }
  const quantity = stepQuantity(item.quantity, unit, direction);
  await update(item.id, { quantity });
}

async function confirmRemove(item: InventoryItem): Promise<void> {
  const message = `Czy usunąć „${item.productName}” z zapasów?`;
  const isConfirmed = await dialogs.confirm('Usunąć z zapasów?', message);
  if (isConfirmed) {
    await remove(item.id);
  }
}
</script>
