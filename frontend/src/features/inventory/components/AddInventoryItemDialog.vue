<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 340px">
      <q-card-section class="text-h6">Dodaj do zapasów</q-card-section>
      <q-form @submit="submit">
        <q-card-section class="q-gutter-sm">
          <ProductPicker
            v-model="product"
            :household-id="householdId"
            :units="units"
            :rules="[(value: Product | null) => value !== null || 'Wybierz produkt']"
            @update:model-value="applyDefaultUnit"
          />
          <q-input
            v-model="quantity"
            dense
            outlined
            inputmode="decimal"
            label="Ilość"
            :rules="[(value: string) => isQuantity(value) || 'Podaj ilość']"
          />
          <q-select
            v-model="unitCode"
            dense
            outlined
            emit-value
            map-options
            option-value="code"
            option-label="name"
            label="Jednostka"
            :options="units"
            :rules="[(value: string) => value !== '' || 'Wybierz jednostkę']"
          />
          <q-select
            v-model="categoryId"
            dense
            outlined
            clearable
            emit-value
            map-options
            use-input
            new-value-mode="add-unique"
            option-value="id"
            option-label="name"
            :options="categoryOptions"
            label="Kategoria (opcjonalnie)"
            hint="Wpisz nazwę i naciśnij Enter, aby dodać nową kategorię."
            @new-value="addCategory"
          />
          <q-input
            v-model="minimumQuantity"
            dense
            outlined
            inputmode="decimal"
            label="Minimalna ilość (opcjonalnie)"
            :rules="[(value: string) => value.trim() === '' || isQuantity(value) || 'Podaj liczbę']"
          />
          <q-file
            v-model="photo"
            dense
            outlined
            clearable
            accept="image/jpeg,image/png,image/webp"
            label="Zdjęcie (opcjonalnie)"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
          <q-btn type="submit" color="primary" no-caps label="Dodaj" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import ProductPicker from '@/features/catalog/components/ProductPicker.vue';
import type { MeasurementUnit, Product } from '@/features/catalog/model';
import { isPositiveDecimal, toDecimalText } from '@/shared/decimal';
import type { InventoryCategory, NewInventoryEntry } from '../model';

const props = defineProps<{
  householdId: number;
  units: MeasurementUnit[];
  categories: InventoryCategory[];
  createCategory: (name: string) => Promise<InventoryCategory | null>;
}>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const product = ref<Product | null>(null);
const quantity = ref('');
const unitCode = ref('');
const categoryId = ref<number | null>(null);
const minimumQuantity = ref('');
const photo = ref<File | null>(null);
const categoryOptions = ref<InventoryCategory[]>([...props.categories]);

function isQuantity(value: string): boolean {
  return value.trim() === '0' || isPositiveDecimal(value);
}

function applyDefaultUnit(chosen: Product | null): void {
  if (chosen !== null) {
    unitCode.value = chosen.defaultUnitCode;
  }
}

async function addCategory(name: string, done: () => void): Promise<void> {
  const created = await props.createCategory(name.trim());
  done();
  if (created === null) {
    return;
  }
  categoryOptions.value = [...categoryOptions.value, created];
  categoryId.value = created.id;
}

function submit(): void {
  const chosen = product.value;
  if (chosen === null) {
    return;
  }
  const minimum = minimumQuantity.value.trim();
  const entry: NewInventoryEntry = {
    item: {
      householdId: props.householdId,
      productId: chosen.id,
      quantity: toDecimalText(quantity.value),
      unitCode: unitCode.value,
      minimumQuantity: minimum === '' ? null : toDecimalText(minimum),
      categoryId: categoryId.value,
    },
    photo: photo.value,
  };
  onDialogOK(entry);
}
</script>
