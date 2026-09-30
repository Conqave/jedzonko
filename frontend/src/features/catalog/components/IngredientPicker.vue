<template>
  <q-select
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
    :options="ingredients"
    :loading="busy"
    @filter="filterIngredients"
    @update:model-value="(value: Ingredient | null) => emit('update:modelValue', value)"
  >
    <template #no-option>
      <q-item>
        <q-item-section class="text-grey">Wpisz nazwę składnika</q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import type { Ingredient } from '../model';
import { useIngredientSearch } from '../useIngredientSearch';

withDefaults(defineProps<{ modelValue: Ingredient | null; label?: string }>(), {
  label: 'Składnik',
});

const emit = defineEmits<{ 'update:modelValue': [value: Ingredient | null] }>();

const { ingredients, busy, search } = useIngredientSearch();

function filterIngredients(value: string, update: (callback: () => void) => void): void {
  void search(value).then(() => {
    update(() => undefined);
  });
}
</script>
