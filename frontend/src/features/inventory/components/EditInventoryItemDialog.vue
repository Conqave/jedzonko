<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 420px">
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
          <PackageFields
            v-model="productPackage"
            :units="units"
            :default-unit-code="product.defaultUnitCode"
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
          <q-input
            v-model="minimumQuantity"
            dense
            outlined
            clearable
            inputmode="decimal"
            label="Minimalny zapas"
            hint="Puste pole oznacza brak minimum"
            :rules="[(value: string | null) => isOptionalQuantity(value) || 'Podaj ilość']"
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
import PackageFields from '@/features/catalog/components/PackageFields.vue';
import ProductIngredientSection from '@/features/catalog/components/ProductIngredientSection.vue';
import type { MeasurementUnit, Product, ProductPackage } from '@/features/catalog/model';
import { formatQuantity } from '@/shared/formatQuantity';
import { isPositiveDecimal, toDecimalText } from '@/shared/decimal';
import type { InventoryItem, PantryItemEdit } from '../model';

const props = defineProps<{ item: InventoryItem; product: Product; units: MeasurementUnit[] }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const productName = ref(props.product.name);
const productPackage = ref<ProductPackage | null>(props.product.package);
const quantity = ref(formatQuantity(props.item.quantity));
const unitCode = ref(props.item.unitCode);
const initialMinimum = props.item.minimumQuantity;
const minimumQuantity = ref<string | null>(
  initialMinimum === null ? null : formatQuantity(initialMinimum),
);

function isQuantity(value: string): boolean {
  return value.trim() === '0' || isPositiveDecimal(value);
}

function isOptionalQuantity(value: string | null): boolean {
  return value === null || value.trim() === '' || isQuantity(value);
}

function readMinimum(): string | null {
  const entered = minimumQuantity.value;
  if (entered === null || entered.trim() === '') {
    return null;
  }
  const text = toDecimalText(entered);
  const isUnchanged = initialMinimum !== null && Number(text) === Number(initialMinimum);
  return isUnchanged ? initialMinimum : text;
}

function submit(): void {
  const packageValue = productPackage.value;
  const pantryEdit: PantryItemEdit = {
    product: {
      name: productName.value.trim(),
      package:
        packageValue === null
          ? null
          : { ...packageValue, quantity: toDecimalText(packageValue.quantity) },
    },
    item: {
      changes: {
        quantity: toDecimalText(quantity.value),
        unitCode: unitCode.value,
      },
      minimumQuantity: readMinimum(),
    },
  };
  onDialogOK(pantryEdit);
}
</script>
