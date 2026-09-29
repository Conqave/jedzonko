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

    <q-banner v-if="households.selectedId === null" class="bg-grey-3">
      Wybierz gospodarstwo domowe, aby zobaczyć zapasy.
    </q-banner>
    <template v-else>
      <LowStockBanner :items="belowMinimumItems" />
      <InventoryTable
        :items="items"
        :categories="categories"
        :busy="busy"
        :saving-item-id="savingItemId"
        :find-unit-name="findUnitName"
        @step="stepItem"
        @set-category="(item, categoryId) => setCategory(item.id, categoryId)"
        @edit="openEditDialog"
        @photo="openPhotoDialog"
        @remove="confirmRemove"
      />
      <q-expansion-item class="q-mt-lg" icon="label" label="Kategorie zapasów">
        <InventoryCategoryList
          :categories="categories"
          @rename="renameCategoryNamed"
          @remove="confirmRemoveCategory"
        />
      </q-expansion-item>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { toRef } from 'vue';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useHouseholdStore } from '@/features/households/store';
import AddInventoryItemDialog from '@/features/inventory/components/AddInventoryItemDialog.vue';
import EditInventoryItemDialog from '@/features/inventory/components/EditInventoryItemDialog.vue';
import InventoryCategoryList from '@/features/inventory/components/InventoryCategoryList.vue';
import InventoryPhotoDialog from '@/features/inventory/components/InventoryPhotoDialog.vue';
import InventoryTable from '@/features/inventory/components/InventoryTable.vue';
import LowStockBanner from '@/features/inventory/components/LowStockBanner.vue';
import {
  stepQuantity,
  type InventoryCategory,
  type InventoryItem,
  type InventoryItemEdit,
  type NewInventoryEntry,
  type QuantityDirection,
} from '@/features/inventory/model';
import { useInventory } from '@/features/inventory/useInventory';
import { useDialogs } from '@/shared/useDialogs';

const quasar = useQuasar();
const households = useHouseholdStore();
const selectedId = toRef(households, 'selectedId');
const dialogs = useDialogs();
const { units, findUnitName } = useMeasurementUnits();
const {
  items,
  categories,
  belowMinimumItems,
  busy,
  savingItemId,
  add,
  update,
  edit,
  remove,
  renameCategory,
  removeCategory,
  setCategory,
  createCategory,
  setPhoto,
  removePhoto,
} = useInventory(selectedId);

function openAddDialog(): void {
  const householdId = households.selectedId;
  if (householdId === null) {
    return;
  }
  const componentProps = {
    householdId,
    units: units.value,
    categories: categories.value,
    createCategory,
  };
  quasar
    .dialog({ component: AddInventoryItemDialog, componentProps })
    .onOk((entry: NewInventoryEntry) => {
      void add(entry);
    });
}

function openEditDialog(item: InventoryItem): void {
  const componentProps = { item, units: units.value };
  quasar
    .dialog({ component: EditInventoryItemDialog, componentProps })
    .onOk((itemEdit: InventoryItemEdit) => {
      void edit(item, itemEdit);
    });
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
  const quantity = stepQuantity(item.quantity, unit.dimension, direction);
  await update(item.id, { quantity });
}

async function renameCategoryNamed(category: InventoryCategory): Promise<void> {
  const prompt = { title: 'Zmień nazwę kategorii', label: 'Nazwa', initial: category.name };
  const name = await dialogs.promptText(prompt);
  if (name !== null) {
    await renameCategory(category.id, name);
  }
}

async function confirmRemoveCategory(category: InventoryCategory): Promise<void> {
  const message = `Pozycje z kategorii „${category.name}” zostaną bez kategorii.`;
  const isConfirmed = await dialogs.confirm('Usunąć kategorię?', message);
  if (isConfirmed) {
    await removeCategory(category.id);
  }
}

async function confirmRemove(item: InventoryItem): Promise<void> {
  const message = `Czy usunąć „${item.productName}” z zapasów?`;
  const isConfirmed = await dialogs.confirm('Usunąć z zapasów?', message);
  if (isConfirmed) {
    await remove(item.id);
  }
}
</script>
