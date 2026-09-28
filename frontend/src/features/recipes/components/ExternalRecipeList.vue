<template>
  <q-banner v-if="recipes.length === 0" class="bg-grey-3"
    >Brak przepisów dla tego zapytania.</q-banner
  >
  <q-list v-else bordered separator>
    <q-item
      v-for="recipe in recipes"
      :key="recipe.reference"
      clickable
      :to="{ name: 'external-recipe', params: { reference: recipe.reference } }"
    >
      <q-item-section avatar>
        <q-avatar rounded size="56px">
          <img v-if="recipe.imageUrl !== null" :src="recipe.imageUrl" :alt="recipe.name" />
          <q-icon v-else name="restaurant" />
        </q-avatar>
      </q-item-section>
      <q-item-section>
        <q-item-label>{{ recipe.name }}</q-item-label>
        <q-item-label caption lines="2">{{ recipe.description }}</q-item-label>
        <q-item-label caption>
          <q-badge color="deep-orange" :label="recipe.sourceName" />
          <span v-if="recipe.totalTimeMinutes !== null"> · {{ recipe.totalTimeMinutes }} min</span>
          <span v-if="recipe.yieldLabel !== ''"> · {{ recipe.yieldLabel }}</span>
        </q-item-label>
        <q-item-label v-if="recipe.matchedProductNames.length > 0" caption>
          Z Twoich zapasów:
          <q-chip
            v-for="product in recipe.matchedProductNames"
            :key="product"
            dense
            square
            color="positive"
            text-color="white"
          >
            {{ product }}
          </q-chip>
        </q-item-label>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import type { ExternalRecipeMatch } from '../model';

defineProps<{ recipes: ExternalRecipeMatch[] }>();
</script>
