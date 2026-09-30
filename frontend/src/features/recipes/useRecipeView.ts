import { computed, type Ref } from 'vue';
import { useListQuery } from '@/shared/useRouteQuery';
import {
  RECIPE_LIST_TABS,
  RECIPE_SORTS,
  arrangeRecipes,
  arrangeSuggestions,
  attachRecipes,
  type RecipeListing,
  type RecipeSuggestion,
  type RecipeView,
} from './model';

export function useRecipeView(recipes: Ref<RecipeListing[]>, suggestions: Ref<RecipeSuggestion[]>) {
  const { query, search, sort, isReversed } = useListQuery(RECIPE_SORTS, 'name');
  const tab = query.choiceParam('tab', RECIPE_LIST_TABS, 'suggestions');
  const isReadyOnly = query.flagParam('ready');

  const view = computed<RecipeView>(() => ({
    search: search.value,
    sort: sort.value,
    isReversed: isReversed.value,
  }));
  const cookable = computed(() => attachRecipes(suggestions.value, recipes.value));
  const visibleRecipes = computed(() => arrangeRecipes(recipes.value, view.value));
  const visibleSuggestions = computed(() =>
    arrangeSuggestions(cookable.value, view.value, isReadyOnly.value),
  );
  const isRecipeListFiltered = computed(() => visibleRecipes.value.length < recipes.value.length);
  const isSuggestionListFiltered = computed(
    () => visibleSuggestions.value.length < cookable.value.length,
  );

  return {
    tab,
    search,
    sort,
    isReversed,
    isReadyOnly,
    visibleRecipes,
    visibleSuggestions,
    isRecipeListFiltered,
    isSuggestionListFiltered,
  };
}
