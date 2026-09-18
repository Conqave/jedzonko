<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Przepisy</div>

    <q-banner v-if="households.selectedId === null" class="bg-grey-3 q-mb-md">
      Wybierz gospodarstwo domowe, aby zobaczyć propozycje przepisów.
    </q-banner>

    <q-tabs v-model="tab" align="left" class="q-mb-md">
      <q-tab name="suggestions" label="Propozycje z zapasów" no-caps />
      <q-tab name="all" label="Wszystkie przepisy" no-caps />
    </q-tabs>

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="suggestions" class="q-pa-none">
        <q-inner-loading :showing="loadingSuggestions" />
        <q-banner v-if="!loadingSuggestions && suggestions.length === 0" class="bg-grey-3">
          Brak propozycji dla bieżących zapasów.
        </q-banner>
        <q-list v-else bordered separator>
          <q-expansion-item
            v-for="suggestion in suggestions"
            :key="suggestion.recipe_id"
            :label="suggestion.recipe_name"
            :caption="`dostępne: ${suggestion.available_item_count} · brakuje: ${suggestion.missing_item_count}`"
          >
            <q-list separator>
              <q-item v-for="item in suggestion.missing_items" :key="item.ingredient_id">
                <q-item-section>{{ item.ingredient_name }}</q-item-section>
                <q-item-section side>{{ item.amount }} {{ item.unit_code }}</q-item-section>
              </q-item>
            </q-list>
            <q-card-actions align="right">
              <q-btn
                flat
                no-caps
                color="primary"
                label="Otwórz przepis"
                :to="{ name: 'recipe-detail', params: { id: suggestion.recipe_id } }"
              />
              <q-btn
                no-caps
                color="primary"
                label="Dodaj brakujące do listy zakupów"
                :loading="addingRecipeId === suggestion.recipe_id"
                @click="addMissingToShoppingList(suggestion.recipe_id)"
              />
            </q-card-actions>
          </q-expansion-item>
        </q-list>
      </q-tab-panel>

      <q-tab-panel name="all" class="q-pa-none">
        <q-banner v-if="!loadingRecipes && recipes.length === 0" class="bg-grey-3">
          Brak przepisów.
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
                <img v-if="recipe.image_url" :src="recipe.image_url" :alt="recipe.name" />
                <q-icon v-else name="restaurant" />
              </q-avatar>
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ recipe.name }}</q-item-label>
              <q-item-label caption>
                {{ recipe.servings }} porcji ·
                {{ recipe.preparation_time_minutes + recipe.cooking_time_minutes }} min ·
                {{ recipe.difficulty }}
              </q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { fetchRecipe, fetchRecipes, fetchSuggestions } from '@/features/recipes/api';
import { describeRecipeError } from '@/features/recipes/errors';
import type { RecipeSuggestion, RecipeSummary } from '@/features/recipes/models';
import { addRecipeItems, fetchShoppingLists } from '@/features/shopping/api';
import { describeShoppingError } from '@/features/shopping/errors';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const households = useHouseholdStore();

const tab = ref<'suggestions' | 'all'>('suggestions');
const suggestions = ref<RecipeSuggestion[]>([]);
const recipes = ref<RecipeSummary[]>([]);
const loadingSuggestions = ref(false);
const loadingRecipes = ref(false);
const addingRecipeId = ref<number | null>(null);

async function loadSuggestions(): Promise<void> {
  if (households.selectedId === null) {
    suggestions.value = [];
    return;
  }
  loadingSuggestions.value = true;
  try {
    suggestions.value = await fetchSuggestions(households.selectedId);
  } catch (error) {
    suggestions.value = [];
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    loadingSuggestions.value = false;
  }
}

async function loadRecipes(): Promise<void> {
  loadingRecipes.value = true;
  try {
    recipes.value = await fetchRecipes();
  } catch (error) {
    recipes.value = [];
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    loadingRecipes.value = false;
  }
}

async function addMissingToShoppingList(recipeId: number): Promise<void> {
  if (households.selectedId === null) {
    return;
  }
  addingRecipeId.value = recipeId;
  try {
    const lists = await fetchShoppingLists(households.selectedId);
    const target = lists.find((list) => list.is_primary) ?? lists[0];
    if (target === undefined) {
      quasar.notify({
        type: 'warning',
        message: 'Gospodarstwo domowe nie ma jeszcze listy zakupów.',
      });
      return;
    }
    const recipe = await fetchRecipe(recipeId);
    const items = await addRecipeItems(target.id, recipeId, recipe.servings);
    quasar.notify({
      type: 'positive',
      message: `Dodano ${items.length} pozycji do listy ${target.name}.`,
    });
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeShoppingError(error) });
  } finally {
    addingRecipeId.value = null;
  }
}

onMounted(() => {
  void loadSuggestions();
  void loadRecipes();
});

watch(
  () => households.selectedId,
  () => {
    void loadSuggestions();
  },
);
</script>
