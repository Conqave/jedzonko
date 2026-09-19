<template>
  <q-page padding>
    <q-inner-loading :showing="loading" />

    <template v-if="recipe !== null">
      <div class="row items-center q-mb-sm">
        <div class="text-h5">{{ recipe.name }}</div>
        <q-space />
        <q-btn flat no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />
      </div>

      <div class="q-mb-md">
        <q-badge color="deep-orange" :label="recipe.source_name" />
        <q-btn
          flat
          dense
          no-caps
          size="sm"
          icon="open_in_new"
          label="Zobacz oryginał"
          type="a"
          :href="recipe.source_url"
          target="_blank"
          rel="noopener"
        />
      </div>

      <q-img
        v-if="recipe.image_url !== null"
        :src="recipe.image_url"
        :alt="recipe.name"
        style="max-height: 280px"
        class="q-mb-md rounded-borders"
      />

      <div class="text-body2 q-mb-md">{{ recipe.description }}</div>

      <q-list bordered separator class="q-mb-md">
        <q-item>
          <q-item-section>Przygotowanie</q-item-section>
          <q-item-section side>{{ recipe.preparation_time_minutes }} min</q-item-section>
        </q-item>
        <q-item>
          <q-item-section>Gotowanie</q-item-section>
          <q-item-section side>{{ recipe.cooking_time_minutes }} min</q-item-section>
        </q-item>
        <q-item v-if="recipe.yield_label">
          <q-item-section>Wydajność</q-item-section>
          <q-item-section side>{{ recipe.yield_label }}</q-item-section>
        </q-item>
      </q-list>

      <div class="text-h6 q-mb-sm">Składniki</div>
      <q-list bordered separator class="q-mb-md">
        <q-item v-for="(ingredient, index) in recipe.ingredients" :key="index">
          <q-item-section>{{ ingredient.source_text }}</q-item-section>
        </q-item>
      </q-list>

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
import { onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute } from 'vue-router';
import { fetchExternalRecipe } from '@/features/recipes/api';
import { describeRecipeError } from '@/features/recipes/errors';
import type { ExternalRecipe } from '@/features/recipes/models';

const quasar = useQuasar();
const route = useRoute();

const recipe = ref<ExternalRecipe | null>(null);
const loading = ref(false);

onMounted(async () => {
  const reference = String(route.params.reference);
  loading.value = true;
  try {
    recipe.value = await fetchExternalRecipe(reference);
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    loading.value = false;
  }
});
</script>
