<template>
  <q-page padding>
    <q-btn flat dense no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />
    <div class="text-h5 q-mt-md q-mb-md">
      {{ recipeId === null ? 'Nowy przepis' : 'Edytuj przepis' }}
    </div>
    <RecipeDraftForm
      v-if="isLoaded"
      v-model="draft"
      :units="units"
      :categories="categories"
      :busy="busy"
      @submit="submit"
      @cancel="leave"
    />
  </q-page>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import RecipeDraftForm from '@/features/recipes/components/RecipeDraftForm.vue';
import { useRecipeDraft } from '@/features/recipes/useRecipeDraft';
import { toDecimalText } from '@/shared/decimal';
import { useDialogs } from '@/shared/useDialogs';

const route = useRoute();
const router = useRouter();
const dialogs = useDialogs();
const recipeId = route.params.id === undefined ? null : Number(route.params.id);
const { draft, categories, isLoaded, busy, save } = useRecipeDraft(recipeId);
const { units } = useMeasurementUnits();

async function submit(): Promise<void> {
  draft.value = {
    ...draft.value,
    name: draft.value.name.trim(),
    description: draft.value.description.trim(),
    steps: draft.value.steps.map((text) => text.trim()),
    ingredients: draft.value.ingredients.map((line) => ({
      ...line,
      name: line.name.trim(),
      quantity: toDecimalText(line.quantity),
    })),
  };
  const saved = await save();
  if (saved !== null) {
    dialogs.notifySuccess('Przepis zapisany.');
    await router.push({ name: 'recipe-detail', params: { id: saved.id } });
  }
}

async function leave(): Promise<void> {
  const target =
    recipeId === null ? { name: 'recipes' } : { name: 'recipe-detail', params: { id: recipeId } };
  await router.push(target);
}
</script>
