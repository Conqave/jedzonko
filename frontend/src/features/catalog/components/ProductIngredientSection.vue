<template>
  <div>
    <div class="row items-center q-px-md">
      <div class="col">
        <div class="text-subtitle1">Składnik</div>
        <div class="text-caption text-grey-8">Łączy produkt z przepisami i listą zakupów.</div>
      </div>
      <q-btn
        flat
        no-caps
        color="primary"
        icon="auto_awesome"
        label="Przeanalizuj ponownie"
        :disable="hasConfirmed"
        :loading="isAnalyzing"
        @click="analyzeAgain"
      >
        <q-tooltip v-if="hasConfirmed"
          >Odrzuć potwierdzony składnik, aby przeanalizować ponownie.</q-tooltip
        >
      </q-btn>
    </div>
    <q-list separator>
      <q-item v-for="decision in decisions" :key="decision.ingredient.id">
        <q-item-section>
          <q-item-label>{{ decision.ingredient.name }}</q-item-label>
          <q-item-label caption>
            {{ STATUS_LABELS[decision.status] }}
            <template v-if="decision.modelName !== null"
              >· propozycja modelu {{ decision.modelName }}</template
            >
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="row no-wrap q-gutter-xs">
            <q-btn
              v-if="decision.status !== 'confirmed'"
              flat
              dense
              round
              color="positive"
              icon="check"
              :aria-label="`Potwierdź ${decision.ingredient.name}`"
              :loading="busy"
              @click="confirm(decision.ingredient.id)"
            />
            <q-btn
              v-if="decision.status !== 'rejected'"
              flat
              dense
              round
              color="negative"
              icon="close"
              :aria-label="`Odrzuć ${decision.ingredient.name}`"
              :loading="busy"
              @click="reject(decision.ingredient.id)"
            />
          </div>
        </q-item-section>
      </q-item>
      <q-item v-if="decisions.length === 0">
        <q-item-section class="text-grey">Brak propozycji składnika.</q-item-section>
      </q-item>
    </q-list>

    <q-card-section class="row q-col-gutter-sm items-center">
      <div class="col">
        <IngredientPicker v-model="chosen" label="Wybierz inny składnik" />
      </div>
      <div class="col-auto">
        <q-btn
          color="primary"
          no-caps
          label="Ustaw"
          :disable="chosen === null"
          :loading="busy"
          @click="confirmChosen"
        />
      </div>
    </q-card-section>
  </div>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import type { Ingredient, Product, ProductIngredientStatus } from '../model';
import { useProductDecisions } from '../useProductDecisions';
import IngredientPicker from './IngredientPicker.vue';

const STATUS_LABELS: Readonly<Record<ProductIngredientStatus, string>> = {
  proposed: 'Do decyzji',
  confirmed: 'Potwierdzony',
  rejected: 'Odrzucony',
};

const props = defineProps<{ product: Product }>();

const quasar = useQuasar();
const { decisions, hasConfirmed, busy, isAnalyzing, confirm, reject, analyze } =
  useProductDecisions(props.product.id);
const chosen = ref<Ingredient | null>(null);

async function confirmChosen(): Promise<void> {
  const ingredient = chosen.value;
  if (ingredient === null) {
    return;
  }
  const isConfirmed = await confirm(ingredient.id);
  if (isConfirmed) {
    chosen.value = null;
  }
}

async function analyzeAgain(): Promise<void> {
  const isProposed = await analyze();
  if (!isProposed) {
    quasar.notify({ type: 'info', message: 'Model nie znalazł pasującego składnika.' });
  }
}
</script>
