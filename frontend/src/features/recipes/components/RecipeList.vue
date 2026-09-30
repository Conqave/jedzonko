<template>
  <q-banner v-if="recipes.length === 0" class="bg-grey-3">
    {{ isFiltered ? NO_MATCHES_LABEL : 'Brak przepisów.' }}
  </q-banner>
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
          Porcje: {{ recipe.servings }} · {{ totalTimeMinutes(recipe) }} min ·
          {{ DIFFICULTY_LABELS[recipe.difficulty] }} · autor:
          {{ recipe.authorUsername ?? 'nieznany' }}
        </q-item-label>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { NO_MATCHES_LABEL } from '@/shared/listView';
import { DIFFICULTY_LABELS, totalTimeMinutes, type RecipeSummary } from '../model';

defineProps<{ recipes: RecipeSummary[]; isFiltered: boolean }>();
</script>
