<template>
  <q-select
    :model-value="modelValue"
    dense
    outlined
    use-input
    input-debounce="300"
    label="Produkt"
    option-label="name"
    :options="options"
    :loading="searching"
    :rules="rules"
    @filter="filterProducts"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <template #no-option>
      <q-item clickable @click="openCreateDialog">
        <q-item-section avatar>
          <q-icon name="add" />
        </q-item-section>
        <q-item-section>Dodaj produkt „{{ search }}”</q-item-section>
      </q-item>
    </template>
    <template #after-options>
      <q-item clickable @click="openCreateDialog">
        <q-item-section avatar>
          <q-icon name="add" />
        </q-item-section>
        <q-item-section>Dodaj nowy produkt</q-item-section>
      </q-item>
    </template>
  </q-select>

  <q-dialog v-model="createDialogOpen">
    <q-card style="min-width: 320px">
      <q-card-section class="text-h6">Nowy produkt</q-card-section>
      <q-form @submit.prevent="submitProduct">
        <q-card-section class="q-gutter-sm">
          <q-input
            v-model="newName"
            autofocus
            dense
            outlined
            label="Nazwa"
            :rules="[(value) => !!value || 'Podaj nazwę']"
          />
          <q-select
            v-model="newUnitCode"
            dense
            outlined
            emit-value
            map-options
            option-value="code"
            option-label="name"
            label="Domyślna jednostka"
            :options="units"
            :rules="[(value) => !!value || 'Wybierz jednostkę']"
          />
          <q-toggle v-model="newIsFood" label="Produkt spożywczy" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Anuluj" no-caps />
          <q-btn type="submit" color="primary" label="Dodaj" no-caps :loading="creating" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar, type ValidationRule } from 'quasar';
import { createProduct, searchProducts } from './api';
import { describeProductError } from './errors';
import type { MeasurementUnit, Product } from './models';

defineOptions({ inheritAttrs: false });

const props = defineProps<{
  modelValue: Product | null;
  householdId: number;
  units: MeasurementUnit[];
  rules?: ValidationRule[];
}>();

const emit = defineEmits<{ 'update:modelValue': [Product | null] }>();

const quasar = useQuasar();

const options = ref<Product[]>([]);
const searching = ref(false);
const search = ref('');
const createDialogOpen = ref(false);
const creating = ref(false);
const newName = ref('');
const newUnitCode = ref('');
const newIsFood = ref(true);

function notifyError(error: unknown): void {
  quasar.notify({ type: 'negative', message: describeProductError(error) });
}

function filterProducts(value: string, update: (callback: () => void) => void): void {
  search.value = value;
  searching.value = true;
  void searchProducts(props.householdId, value)
    .then((found) => {
      update(() => {
        options.value = found;
      });
    })
    .catch((error: unknown) => {
      update(() => {
        options.value = [];
      });
      notifyError(error);
    })
    .finally(() => {
      searching.value = false;
    });
}

function openCreateDialog(): void {
  newName.value = search.value;
  newUnitCode.value = '';
  newIsFood.value = true;
  createDialogOpen.value = true;
}

async function submitProduct(): Promise<void> {
  creating.value = true;
  try {
    const product = await createProduct({
      household_id: props.householdId,
      name: newName.value.trim(),
      default_unit_code: newUnitCode.value,
      is_food: newIsFood.value,
    });
    options.value = [product, ...options.value];
    emit('update:modelValue', product);
    createDialogOpen.value = false;
  } catch (error) {
    notifyError(error);
  } finally {
    creating.value = false;
  }
}
</script>
