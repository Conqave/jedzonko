<template>
  <div class="row q-col-gutter-sm items-start">
    <div class="col-12">
      <q-toggle
        :model-value="modelValue !== null"
        label="Sprzedawany w opakowaniu"
        @update:model-value="togglePackage"
      />
    </div>
    <template v-if="modelValue !== null">
      <div class="col-6">
        <q-input
          :model-value="modelValue.quantity"
          dense
          outlined
          inputmode="decimal"
          label="Zawartość opakowania"
          :rules="[(value: string) => isPositiveDecimal(value) || 'Podaj dodatnią liczbę']"
          @update:model-value="(value) => updateQuantity(String(value ?? ''))"
        />
      </div>
      <div class="col-6">
        <q-select
          :model-value="modelValue.unitCode"
          dense
          outlined
          emit-value
          map-options
          option-value="code"
          option-label="name"
          label="Jednostka"
          :options="units"
          @update:model-value="updateUnit"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { isPositiveDecimal } from '@/shared/decimal';
import type { MeasurementUnit, ProductPackage } from '../model';

const props = defineProps<{
  modelValue: ProductPackage | null;
  units: MeasurementUnit[];
  defaultUnitCode: string;
}>();

const emit = defineEmits<{ 'update:modelValue': [value: ProductPackage | null] }>();

function togglePackage(isPackaged: boolean): void {
  emit('update:modelValue', isPackaged ? { quantity: '', unitCode: props.defaultUnitCode } : null);
}

function updateQuantity(quantity: string): void {
  if (props.modelValue !== null) {
    emit('update:modelValue', { ...props.modelValue, quantity });
  }
}

function updateUnit(unitCode: string): void {
  if (props.modelValue !== null) {
    emit('update:modelValue', { ...props.modelValue, unitCode });
  }
}
</script>
