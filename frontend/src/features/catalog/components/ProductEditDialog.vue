<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 380px">
      <q-card-section class="text-h6">Edytuj produkt</q-card-section>
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
          <PackageFields
            v-model="productPackage"
            :units="units"
            :default-unit-code="product.defaultUnitCode"
          />
        </q-card-section>
        <q-separator />
        <ProductIngredientSection :product="product" class="q-py-sm" />
        <q-separator />
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
import { toDecimalText } from '@/shared/decimal';
import type { MeasurementUnit, Product, ProductChanges, ProductPackage } from '../model';
import PackageFields from './PackageFields.vue';
import ProductIngredientSection from './ProductIngredientSection.vue';

const props = defineProps<{ product: Product; units: MeasurementUnit[] }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const name = ref(props.product.name);
const productPackage = ref<ProductPackage | null>(props.product.package);

function submit(): void {
  const packageValue = productPackage.value;
  const changes: ProductChanges = {
    name: name.value.trim(),
    package:
      packageValue === null
        ? null
        : { ...packageValue, quantity: toDecimalText(packageValue.quantity) },
  };
  onDialogOK(changes);
}
</script>
