<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 340px">
      <q-card-section class="text-h6">Nowy produkt</q-card-section>
      <q-form @submit="submit">
        <q-card-section class="q-gutter-sm">
          <q-input
            v-model="name"
            autofocus
            dense
            outlined
            label="Nazwa"
            :rules="[(value: string) => value.trim() !== '' || 'Podaj nazwę']"
          />
          <q-select
            v-model="defaultUnitCode"
            dense
            outlined
            emit-value
            map-options
            option-value="code"
            option-label="name"
            label="Domyślna jednostka"
            :options="units"
            :rules="[(value: string) => value !== '' || 'Wybierz jednostkę']"
          />
          <q-toggle v-model="isFood" label="Produkt spożywczy" />
          <PackageFields
            v-model="productPackage"
            :units="units"
            :default-unit-code="defaultUnitCode"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
          <q-btn type="submit" color="primary" no-caps label="Dodaj" :loading="busy" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import { toDecimalText } from '@/shared/decimal';
import type { MeasurementUnit, ProductPackage } from '../model';
import { useProductCreation } from '../useProductCreation';
import PackageFields from './PackageFields.vue';

const props = defineProps<{ householdId: number; units: MeasurementUnit[]; initialName: string }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const { busy, create } = useProductCreation();
const name = ref(props.initialName);
const defaultUnitCode = ref('');
const isFood = ref(true);
const productPackage = ref<ProductPackage | null>(null);

async function submit(): Promise<void> {
  const packageValue = productPackage.value;
  const product = await create({
    householdId: props.householdId,
    name: name.value.trim(),
    defaultUnitCode: defaultUnitCode.value,
    isFood: isFood.value,
    package:
      packageValue === null
        ? null
        : { ...packageValue, quantity: toDecimalText(packageValue.quantity) },
  });
  if (product !== null) {
    onDialogOK(product);
  }
}
</script>
