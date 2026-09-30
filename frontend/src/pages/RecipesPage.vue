<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="text-h5">Przepisy</div>
      <q-space />
      <q-btn no-caps color="primary" icon="add" label="Nowy przepis" :to="{ name: 'recipe-new' }" />
    </div>

    <q-banner v-if="households.selectedId === null" class="bg-grey-3 q-mb-md">
      Nie masz jeszcze gospodarstwa domowego albo żadne nie jest wybrane. Utwórz dom, aby zacząć.
      <template #action>
        <q-btn flat no-caps color="primary" label="Utwórz dom" :to="{ name: 'households' }" />
      </template>
    </q-banner>

    <q-tabs v-model="tab" align="left" class="q-mb-md" dense outside-arrows mobile-arrows>
      <q-tab
        name="suggestions"
        :label="quasar.screen.xs ? 'Z zapasów' : 'Propozycje z zapasów'"
        no-caps
      />
      <q-tab name="all" :label="quasar.screen.xs ? 'Wszystkie' : 'Wszystkie przepisy'" no-caps />
      <q-tab name="external" label="Ania Gotuje" no-caps />
    </q-tabs>

    <ListFilterBar
      v-if="tab !== 'external'"
      v-model:search="search"
      v-model:sort="sort"
      v-model:is-reversed="isReversed"
      search-label="Szukaj po nazwie, składniku, tagu lub kategorii"
      :sorts="RECIPE_SORTS"
      :sort-labels="RECIPE_SORT_LABELS"
    >
      <q-toggle
        v-if="tab === 'suggestions'"
        v-model="isReadyOnly"
        dense
        label="Tylko te, które ugotuję teraz"
      />
    </ListFilterBar>

    <q-linear-progress v-if="busy || isSearching" indeterminate class="q-mb-sm" />

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="suggestions" class="q-pa-none">
        <template v-if="households.selectedId !== null">
          <RecipeSuggestionList
            :suggestions="visibleSuggestions"
            :is-filtered="isSuggestionListFiltered"
            :household-id="households.selectedId"
            :describe-unit-quantity="describeUnitQuantity"
          />
        </template>
      </q-tab-panel>

      <q-tab-panel name="all" class="q-pa-none">
        <RecipeList :recipes="visibleRecipes" :is-filtered="isRecipeListFiltered" />
      </q-tab-panel>

      <q-tab-panel name="external" class="q-pa-none">
        <template v-if="households.selectedId !== null">
          <q-form class="row q-col-gutter-sm items-start q-mb-md" @submit="searchByText">
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
              <q-btn type="submit" color="primary" label="Szukaj" no-caps :loading="isSearching" />
            </div>
            <div class="col-auto">
              <q-btn
                outline
                color="primary"
                label="Z moich zapasów"
                no-caps
                :loading="isSearching"
                @click="searchFromPantry"
              />
            </div>
          </q-form>
          <q-banner v-if="pantryIngredientNames.length > 0" class="bg-grey-3 q-mb-md">
            Szukam po {{ pantryIngredientNames.length }} składnikach z
            {{ pantryItemCount }} produktów w domu.
          </q-banner>
          <template v-if="externalPage !== null">
            <ExternalRecipeList :recipes="externalPage.recipes" />
            <div v-if="externalPage.totalPages > 1" class="row justify-center q-mt-md">
              <q-pagination
                :model-value="externalPage.page + 1"
                :max="externalPage.totalPages"
                :max-pages="7"
                boundary-numbers
                @update:model-value="openExternalPage"
              />
            </div>
          </template>
        </template>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref, toRef } from 'vue';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useHouseholdStore } from '@/features/households/store';
import ExternalRecipeList from '@/features/recipes/components/ExternalRecipeList.vue';
import RecipeList from '@/features/recipes/components/RecipeList.vue';
import RecipeSuggestionList from '@/features/recipes/components/RecipeSuggestionList.vue';
import { RECIPE_SORT_LABELS, RECIPE_SORTS } from '@/features/recipes/model';
import { useExternalRecipeSearch } from '@/features/recipes/useExternalRecipeSearch';
import { useRecipeCatalog } from '@/features/recipes/useRecipeCatalog';
import { useRecipeView } from '@/features/recipes/useRecipeView';
import ListFilterBar from '@/shared/components/ListFilterBar.vue';

const quasar = useQuasar();
const households = useHouseholdStore();
const selectedId = toRef(households, 'selectedId');
const { recipes, suggestions, busy } = useRecipeCatalog(selectedId);
const { describeUnitQuantity } = useMeasurementUnits();
const {
  page: externalPage,
  pantryIngredientNames,
  pantryItemCount,
  busy: isSearching,
  loadPage,
  searchByQuery,
  searchByPantry,
} = useExternalRecipeSearch();

const {
  tab,
  search,
  sort,
  isReversed,
  isReadyOnly,
  visibleRecipes,
  visibleSuggestions,
  isRecipeListFiltered,
  isSuggestionListFiltered,
} = useRecipeView(recipes, suggestions);
const externalQuery = ref('');

async function searchByText(): Promise<void> {
  if (households.selectedId !== null) {
    await searchByQuery(households.selectedId, externalQuery.value);
  }
}

async function searchFromPantry(): Promise<void> {
  if (households.selectedId !== null) {
    await searchByPantry(households.selectedId);
  }
}

async function openExternalPage(pageNumber: number): Promise<void> {
  if (households.selectedId !== null) {
    await loadPage(households.selectedId, pageNumber - 1);
  }
}
</script>
