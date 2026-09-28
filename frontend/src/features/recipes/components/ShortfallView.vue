<template>
  <q-banner v-if="shortfall.isReady" dense class="bg-green-2 q-mb-sm">
    Masz w domu wszystkie składniki.
  </q-banner>
  <q-banner v-if="shortfall.unmeasuredIngredients.length > 0" dense class="bg-orange-2 q-mb-sm">
    Nie da się porównać ilości dla: {{ shortfall.unmeasuredIngredients.join(', ') }}
  </q-banner>
  <q-list v-if="shortfall.missingItems.length > 0" bordered separator>
    <q-item v-for="item in shortfall.missingItems" :key="item.name">
      <q-item-section>{{ item.name }}</q-item-section>
      <q-item-section side>{{ describeAmount(item) }}</q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { formatQuantity } from '@/shared/formatQuantity';
import type { MissingRecipeItem, RecipeShortfall } from '../model';

const props = defineProps<{ shortfall: RecipeShortfall; findUnitName: (code: string) => string }>();

function describeAmount(item: MissingRecipeItem): string {
  if (item.amount === null || item.unitCode === null) {
    return 'do kupienia';
  }
  const amount = formatQuantity(item.amount);
  const unit = props.findUnitName(item.unitCode);
  return `${amount} ${unit}`;
}
</script>
