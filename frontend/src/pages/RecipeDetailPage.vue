<template>
  <q-page padding>
    <q-btn flat dense no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />

    <template v-if="recipe !== null">
      <div class="text-h5 q-mt-md">{{ recipe.name }}</div>
      <div class="row items-center q-gutter-sm q-mt-xs">
        <q-btn
          no-caps
          color="primary"
          icon="restaurant"
          label="Ugotowane"
          :loading="busy"
          :disable="households.selectedId === null"
          @click="confirmPrepared"
        />
        <q-btn
          flat
          no-caps
          color="primary"
          icon="edit"
          label="Edytuj"
          :to="{ name: 'recipe-edit', params: { id: recipe.id } }"
        />
        <q-btn flat no-caps color="negative" icon="delete" label="Usuń" @click="removeRecipe" />
      </div>
      <div class="text-caption q-mt-sm q-mb-md">
        autor: {{ recipe.authorUsername ?? 'nieznany' }} · porcje: {{ recipe.servings }} ·
        przygotowanie {{ recipe.preparationTimeMinutes }} min · gotowanie
        {{ recipe.cookingTimeMinutes }} min ·
        {{ DIFFICULTY_LABELS[recipe.difficulty] }}
        <span v-if="recipe.category !== null"> · {{ recipe.category.name }}</span>
      </div>
      <NutritionSummary v-if="nutrition !== null" :nutrition="nutrition" class="q-mb-md" />
      <div class="q-gutter-xs q-mb-md">
        <q-badge v-for="tag in recipe.tags" :key="tag" color="primary" outline>{{ tag }}</q-badge>
      </div>
      <q-img
        v-if="recipe.imageUrl !== null"
        :src="recipe.imageUrl"
        :alt="recipe.name"
        class="q-mb-md"
      />
      <div class="q-mb-md">{{ recipe.description }}</div>

      <div class="text-h6 q-mb-sm">Składniki</div>
      <q-list bordered separator class="q-mb-md">
        <q-item v-for="line in recipe.ingredients" :key="line.name">
          <q-item-section>{{ line.name }}</q-item-section>
          <q-item-section side>{{
            describeUnitQuantity(line.quantity, line.unitCode)
          }}</q-item-section>
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

      <template v-if="households.selectedId !== null">
        <div class="text-h6 q-mb-sm">Czego brakuje</div>
        <div class="row q-col-gutter-sm items-start q-mb-md">
          <div class="col-6 col-sm-3">
            <q-input
              v-model.number="servings"
              dense
              outlined
              type="number"
              min="1"
              label="Porcje"
            />
          </div>
          <div class="col-auto">
            <q-btn
              no-caps
              color="primary"
              label="Sprawdź"
              :loading="busy"
              @click="checkShortfall"
            />
          </div>
          <div v-if="shortfall !== null && shortfall.missingItems.length > 0" class="col-auto">
            <RecipeShoppingButton
              :household-id="households.selectedId"
              :source="{ kind: 'recipe', recipeId, servings }"
            />
          </div>
        </div>
        <ShortfallView
          v-if="shortfall !== null"
          :shortfall="shortfall"
          :describe-unit-quantity="describeUnitQuantity"
        />
      </template>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useHouseholdStore } from '@/features/households/store';
import NutritionSummary from '@/features/recipes/components/NutritionSummary.vue';
import ShortfallView from '@/features/recipes/components/ShortfallView.vue';
import { DIFFICULTY_LABELS } from '@/features/recipes/model';
import { useRecipe } from '@/features/recipes/useRecipe';
import RecipeShoppingButton from '@/features/shopping/components/RecipeShoppingButton.vue';
import { useDialogs } from '@/shared/useDialogs';

const route = useRoute();
const router = useRouter();
const households = useHouseholdStore();
const dialogs = useDialogs();
const recipeId = Number(route.params.id);
const { recipe, shortfall, nutrition, busy, loadShortfall, confirm, remove } = useRecipe(recipeId);
const { describeUnitQuantity } = useMeasurementUnits();
const servings = ref(1);

watch(recipe, (loaded) => {
  if (loaded !== null) {
    servings.value = loaded.servings;
  }
});

async function checkShortfall(): Promise<void> {
  if (households.selectedId !== null) {
    await loadShortfall(households.selectedId, servings.value);
  }
}

async function confirmPrepared(): Promise<void> {
  const householdId = households.selectedId;
  if (householdId === null) {
    return;
  }
  const message = `Składniki na ${servings.value} porcji zostaną odjęte od zapasów.`;
  const isConfirmed = await dialogs.confirm('Ugotowane?', message);
  if (!isConfirmed) {
    return;
  }
  const isPrepared = await confirm(householdId, servings.value);
  if (isPrepared) {
    dialogs.notifySuccess(`Zużyto składniki na ${servings.value} porcji.`);
  }
}

async function removeRecipe(): Promise<void> {
  const isConfirmed = await dialogs.confirm('Usunąć przepis?', 'Tej operacji nie można cofnąć.');
  if (!isConfirmed) {
    return;
  }
  const isRemoved = await remove();
  if (isRemoved) {
    await router.push({ name: 'recipes' });
  }
}
</script>
