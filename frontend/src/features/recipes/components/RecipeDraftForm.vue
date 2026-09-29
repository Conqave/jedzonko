<template>
  <q-form @submit="emit('submit')">
    <div class="row q-col-gutter-md">
      <div class="col-12">
        <q-input
          v-model="draft.name"
          outlined
          label="Nazwa"
          :rules="[(value: string) => value.trim() !== '' || 'Podaj nazwę przepisu.']"
        />
      </div>
      <div class="col-12">
        <q-input v-model="draft.description" outlined type="textarea" autogrow label="Opis" />
      </div>
      <div class="col-6 col-sm-3">
        <q-input
          v-model.number="draft.servings"
          outlined
          type="number"
          min="1"
          label="Porcje"
          :rules="[(value: number) => value >= 1 || 'Minimum 1 porcja.']"
        />
      </div>
      <div class="col-6 col-sm-3">
        <q-input
          v-model.number="draft.preparationTimeMinutes"
          outlined
          type="number"
          min="0"
          label="Przygotowanie (min)"
          :rules="[(value: number) => value >= 0 || 'Podaj liczbę minut.']"
        />
      </div>
      <div class="col-6 col-sm-3">
        <q-input
          v-model.number="draft.cookingTimeMinutes"
          outlined
          type="number"
          min="0"
          label="Gotowanie (min)"
          :rules="[(value: number) => value >= 0 || 'Podaj liczbę minut.']"
        />
      </div>
      <div class="col-6 col-sm-3">
        <q-select
          v-model="draft.difficulty"
          outlined
          emit-value
          map-options
          :options="DIFFICULTY_OPTIONS"
          label="Trudność"
        />
      </div>
      <div class="col-12 col-sm-6">
        <q-select
          v-model="draft.categoryId"
          outlined
          clearable
          emit-value
          map-options
          option-value="id"
          option-label="name"
          :options="categories"
          label="Kategoria"
        />
      </div>
      <div class="col-12">
        <q-select
          v-model="draft.tagNames"
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
      v-for="(line, index) in draft.ingredients"
      :key="`ingredient-${index}`"
      class="row q-col-gutter-sm items-start"
    >
      <div class="col-12 col-sm-5">
        <q-input
          v-model="line.name"
          outlined
          dense
          label="Składnik"
          :rules="[(value: string) => value.trim() !== '' || 'Podaj nazwę składnika.']"
        />
      </div>
      <div class="col-6 col-sm-3">
        <q-input
          v-model="line.quantity"
          outlined
          dense
          inputmode="decimal"
          label="Ilość"
          :rules="[(value: string) => isPositiveDecimal(value) || 'Podaj ilość większą od zera.']"
        />
      </div>
      <div class="col-4 col-sm-3">
        <q-select
          v-model="line.unitCode"
          outlined
          dense
          emit-value
          map-options
          option-value="code"
          option-label="name"
          :options="units"
          label="Jednostka"
          :rules="[(value: string) => value !== '' || 'Wybierz jednostkę.']"
        />
      </div>
      <div class="col-2 col-sm-1">
        <q-btn
          flat
          dense
          round
          color="negative"
          icon="delete"
          aria-label="Usuń składnik"
          :disable="draft.ingredients.length === 1"
          @click="removeIngredient(index)"
        />
      </div>
    </div>
    <q-btn flat no-caps color="primary" icon="add" label="Dodaj składnik" @click="addIngredient" />

    <div class="text-h6 q-mt-lg q-mb-sm">Kroki przygotowania</div>
    <div
      v-for="(_, index) in draft.steps"
      :key="`step-${index}`"
      class="row q-col-gutter-sm items-start"
    >
      <div class="col-12 col-sm-10">
        <q-input
          v-model="draft.steps[index]"
          outlined
          dense
          autogrow
          :label="`Krok ${index + 1}`"
          :rules="[(value: string) => value.trim() !== '' || 'Opisz krok.']"
        />
      </div>
      <div class="col-12 col-sm-2">
        <q-btn
          flat
          dense
          round
          icon="arrow_upward"
          aria-label="W górę"
          :disable="index === 0"
          @click="moveStep(index, -1)"
        />
        <q-btn
          flat
          dense
          round
          icon="arrow_downward"
          aria-label="W dół"
          :disable="index === draft.steps.length - 1"
          @click="moveStep(index, 1)"
        />
        <q-btn
          flat
          dense
          round
          color="negative"
          icon="delete"
          aria-label="Usuń krok"
          :disable="draft.steps.length === 1"
          @click="removeStep(index)"
        />
      </div>
    </div>
    <q-btn flat no-caps color="primary" icon="add" label="Dodaj krok" @click="addStep" />

    <div class="q-mt-lg q-gutter-sm">
      <q-btn type="submit" no-caps color="primary" label="Zapisz" :loading="busy" />
      <q-btn flat no-caps label="Anuluj" @click="emit('cancel')" />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import type { MeasurementUnit } from '@/features/catalog/model';
import { isPositiveDecimal } from '@/shared/decimal';
import {
  DIFFICULTY_LABELS,
  moveItem,
  RECIPE_DIFFICULTIES,
  type RecipeCategory,
  type RecipeDraft,
} from '../model';

const DIFFICULTY_OPTIONS = RECIPE_DIFFICULTIES.map((value) => ({
  value,
  label: DIFFICULTY_LABELS[value],
}));

defineProps<{ units: MeasurementUnit[]; categories: RecipeCategory[]; busy: boolean }>();

const emit = defineEmits<{ submit: []; cancel: [] }>();

const draft = defineModel<RecipeDraft>({ required: true });

function addIngredient(): void {
  draft.value.ingredients.push({ name: '', quantity: '', unitCode: '' });
}

function removeIngredient(index: number): void {
  draft.value.ingredients.splice(index, 1);
}

function addStep(): void {
  draft.value.steps.push('');
}

function removeStep(index: number): void {
  draft.value.steps.splice(index, 1);
}

function moveStep(index: number, offset: number): void {
  draft.value.steps = moveItem(draft.value.steps, index, offset);
}
</script>
