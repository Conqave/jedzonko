<template>
  <q-banner v-if="suggestions.length === 0" class="bg-grey-3">
    Brak propozycji dla bieżących zapasów.
  </q-banner>
  <q-list v-else bordered separator>
    <q-expansion-item v-for="entry in suggestions" :key="entry.suggestion.recipeId">
      <template #header>
        <q-item-section>
          <q-item-label>{{ entry.suggestion.recipeName }}</q-item-label>
          <q-item-label caption>
            Składniki w domu: {{ entry.suggestion.shortfall.availableItemCount }} z
            {{ entry.suggestion.shortfall.requiredItemCount }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-badge v-if="entry.suggestion.shortfall.isReady" color="positive"
            >Ugotujesz teraz</q-badge
          >
        </q-item-section>
      </template>
      <div class="q-pa-sm">
        <ShortfallView :shortfall="entry.suggestion.shortfall" :find-unit-name="findUnitName" />
        <div class="row justify-end items-center q-gutter-sm q-mt-sm">
          <q-btn
            flat
            no-caps
            color="primary"
            label="Otwórz przepis"
            :to="{ name: 'recipe-detail', params: { id: entry.suggestion.recipeId } }"
          />
          <RecipeShoppingButton
            v-if="entry.suggestion.shortfall.missingItems.length > 0"
            :household-id="householdId"
            :source="{
              kind: 'recipe',
              recipeId: entry.suggestion.recipeId,
              servings: entry.servings,
            }"
          />
        </div>
      </div>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import RecipeShoppingButton from '@/features/shopping/components/RecipeShoppingButton.vue';
import type { CookableSuggestion } from '../model';
import ShortfallView from './ShortfallView.vue';

defineProps<{
  suggestions: CookableSuggestion[];
  householdId: number;
  findUnitName: (code: string) => string;
}>();
</script>
