<template>
  <q-select
    ref="selectRef"
    :model-value="modelValue"
    dense
    outlined
    use-input
    hide-selected
    fill-input
    input-debounce="300"
    :label="label"
    option-label="name"
    option-value="id"
    :options="products"
    :loading="busy"
    :rules="rules"
    @filter="filterProducts"
    @update:model-value="choose"
  >
    <template #no-option>
      <q-item clickable @click="openCreateDialog">
        <q-item-section avatar><q-icon name="add" /></q-item-section>
        <q-item-section>Dodaj produkt „{{ term }}”</q-item-section>
      </q-item>
    </template>
    <template #after-options>
      <q-item clickable @click="openCreateDialog">
        <q-item-section avatar><q-icon name="add" /></q-item-section>
        <q-item-section>Dodaj nowy produkt</q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { QSelect, useQuasar, type ValidationRule } from 'quasar';
import { ref } from 'vue';
import type { MeasurementUnit, Product } from '../model';
import { useProductSearch } from '../useProductSearch';
import ProductCreateDialog from './ProductCreateDialog.vue';

const props = withDefaults(
  defineProps<{
    modelValue: Product | null;
    householdId: number;
    units: MeasurementUnit[];
    label?: string;
    rules?: ValidationRule[];
  }>(),
  { label: 'Produkt', rules: () => [] },
);

const emit = defineEmits<{ 'update:modelValue': [value: Product | null] }>();

const quasar = useQuasar();
const { products, busy, search } = useProductSearch();
const term = ref('');
const selectRef = ref<QSelect | null>(null);

function choose(product: Product | null): void {
  emit('update:modelValue', product);
  selectRef.value?.hidePopup();
}

function filterProducts(value: string, update: (callback: () => void) => void): void {
  term.value = value;
  void search(props.householdId, value).then(() => {
    update(() => undefined);
  });
}

function openCreateDialog(): void {
  const componentProps = {
    householdId: props.householdId,
    units: props.units,
    initialName: term.value,
  };
  selectRef.value?.hidePopup();
  quasar.dialog({ component: ProductCreateDialog, componentProps }).onOk((product: Product) => {
    choose(product);
  });
}
</script>
