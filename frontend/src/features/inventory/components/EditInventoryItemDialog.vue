<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 340px">
      <q-card-section class="text-h6">Edytuj pozycję</q-card-section>
      <q-form @submit="submit">
        <q-card-section class="q-gutter-sm">
          <q-input
            v-model="productName"
            dense
            outlined
            label="Nazwa produktu"
            :rules="[(value: string) => value.trim() !== '' || 'Podaj nazwę']"
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
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
          <q-btn type="submit" color="primary" no-caps label="Zapisz" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import type { MeasurementUnit } from '@/features/catalog/model';
import { formatQuantity } from '@/shared/formatQuantity';
import { isPositiveDecimal, toDecimalText } from '@/shared/decimal';
import type { InventoryItem, InventoryItemChanges } from '../model';

const props = defineProps<{ item: InventoryItem; units: MeasurementUnit[] }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const productName = ref(props.item.productName);
const quantity = ref(formatQuantity(props.item.quantity));
const unitCode = ref(props.item.unitCode);

function isQuantity(value: string): boolean {
  return value.trim() === '0' || isPositiveDecimal(value);
}

function submit(): void {
  const changes: InventoryItemChanges = {
    productName: productName.value.trim(),
    quantity: toDecimalText(quantity.value),
    unitCode: unitCode.value,
  };
  onDialogOK(changes);
}
</script>
