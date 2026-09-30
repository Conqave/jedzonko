<template>
  <q-btn-toggle
    :model-value="choice"
    :options="options"
    :aria-label="label"
    dense
    no-caps
    unelevated
    color="grey-3"
    text-color="grey-9"
    toggle-color="primary"
    @update:model-value="select"
  />
</template>

<script setup lang="ts" generic="Choice extends string">
import { computed } from 'vue';

const choice = defineModel<Choice>({ required: true });

const props = defineProps<{
  choices: readonly Choice[];
  labels: Readonly<Record<Choice, string>>;
  label: string;
}>();

const options = computed(() =>
  props.choices.map((value) => ({ value, label: props.labels[value] })),
);

function select(value: unknown): void {
  const selected = props.choices.find((candidate) => candidate === value);
  if (selected === undefined) {
    throw new Error(`Unknown choice for ${props.label}.`);
  }
  choice.value = selected;
}
</script>
