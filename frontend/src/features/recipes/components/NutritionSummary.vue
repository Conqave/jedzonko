<template>
  <div>
    <div class="text-subtitle1">
      <q-icon name="local_fire_department" color="deep-orange" class="q-mr-xs" />{{
        describeNutrition(nutrition)
      }}
    </div>
    <q-expansion-item
      v-if="nutrition.uncountedIngredients.length > 0"
      dense
      dense-toggle
      switch-toggle-side
      header-class="text-caption text-grey-8 q-px-none"
      :label="`Nie wliczono: ${nutrition.uncountedIngredients.length}`"
    >
      <q-list dense>
        <q-item v-for="(line, index) in nutrition.uncountedIngredients" :key="index">
          <q-item-section>{{ line.name }}</q-item-section>
          <q-item-section side>{{ UNCOUNTED_REASON_LABELS[line.reason] }}</q-item-section>
        </q-item>
      </q-list>
    </q-expansion-item>
  </div>
</template>

<script setup lang="ts">
import { UNCOUNTED_REASON_LABELS, describeNutrition, type RecipeNutrition } from '../model';

defineProps<{ nutrition: RecipeNutrition }>();
</script>
