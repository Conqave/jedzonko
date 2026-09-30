<template>
  <div class="q-mb-md">
    <div class="row no-wrap items-center q-gutter-x-sm">
      <q-input
        class="col"
        :model-value="search"
        dense
        outlined
        clearable
        debounce="250"
        :label="searchLabel"
        @update:model-value="setSearch"
      >
        <template #prepend><q-icon name="search" /></template>
      </q-input>
      <q-select
        class="list-sort"
        :model-value="sort"
        dense
        outlined
        emit-value
        map-options
        :options="sortOptions"
        label="Sortuj"
        @update:model-value="selectSort"
      />
      <q-btn
        flat
        dense
        round
        :color="isReversed ? 'primary' : 'grey-8'"
        :icon="isReversed ? 'arrow_upward' : 'arrow_downward'"
        aria-label="Odwróć kolejność"
        :aria-pressed="isReversed"
        @click="isReversed = !isReversed"
      >
        <q-tooltip>Odwróć kolejność</q-tooltip>
      </q-btn>
    </div>
    <div v-if="$slots.default" class="row items-center q-gutter-sm q-mt-xs">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts" generic="Sort extends string">
import { computed } from 'vue';

const search = defineModel<string>('search', { required: true });
const sort = defineModel<Sort>('sort', { required: true });
const isReversed = defineModel<boolean>('isReversed', { required: true });

const props = defineProps<{
  searchLabel: string;
  sorts: readonly Sort[];
  sortLabels: Readonly<Record<Sort, string>>;
}>();

const sortOptions = computed(() =>
  props.sorts.map((value) => ({ value, label: props.sortLabels[value] })),
);

function setSearch(value: string | number | null): void {
  search.value = value === null ? '' : String(value);
}

function selectSort(value: unknown): void {
  const selected = props.sorts.find((candidate) => candidate === value);
  if (selected === undefined) {
    throw new Error('Unknown sort option.');
  }
  sort.value = selected;
}
</script>

<style scoped>
.list-sort {
  width: 8.5rem;
}
</style>
