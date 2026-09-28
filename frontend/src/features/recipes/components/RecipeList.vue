<template>
  <q-banner v-if="recipes.length === 0" class="bg-grey-3">Brak przepisów.</q-banner>
  <q-list v-else bordered separator>
    <q-item
      v-for="recipe in recipes"
      :key="recipe.id"
      clickable
      :to="{ name: 'recipe-detail', params: { id: recipe.id } }"
    >
      <q-item-section avatar>
        <q-avatar rounded>
          <img v-if="recipe.imageUrl !== null" :src="recipe.imageUrl" :alt="recipe.name" />
          <q-icon v-else name="restaurant" />
        </q-avatar>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ recipe.name }}</q-item-label>
        <q-item-label caption>
          Porcje: {{ recipe.servings }} ·
          {{ recipe.preparationTimeMinutes + recipe.cookingTimeMinutes }} min ·
          {{ DIFFICULTY_LABELS[recipe.difficulty] }} · autor: {{ recipe.authorUsername }}
        </q-item-label>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { DIFFICULTY_LABELS, type RecipeSummary } from '../model';

defineProps<{ recipes: RecipeSummary[] }>();
</script>
