<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5">Przepisy</div>
      <q-space />
      <q-btn no-caps color="primary" icon="add" label="Nowy przepis" :to="{ name: 'recipe-new' }" />
    </div>

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
        <q-toggle v-model="onlyReady" class="q-mb-sm" label="Tylko te, które mogę ugotować teraz" />
        <q-banner v-if="!loadingSuggestions && visibleSuggestions.length === 0" class="bg-grey-3">
          {{
            onlyReady
              ? 'Żadnego przepisu nie ugotujesz w całości z bieżących zapasów.'
              : 'Brak propozycji dla bieżących zapasów.'
          }}
        </q-banner>
        <q-list v-else bordered separator>
          <q-expansion-item v-for="suggestion in visibleSuggestions" :key="suggestion.recipe_id">
            <template #header>
              <q-item-section>
                <q-item-label>{{ suggestion.recipe_name }}</q-item-label>
                <q-item-label caption>
                  dostępne: {{ suggestion.available_item_count }} z
                  {{ suggestion.required_item_count }} · brakuje:
                  {{ suggestion.missing_item_count }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge v-if="suggestion.is_ready" color="positive">Ugotujesz teraz</q-badge>
              </q-item-section>
            </template>
            <q-banner v-if="suggestion.unmeasured_ingredients.length > 0" dense class="bg-orange-2">
              Nie da się porównać ilości dla:
              {{ suggestion.unmeasured_ingredients.join(', ') }}
            </q-banner>
            <q-list separator>
              <q-item v-for="item in suggestion.missing_items" :key="item.name">
                <q-item-section>{{ item.name }}</q-item-section>
                <q-item-section side
                  >{{ formatQuantity(item.amount) }} {{ item.unit_code }}</q-item-section
                >
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
                {{ recipe.difficulty }} · autor: {{ recipe.author_username }}
              </q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { formatQuantity } from '@/features/shared/formatQuantity';
import { computed, onMounted, ref, watch } from 'vue';
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
const onlyReady = ref(false);

const visibleSuggestions = computed<RecipeSuggestion[]>(() =>
  onlyReady.value ? suggestions.value.filter((item) => item.is_ready) : suggestions.value,
);

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
