<template>
  <q-page padding>
    <q-btn flat dense no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />

    <q-banner v-if="recipe === null && !loading" class="bg-grey-3 q-mt-md">
      Nie udało się wczytać przepisu.
    </q-banner>

    <template v-if="recipe !== null">
      <div class="text-h5 q-mt-md">{{ recipe.name }}</div>
      <div class="text-caption q-mb-md">
        {{ recipe.servings }} porcji · przygotowanie {{ recipe.preparation_time_minutes }} min ·
        gotowanie {{ recipe.cooking_time_minutes }} min · {{ recipe.difficulty }}
        <span v-if="recipe.category_name"> · {{ recipe.category_name }}</span>
      </div>
      <div class="q-gutter-xs q-mb-md">
        <q-badge v-for="tag in recipe.tags" :key="tag" color="primary" outline>{{ tag }}</q-badge>
      </div>

      <q-img v-if="recipe.image_url" :src="recipe.image_url" :alt="recipe.name" class="q-mb-md" />

      <div class="q-mb-md">{{ recipe.description }}</div>

      <div class="text-h6 q-mb-sm">Składniki</div>
      <q-list bordered separator class="q-mb-md">
        <q-item v-for="ingredient in recipe.ingredients" :key="ingredient.ingredient_id">
          <q-item-section>{{ ingredient.ingredient_name }}</q-item-section>
          <q-item-section side>{{ ingredient.quantity }} {{ ingredient.unit_code }}</q-item-section>
        </q-item>
      </q-list>

      <div class="text-h6 q-mb-sm">Przygotowanie</div>
      <q-list bordered separator class="q-mb-md">
        <q-item v-for="step in recipe.steps" :key="step.position">
          <q-item-section avatar>
            <q-avatar color="primary" text-color="white">{{ step.position }}</q-avatar>
          </q-item-section>
          <q-item-section>{{ step.text }}</q-item-section>
        </q-item>
      </q-list>

      <div class="text-h6 q-mb-sm">Brakujące składniki</div>
      <div class="row q-col-gutter-sm items-start q-mb-md">
        <div class="col-6 col-sm-3">
          <q-input v-model.number="servings" dense outlined type="number" min="1" label="Porcje" />
        </div>
        <div class="col-6 col-sm-3">
          <q-btn
            no-caps
            color="primary"
            label="Przelicz"
            :loading="loadingMissing"
            :disable="households.selectedId === null"
            @click="loadMissing"
          />
        </div>
      </div>
      <q-banner v-if="missingLoaded && missingItems.length === 0" class="bg-grey-3">
        Masz w domu wszystkie składniki.
      </q-banner>
      <q-list v-else-if="missingItems.length > 0" bordered separator>
        <q-item v-for="item in missingItems" :key="item.ingredient_id">
          <q-item-section>{{ item.ingredient_name }}</q-item-section>
          <q-item-section side>{{ item.amount }} {{ item.unit_code }}</q-item-section>
        </q-item>
      </q-list>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute } from 'vue-router';
import { fetchMissingItems, fetchRecipe } from '@/features/recipes/api';
import { describeRecipeError } from '@/features/recipes/errors';
import type { MissingItem, RecipeDetail } from '@/features/recipes/models';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const route = useRoute();
const households = useHouseholdStore();

const recipeId = Number(route.params.id);
const recipe = ref<RecipeDetail | null>(null);
const loading = ref(false);
const servings = ref(1);
const missingItems = ref<MissingItem[]>([]);
const missingLoaded = ref(false);
const loadingMissing = ref(false);

function notifyError(error: unknown): void {
  quasar.notify({ type: 'negative', message: describeRecipeError(error) });
}

async function loadRecipe(): Promise<void> {
  loading.value = true;
  try {
    recipe.value = await fetchRecipe(recipeId);
    servings.value = recipe.value.servings;
  } catch (error) {
    recipe.value = null;
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

async function loadMissing(): Promise<void> {
  if (households.selectedId === null) {
    return;
  }
  loadingMissing.value = true;
  try {
    missingItems.value = await fetchMissingItems(recipeId, households.selectedId, servings.value);
    missingLoaded.value = true;
  } catch (error) {
    missingItems.value = [];
    notifyError(error);
  } finally {
    loadingMissing.value = false;
  }
}

onMounted(() => {
  void loadRecipe();
});
</script>
