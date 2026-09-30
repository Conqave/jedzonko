<template>
  <q-page padding>
    <q-btn flat dense no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />
    <q-linear-progress v-if="busy" indeterminate class="q-my-sm" />

    <template v-if="recipe !== null">
      <div class="text-h5 q-mt-md">{{ recipe.name }}</div>
      <div class="q-mb-md">
        <q-badge color="deep-orange" :label="recipe.sourceName" />
        <q-btn
          flat
          dense
          no-caps
          size="sm"
          icon="open_in_new"
          label="Zobacz oryginał"
          type="a"
          :href="recipe.sourceUrl"
          target="_blank"
          rel="noopener"
        />
      </div>
      <q-img
        v-if="recipe.imageUrl !== null"
        :src="recipe.imageUrl"
        :alt="recipe.name"
        style="max-height: 280px"
        class="q-mb-md rounded-borders"
      />
      <div class="text-body2 q-mb-md">{{ recipe.description }}</div>
      <div class="text-caption q-mb-md">
        <span v-if="recipe.preparationTimeMinutes !== null"
          >przygotowanie {{ recipe.preparationTimeMinutes }} min</span
        >
        <span v-if="recipe.cookingTimeMinutes !== null">
          · gotowanie {{ recipe.cookingTimeMinutes }} min</span
        >
        <span v-if="recipe.yieldLabel !== ''"> · {{ recipe.yieldLabel }}</span>
      </div>

      <NutritionSummary v-if="nutrition !== null" :nutrition="nutrition" class="q-mb-md" />

      <div class="text-h6 q-mb-sm">Składniki</div>
      <q-list bordered separator class="q-mb-md">
        <q-item v-for="(line, index) in recipe.ingredients" :key="index">
          <q-item-section>{{ line.sourceText }}</q-item-section>
        </q-item>
      </q-list>

      <q-banner v-if="isMatching" class="bg-blue-1 q-mb-md">
        <template #avatar><q-spinner color="primary" size="24px" /></template>
        Dopasowuję składniki przepisu do Twoich zapasów…
      </q-banner>
      <template v-if="households.selectedId !== null && shortfall !== null">
        <div class="row items-center q-mb-sm">
          <div class="text-h6 col">Czego brakuje</div>
          <RecipeShoppingButton
            v-if="shortfall.missingItems.length > 0"
            :household-id="households.selectedId"
            :source="{ kind: 'external', reference }"
          />
        </div>
        <ShortfallView
          :shortfall="shortfall"
          :describe-unit-quantity="describeUnitQuantity"
          class="q-mb-md"
        />
      </template>

      <div class="text-h6 q-mb-sm">Przygotowanie</div>
      <q-list bordered separator>
        <q-item v-for="(step, index) in recipe.steps" :key="index">
          <q-item-section avatar>
            <q-avatar color="primary" text-color="white" size="28px">{{ index + 1 }}</q-avatar>
          </q-item-section>
          <q-item-section>{{ step }}</q-item-section>
        </q-item>
      </q-list>

      <div v-if="recipe.tags.length > 0" class="q-mt-md">
        <q-chip v-for="tag in recipe.tags" :key="tag" dense square outline>{{ tag }}</q-chip>
      </div>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { toRef } from 'vue';
import { useRoute } from 'vue-router';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useHouseholdStore } from '@/features/households/store';
import NutritionSummary from '@/features/recipes/components/NutritionSummary.vue';
import ShortfallView from '@/features/recipes/components/ShortfallView.vue';
import { useExternalRecipe } from '@/features/recipes/useExternalRecipe';
import RecipeShoppingButton from '@/features/shopping/components/RecipeShoppingButton.vue';

const route = useRoute();
const households = useHouseholdStore();
const reference = String(route.params.reference);
const selectedId = toRef(households, 'selectedId');
const { recipe, shortfall, nutrition, busy, isMatching } = useExternalRecipe(reference, selectedId);
const { describeUnitQuantity } = useMeasurementUnits();
</script>
