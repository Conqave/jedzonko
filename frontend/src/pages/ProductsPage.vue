<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Produkty</div>
    <q-banner v-if="households.selectedId === null" class="bg-grey-3">
      Wybierz gospodarstwo domowe, aby zobaczyć jego produkty.
    </q-banner>
    <template v-else>
      <q-input
        v-model="search"
        dense
        outlined
        clearable
        debounce="300"
        label="Szukaj produktu"
        class="q-mb-md"
      >
        <template #prepend><q-icon name="search" /></template>
      </q-input>
      <q-linear-progress v-if="busy" indeterminate class="q-mb-sm" />
      <ProductListingList
        :listings="listings"
        :find-unit-name="findUnitName"
        @edit="edit"
        @remove="confirmRemove"
      />
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { toRef } from 'vue';
import ProductEditDialog from '@/features/catalog/components/ProductEditDialog.vue';
import ProductListingList from '@/features/catalog/components/ProductListingList.vue';
import type { Product, ProductChanges } from '@/features/catalog/model';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useProductCatalog } from '@/features/catalog/useProductCatalog';
import { useHouseholdStore } from '@/features/households/store';
import { useDialogs } from '@/shared/useDialogs';

const quasar = useQuasar();
const dialogs = useDialogs();
const households = useHouseholdStore();
const selectedId = toRef(households, 'selectedId');
const { listings, search, busy, load, update, remove } = useProductCatalog(selectedId);
const { units, findUnitName } = useMeasurementUnits();

function edit(product: Product): void {
  const componentProps = { product, units: units.value };
  quasar
    .dialog({ component: ProductEditDialog, componentProps })
    .onOk((changes: ProductChanges) => {
      void saveAndReload(product.id, changes);
    })
    .onCancel(() => {
      void load();
    });
}

async function saveAndReload(productId: number, changes: ProductChanges): Promise<void> {
  await update(productId, changes);
  await load();
}

async function confirmRemove(product: Product): Promise<void> {
  const message = `„${product.name}” zniknie z produktów, zapasów i list zakupów.`;
  const isConfirmed = await dialogs.confirm('Usunąć produkt?', message);
  if (isConfirmed) {
    await remove(product.id);
  }
}
</script>
