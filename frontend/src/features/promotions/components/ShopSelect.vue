<template>
  <q-select
    :model-value="modelValue"
    dense
    outlined
    multiple
    use-chips
    use-input
    emit-value
    map-options
    input-debounce="0"
    :label="label"
    option-label="name"
    option-value="slug"
    :options="filteredShops"
    :loading="busy"
    :hint="hint"
    @filter="filterShops"
    @update:model-value="(value: string[] | null) => emit('update:modelValue', value ?? [])"
  >
    <template #no-option>
      <q-item>
        <q-item-section class="text-grey">Brak pasujących sklepów.</q-item-section>
      </q-item>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { PromotionShop } from '../model';

const props = withDefaults(
  defineProps<{
    modelValue: string[];
    shops: PromotionShop[];
    label: string;
    busy?: boolean;
    hint?: string;
  }>(),
  { busy: false, hint: '' },
);

const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>();

const filteredShops = ref<PromotionShop[]>([]);

function filterShops(value: string, update: (callback: () => void) => void): void {
  const needle = value.toLowerCase();
  update(() => {
    filteredShops.value = props.shops.filter((shop) => shop.name.toLowerCase().includes(needle));
  });
}
</script>
