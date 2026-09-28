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
      <q-tab name="external" label="Ania Gotuje" no-caps />
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
                  {{ suggestion.is_ready ? 'Masz wszystkie składniki' : `Brakuje ${suggestion.missing_item_count} składników` }}
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

      <q-tab-panel name="external" class="q-pa-none">
        <q-form class="row q-col-gutter-sm items-start q-mb-md" @submit.prevent="searchExternal">
          <div class="col-12 col-sm-7">
            <q-input
              v-model="externalQuery"
              dense
              outlined
              clearable
              label="Szukaj przepisu w Ania Gotuje"
            />
          </div>
          <div class="col-auto">
            <q-btn
              type="submit"
              color="primary"
              label="Szukaj"
              no-caps
              :disable="households.selectedId === null"
              :loading="loadingExternal"
            />
          </div>
          <div class="col-auto">
            <q-btn
              outline
              color="primary"
              label="Z moich zapasów"
              no-caps
              :disable="households.selectedId === null"
              :loading="loadingExternal"
              @click="loadExternalSuggestions"
            />
          </div>
        </q-form>

        <q-banner v-if="externalIngredients.length > 0" class="bg-grey-3 q-mb-md pantry-search-banner">
          <div class="row items-center q-col-gutter-sm">
            <div class="col-auto text-weight-medium">Szukam po zapasach</div>
            <div class="col text-caption text-grey-8">
              {{ externalIngredients.length }} tagów · {{ externalInventoryCount }} produktów w domu
            </div>
            <div class="col-auto">
              <q-btn
                flat
                dense
                no-caps
                color="primary"
                :label="showExternalIngredients ? 'Ukryj tagi' : 'Pokaż tagi'"
                @click="showExternalIngredients = !showExternalIngredients"
              />
            </div>
          </div>
          <div class="row q-gutter-xs q-mt-xs">
          <q-chip
            v-for="ingredient in displayedExternalIngredients"
            :key="ingredient"
            dense
            square
            color="primary"
            text-color="white"
          >
            {{ ingredient }}
          </q-chip>
          <q-chip
            v-if="!showExternalIngredients && externalIngredients.length > ingredientPreviewLimit"
            dense
            outline
            color="primary"
          >
            +{{ externalIngredients.length - ingredientPreviewLimit }} więcej
          </q-chip>
          </div>
        </q-banner>

        <q-banner v-if="externalLoaded && externalRecipes.length === 0" class="bg-grey-3">
          Brak przepisów dla tego zapytania.
        </q-banner>

        <q-list v-else-if="externalRecipes.length > 0" bordered separator>
          <q-item
            v-for="recipe in externalRecipes"
            :key="recipe.reference"
            clickable
            :to="{ name: 'external-recipe', params: { reference: recipe.reference } }"
          >
            <q-item-section avatar>
              <q-avatar rounded size="56px">
                <img v-if="recipe.image_url !== null" :src="recipe.image_url" :alt="recipe.name" />
                <span v-else>🍽️</span>
              </q-avatar>
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ recipe.name }}</q-item-label>
              <q-item-label caption lines="2">{{ recipe.description }}</q-item-label>
              <q-item-label caption>
                <q-badge color="deep-orange" :label="recipe.source_name" />
                <span v-if="recipe.total_time_minutes !== null">
                  · {{ recipe.total_time_minutes }} min
                </span>
                <span v-if="recipe.yield_label"> · {{ recipe.yield_label }}</span>
              </q-item-label>
              <q-item-label v-if="recipe.matched_product_count > 0" caption>
                Wykorzystuje {{ recipe.matched_product_count }} z Twoich produktów:
                <q-chip
                  v-for="product in recipe.matched_product_names"
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

        <div v-if="externalTotalPages > 1" class="row justify-center q-mt-md">
          <q-pagination
            v-model="externalPageNumber"
            :max="externalTotalPages"
            :max-pages="7"
            boundary-numbers
            @update:model-value="reloadExternalPage"
          />
        </div>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { formatQuantity } from '@/features/shared/formatQuantity';
import { computed, onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import {
  fetchExternalSuggestions,
  fetchRecipe,
  fetchRecipes,
  fetchSuggestions,
  searchExternalRecipes,
} from '@/features/recipes/api';
import { describeRecipeError } from '@/features/recipes/errors';
import type {
  ExternalRecipeSummary,
  RecipeSuggestion,
  RecipeSummary,
} from '@/features/recipes/models';
import { addRecipeItems, fetchShoppingLists } from '@/features/shopping/api';
import { describeShoppingError } from '@/features/shopping/errors';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const households = useHouseholdStore();

const tab = ref<'suggestions' | 'all' | 'external'>('suggestions');
const suggestions = ref<RecipeSuggestion[]>([]);
const recipes = ref<RecipeSummary[]>([]);
const loadingSuggestions = ref(false);
const loadingRecipes = ref(false);
const addingRecipeId = ref<number | null>(null);
const onlyReady = ref(false);

const externalQuery = ref('');
const externalRecipes = ref<ExternalRecipeSummary[]>([]);
const externalIngredients = ref<string[]>([]);
const externalInventoryCount = ref(0);
const externalPageNumber = ref(1);
const externalTotalPages = ref(0);
const externalFromInventory = ref(false);
const loadingExternal = ref(false);
const externalLoaded = ref(false);
const showExternalIngredients = ref(false);
const ingredientPreviewLimit = 5;

const displayedExternalIngredients = computed(() =>
  showExternalIngredients.value
    ? externalIngredients.value
    : externalIngredients.value.slice(0, ingredientPreviewLimit),
);

async function loadExternalPage(page: number): Promise<void> {
  loadingExternal.value = true;
  try {
    if (households.selectedId === null) {
      return;
    }
    if (externalFromInventory.value) {
      const suggested = await fetchExternalSuggestions(households.selectedId, page - 1);
      externalRecipes.value = suggested.recipes;
      externalIngredients.value = suggested.ingredient_names;
      externalInventoryCount.value = suggested.inventory_item_count;
      externalTotalPages.value = suggested.total_pages;
    } else {
      const found = await searchExternalRecipes(
        households.selectedId,
        externalQuery.value.trim(),
        page - 1,
      );
      externalRecipes.value = found.recipes;
      externalIngredients.value = [];
      externalInventoryCount.value = 0;
      externalTotalPages.value = found.total_pages;
    }
    externalLoaded.value = true;
  } catch (error) {
    externalRecipes.value = [];
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    loadingExternal.value = false;
  }
}

async function searchExternal(): Promise<void> {
  externalFromInventory.value = false;
  externalPageNumber.value = 1;
  await loadExternalPage(1);
}

async function loadExternalSuggestions(): Promise<void> {
  externalFromInventory.value = true;
  externalPageNumber.value = 1;
  showExternalIngredients.value = false;
  await loadExternalPage(1);
}

async function reloadExternalPage(page: number): Promise<void> {
  await loadExternalPage(page);
}

const visibleSuggestions = computed<RecipeSuggestion[]>(() => {
  const filtered = onlyReady.value
    ? suggestions.value.filter((item) => item.is_ready)
    : suggestions.value;
  return [...filtered].sort((left, right) => {
    if (left.is_ready !== right.is_ready) return left.is_ready ? -1 : 1;
    if (left.missing_item_count !== right.missing_item_count) {
      return left.missing_item_count - right.missing_item_count;
    }
    return left.recipe_name.localeCompare(right.recipe_name, 'pl');
  });
});

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
