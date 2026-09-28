<template>
  <q-form v-if="!isAdvanced" class="row no-wrap q-gutter-sm q-mb-md" @submit="submitText">
    <q-input
      v-model="text"
      class="col"
      dense
      outlined
      label="Dodaj pozycję"
      placeholder="np. mleko"
    />
    <q-btn type="submit" color="primary" icon="add" aria-label="Dodaj pozycję" :loading="busy" />
    <q-btn flat dense no-caps label="Więcej opcji" @click="isAdvanced = true" />
  </q-form>

  <q-form v-else class="row q-col-gutter-sm q-mb-md" @submit="submitAdvanced">
    <div class="col-12">
      <q-btn
        flat
        dense
        no-caps
        icon="arrow_back"
        label="Proste dodawanie"
        @click="isAdvanced = false"
      />
    </div>
    <div class="col-12 col-sm-3">
      <q-select
        v-model="kind"
        dense
        outlined
        emit-value
        map-options
        label="Rodzaj pozycji"
        :options="KIND_OPTIONS"
      />
    </div>
    <div class="col-12 col-sm-4">
      <ProductPicker
        v-if="kind === 'product'"
        v-model="product"
        :household-id="householdId"
        :units="units"
        :rules="[(value: Product | null) => value !== null || 'Wybierz produkt']"
      />
      <IngredientPicker v-else-if="kind === 'ingredient'" v-model="ingredient" />
      <q-input
        v-else
        v-model="text"
        dense
        outlined
        label="Pozycja"
        :rules="[(value: string) => value.trim() !== '' || 'Podaj nazwę']"
      />
    </div>
    <div class="col-6 col-sm-2">
      <q-input
        v-model="quantity"
        dense
        outlined
        inputmode="decimal"
        label="Ilość"
        :rules="[(value: string) => isPositiveDecimal(value) || 'Podaj dodatnią liczbę']"
      />
    </div>
    <div class="col-6 col-sm-2">
      <q-select
        v-model="unitCode"
        dense
        outlined
        clearable
        emit-value
        map-options
        option-value="code"
        option-label="name"
        label="Jednostka"
        :options="units"
      />
    </div>
    <div class="col-12 col-sm-1">
      <q-btn type="submit" color="primary" icon="add" aria-label="Dodaj pozycję" :loading="busy" />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import IngredientPicker from '@/features/catalog/components/IngredientPicker.vue';
import ProductPicker from '@/features/catalog/components/ProductPicker.vue';
import type { Ingredient, MeasurementUnit, Product } from '@/features/catalog/model';
import { isPositiveDecimal, toDecimalText } from '@/shared/decimal';
import type { NewShoppingItem, ShoppingSubject } from '../model';

type SubjectKind = ShoppingSubject['kind'];

const KIND_OPTIONS: { label: string; value: SubjectKind }[] = [
  { label: 'Produkt', value: 'product' },
  { label: 'Składnik', value: 'ingredient' },
  { label: 'Tekst własny', value: 'text' },
];

const DEFAULT_QUANTITY = '1';

const props = defineProps<{
  householdId: number;
  units: MeasurementUnit[];
  busy: boolean;
  addItem: (item: NewShoppingItem) => Promise<boolean>;
}>();

const isAdvanced = ref(false);
const kind = ref<SubjectKind>('product');
const product = ref<Product | null>(null);
const ingredient = ref<Ingredient | null>(null);
const text = ref('');
const quantity = ref(DEFAULT_QUANTITY);
const unitCode = ref<string | null>(null);

function clear(): void {
  product.value = null;
  ingredient.value = null;
  text.value = '';
  quantity.value = DEFAULT_QUANTITY;
  unitCode.value = null;
}

function findSubject(): ShoppingSubject | null {
  if (kind.value === 'product') {
    return product.value === null ? null : { kind: 'product', productId: product.value.id };
  }
  if (kind.value === 'ingredient') {
    return ingredient.value === null
      ? null
      : { kind: 'ingredient', ingredientId: ingredient.value.id };
  }
  const trimmed = text.value.trim();
  return trimmed === '' ? null : { kind: 'text', text: trimmed };
}

async function submitText(): Promise<void> {
  const trimmed = text.value.trim();
  if (trimmed === '') {
    return;
  }
  const item: NewShoppingItem = {
    subject: { kind: 'text', text: trimmed },
    quantity: DEFAULT_QUANTITY,
    unitCode: null,
  };
  const isAdded = await props.addItem(item);
  if (isAdded) {
    clear();
  }
}

async function submitAdvanced(): Promise<void> {
  const subject = findSubject();
  if (subject === null) {
    return;
  }
  const item: NewShoppingItem = {
    subject,
    quantity: toDecimalText(quantity.value),
    unitCode: unitCode.value,
  };
  const isAdded = await props.addItem(item);
  if (isAdded) {
    clear();
  }
}
</script>
