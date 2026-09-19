<template>
  <q-page padding>
    <q-btn flat dense no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />

    <div class="text-h5 q-mt-md q-mb-md">
      {{ isEdit ? 'Edytuj przepis' : 'Nowy przepis' }}
    </div>

    <q-inner-loading :showing="loading" />

    <q-form v-if="!loading" @submit="save">
      <div class="row q-col-gutter-md">
        <div class="col-12">
          <q-input
            v-model="form.name"
            outlined
            label="Nazwa"
            :rules="[(value: string) => value.trim().length > 0 || 'Podaj nazwę przepisu.']"
          />
        </div>
        <div class="col-12">
          <q-input v-model="form.description" outlined type="textarea" autogrow label="Opis" />
        </div>
        <div class="col-6 col-sm-3">
          <q-input
            v-model.number="form.servings"
            outlined
            type="number"
            min="1"
            label="Porcje"
            :rules="[(value: number) => value >= 1 || 'Minimum 1 porcja.']"
          />
        </div>
        <div class="col-6 col-sm-3">
          <q-input
            v-model.number="form.preparation_time_minutes"
            outlined
            type="number"
            min="0"
            label="Przygotowanie (min)"
            :rules="[(value: number) => value >= 0 || 'Podaj liczbę minut.']"
          />
        </div>
        <div class="col-6 col-sm-3">
          <q-input
            v-model.number="form.cooking_time_minutes"
            outlined
            type="number"
            min="0"
            label="Gotowanie (min)"
            :rules="[(value: number) => value >= 0 || 'Podaj liczbę minut.']"
          />
        </div>
        <div class="col-6 col-sm-3">
          <q-select
            v-model="form.difficulty"
            outlined
            emit-value
            map-options
            :options="difficultyOptions"
            label="Trudność"
          />
        </div>
        <div class="col-12">
          <q-select
            v-model="form.tag_names"
            outlined
            multiple
            use-input
            use-chips
            hide-dropdown-icon
            new-value-mode="add-unique"
            label="Tagi"
            hint="Wpisz tag i zatwierdź Enterem."
          />
        </div>
      </div>

      <div class="text-h6 q-mt-lg q-mb-sm">Składniki</div>
      <div
        v-for="(ingredient, index) in form.ingredients"
        :key="`ingredient-${index}`"
        class="row q-col-gutter-sm items-start"
      >
        <div class="col-12 col-sm-5">
          <q-input
            v-model="ingredient.name"
            outlined
            dense
            label="Składnik"
            :rules="[(value: string) => value.trim().length > 0 || 'Podaj nazwę składnika.']"
          />
        </div>
        <div class="col-6 col-sm-3">
          <q-input
            v-model="ingredient.quantity"
            outlined
            dense
            type="number"
            min="0"
            step="0.001"
            label="Ilość"
            :rules="[(value: string) => Number(value) > 0 || 'Podaj ilość większą od zera.']"
          />
        </div>
        <div class="col-4 col-sm-3">
          <q-select
            v-model="ingredient.unit_code"
            outlined
            dense
            emit-value
            map-options
            option-value="code"
            option-label="name"
            :options="units"
            label="Jednostka"
            :rules="[(value: string) => value.length > 0 || 'Wybierz jednostkę.']"
          />
        </div>
        <div class="col-2 col-sm-1">
          <q-btn
            flat
            dense
            round
            color="negative"
            icon="delete"
            :disable="form.ingredients.length === 1"
            @click="removeIngredient(index)"
          >
            <q-tooltip>Usuń składnik</q-tooltip>
          </q-btn>
        </div>
      </div>
      <q-btn
        flat
        no-caps
        color="primary"
        icon="add"
        label="Dodaj składnik"
        @click="addIngredient"
      />

      <div class="text-h6 q-mt-lg q-mb-sm">Kroki przygotowania</div>
      <div
        v-for="(step, index) in form.steps"
        :key="`step-${index}`"
        class="row q-col-gutter-sm items-start"
      >
        <div class="col-12 col-sm-10">
          <q-input
            v-model="step.text"
            outlined
            dense
            autogrow
            :label="`Krok ${index + 1}`"
            :rules="[(value: string) => value.trim().length > 0 || 'Opisz krok.']"
          />
        </div>
        <div class="col-12 col-sm-2">
          <q-btn
            flat
            dense
            round
            icon="arrow_upward"
            :disable="index === 0"
            @click="moveStep(index, -1)"
          >
            <q-tooltip>W górę</q-tooltip>
          </q-btn>
          <q-btn
            flat
            dense
            round
            icon="arrow_downward"
            :disable="index === form.steps.length - 1"
            @click="moveStep(index, 1)"
          >
            <q-tooltip>W dół</q-tooltip>
          </q-btn>
          <q-btn
            flat
            dense
            round
            color="negative"
            icon="delete"
            :disable="form.steps.length === 1"
            @click="removeStep(index)"
          >
            <q-tooltip>Usuń krok</q-tooltip>
          </q-btn>
        </div>
      </div>
      <q-btn flat no-caps color="primary" icon="add" label="Dodaj krok" @click="addStep" />

      <q-banner class="bg-grey-3 q-mt-lg">
        Kategoria przepisu nie jest jeszcze dostępna w formularzu — backend nie udostępnia listy
        kategorii.
      </q-banner>

      <div class="q-mt-lg q-gutter-sm">
        <q-btn type="submit" no-caps color="primary" label="Zapisz" :loading="saving" />
        <q-btn flat no-caps label="Anuluj" :to="cancelTarget" />
      </div>
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { createRecipe, fetchRecipe, updateRecipe } from '@/features/recipes/api';
import { describeRecipeError } from '@/features/recipes/errors';
import type { RecipeInput } from '@/features/recipes/models';
import { fetchUnits } from '@/features/products/api';
import type { MeasurementUnit } from '@/features/products/models';

