<template>
  <q-page padding>
    <q-btn flat dense no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />

    <q-banner v-if="recipe === null && !loading" class="bg-grey-3 q-mt-md">
      Nie udało się wczytać przepisu.
    </q-banner>

    <template v-if="recipe !== null">
      <div class="text-h5 q-mt-md">{{ recipe.name }}</div>
      <div class="row items-center q-gutter-sm q-mt-xs">
        <q-btn
          no-caps
          color="primary"
          icon="restaurant"
          label="Ugotowane"
          :loading="confirming"
          :disable="households.selectedId === null"
          @click="askConfirmPreparation"
        >
          <q-tooltip v-if="households.selectedId === null">
            Wybierz gospodarstwo domowe, aby potwierdzić przygotowanie.
          </q-tooltip>
        </q-btn>
        <q-btn
          flat
          no-caps
          color="primary"
          icon="edit"
          label="Edytuj"
          :to="{ name: 'recipe-edit', params: { id: recipe.id } }"
        />
        <q-btn flat no-caps color="negative" icon="delete" label="Usuń" @click="askDelete" />
      </div>
      <div class="text-caption q-mb-md">
        autor: {{ recipe.author_username }} · {{ recipe.servings }} porcji · przygotowanie
        {{ recipe.preparation_time_minutes }} min · gotowanie {{ recipe.cooking_time_minutes }} min
        · {{ recipe.difficulty }}
        <span v-if="recipe.category_name"> · {{ recipe.category_name }}</span>
      </div>
      <div class="q-gutter-xs q-mb-md">
        <q-badge v-for="tag in recipe.tags" :key="tag" color="primary" outline>{{ tag }}</q-badge>
      </div>

      <q-img v-if="recipe.image_url" :src="recipe.image_url" :alt="recipe.name" class="q-mb-md" />

      <div class="q-mb-md">{{ recipe.description }}</div>

      <div class="text-h6 q-mb-sm">Składniki</div>
      <q-list bordered separator class="q-mb-md">
        <q-item v-for="ingredient in recipe.ingredients" :key="ingredient.name">
          <q-item-section>{{ ingredient.name }}</q-item-section>
          <q-item-section side
            >{{ formatQuantity(ingredient.quantity) }} {{ ingredient.unit_code }}</q-item-section
          >
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
      <template v-if="shortfall !== null">
        <q-banner v-if="shortfall.is_ready" class="bg-green-2 q-mb-sm">
          <q-badge color="positive" class="q-mr-sm">Ugotujesz teraz</q-badge>
          Masz w domu wszystkie składniki.
        </q-banner>
        <q-banner
          v-else-if="shortfall.unmeasured_ingredients.length > 0"
          class="bg-orange-2 q-mb-sm"
        >
          Nie da się porównać ilości dla:
          {{ shortfall.unmeasured_ingredients.join(', ') }}
        </q-banner>
      </template>
      <q-list v-if="shortfall !== null && shortfall.missing_items.length > 0" bordered separator>
        <q-item v-for="item in shortfall.missing_items" :key="item.name">
          <q-item-section>{{ item.name }}</q-item-section>
          <q-item-section side
            >{{ formatQuantity(item.amount) }} {{ item.unit_code }}</q-item-section
          >
        </q-item>
      </q-list>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { formatQuantity } from '@/features/shared/formatQuantity';
import { onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import {
  confirmPreparation,
  deleteRecipe,
  fetchMissingItems,
  fetchRecipe,
} from '@/features/recipes/api';
import { describeRecipeError } from '@/features/recipes/errors';
import type { RecipeDetail, RecipeShortfall } from '@/features/recipes/models';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const route = useRoute();
const router = useRouter();
const households = useHouseholdStore();

const recipeId = Number(route.params.id);
const recipe = ref<RecipeDetail | null>(null);
const loading = ref(false);
const servings = ref(1);
const shortfall = ref<RecipeShortfall | null>(null);
const loadingMissing = ref(false);
const confirming = ref(false);

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
    shortfall.value = await fetchMissingItems(recipeId, households.selectedId, servings.value);
  } catch (error) {
    shortfall.value = null;
    notifyError(error);
  } finally {
    loadingMissing.value = false;
  }
}

function askConfirmPreparation(): void {
  const householdId = households.selectedId;
  if (householdId === null) {
    return;
  }
  quasar
    .dialog({
      title: 'Potwierdź przygotowanie',
      message:
        'Potwierdzenie ZUŻYJE składniki tego przepisu z zapasów wybranego gospodarstwa domowego ' +
        '(„Mam w domu”). Ilości zostaną odjęte od stanu w spiżarni. Podaj liczbę ugotowanych porcji:',
      prompt: { model: String(servings.value), type: 'number' },
      cancel: { label: 'Anuluj', flat: true, noCaps: true },
      ok: { label: 'Ugotowane — zużyj składniki', color: 'primary', noCaps: true },
      persistent: true,
    })
    .onOk((value: string) => {
      void runConfirmPreparation(householdId, Number(value));
    });
}

async function runConfirmPreparation(householdId: number, preparedServings: number): Promise<void> {
  confirming.value = true;
  try {
    await confirmPreparation(recipeId, householdId, preparedServings);
    quasar.notify({
      type: 'positive',
      message: `Zużyto składniki na ${preparedServings} porcji.`,
    });
    servings.value = preparedServings;
    await loadMissing();
  } catch (error) {
    notifyError(error);
  } finally {
    confirming.value = false;
  }
}

function askDelete(): void {
  quasar
    .dialog({
      title: 'Usuń przepis',
      message: 'Czy na pewno usunąć ten przepis? Tej operacji nie można cofnąć.',
      cancel: { label: 'Anuluj', flat: true, noCaps: true },
      ok: { label: 'Usuń', color: 'negative', noCaps: true },
      persistent: true,
    })
    .onOk(() => {
      void runDelete();
    });
}

async function runDelete(): Promise<void> {
  try {
    await deleteRecipe(recipeId);
    quasar.notify({ type: 'positive', message: 'Przepis usunięty.' });
    await router.push({ name: 'recipes' });
  } catch (error) {
    notifyError(error);
  }
}

onMounted(() => {
  void loadRecipe();
});
</script>