const quasar = useQuasar();
const route = useRoute();
const router = useRouter();

const difficultyOptions = [
  { value: 'easy', label: 'Łatwy' },
  { value: 'medium', label: 'Średni' },
  { value: 'hard', label: 'Trudny' },
];

const recipeId = route.params.id === undefined ? null : Number(route.params.id);
const isEdit = recipeId !== null;

const units = ref<MeasurementUnit[]>([]);
const loading = ref(true);
const saving = ref(false);

const form = reactive<RecipeInput>({
  name: '',
  description: '',
  servings: 4,
  preparation_time_minutes: 0,
  cooking_time_minutes: 0,
  difficulty: 'easy',
  tag_names: [],
  steps: [{ position: 1, text: '' }],
  ingredients: [{ name: '', quantity: '', unit_code: '' }],
});

const cancelTarget = computed(() =>
  isEdit ? { name: 'recipe-detail', params: { id: recipeId } } : { name: 'recipes' },
);

function addIngredient(): void {
  form.ingredients.push({ name: '', quantity: '', unit_code: '' });
}

function removeIngredient(index: number): void {
  form.ingredients.splice(index, 1);
}

function addStep(): void {
  form.steps.push({ position: form.steps.length + 1, text: '' });
}

function removeStep(index: number): void {
  form.steps.splice(index, 1);
}

function moveStep(index: number, offset: number): void {
  const moved = form.steps[index];
  const target = form.steps[index + offset];
  if (moved === undefined || target === undefined) {
    return;
  }
  form.steps[index] = target;
  form.steps[index + offset] = moved;
}

async function load(): Promise<void> {
  loading.value = true;
  try {
    units.value = await fetchUnits();
    if (recipeId !== null) {
      const recipe = await fetchRecipe(recipeId);
      form.name = recipe.name;
      form.description = recipe.description;
      form.servings = recipe.servings;
      form.preparation_time_minutes = recipe.preparation_time_minutes;
      form.cooking_time_minutes = recipe.cooking_time_minutes;
      form.difficulty = recipe.difficulty;
      form.tag_names = [...recipe.tags];
      form.ingredients = recipe.ingredients.map((ingredient) => ({ ...ingredient }));
      form.steps = recipe.steps.map((step, index) => ({ position: index + 1, text: step.text }));
    }
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    loading.value = false;
  }
}

async function save(): Promise<void> {
  const payload: RecipeInput = {
    name: form.name.trim(),
    description: form.description.trim(),
    servings: form.servings,
    preparation_time_minutes: form.preparation_time_minutes,
    cooking_time_minutes: form.cooking_time_minutes,
    difficulty: form.difficulty,
    tag_names: [...form.tag_names],
    steps: form.steps.map((step, index) => ({ position: index + 1, text: step.text.trim() })),
    ingredients: form.ingredients.map((ingredient) => ({
      name: ingredient.name.trim(),
      quantity: ingredient.quantity,
      unit_code: ingredient.unit_code,
    })),
  };
  saving.value = true;
  try {
    const saved =
      recipeId === null ? await createRecipe(payload) : await updateRecipe(recipeId, payload);
    quasar.notify({ type: 'positive', message: 'Przepis zapisany.' });
    await router.push({ name: 'recipe-detail', params: { id: saved.id } });
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void load();
});
</script>
