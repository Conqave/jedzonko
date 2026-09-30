<template>
  <div>
    <div class="row items-center q-px-md">
      <div class="col">
        <div class="text-subtitle1">Tagi</div>
        <div class="text-caption text-grey-8">
          Tagi Ania Gotuje łączą produkt z przepisami i listą zakupów.
        </div>
      </div>
      <q-btn
        flat
        no-caps
        color="primary"
        icon="auto_awesome"
        label="Przeanalizuj ponownie"
        :loading="isAnalyzing"
        @click="analyzeAgain"
      />
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
          <TagFactCaption
            :text="describeTagCalories(decision.calories)"
            :source="decision.calories"
          />
          <TagFactCaption
            :text="describeTagPieceWeight(decision.pieceWeight)"
            :source="decision.pieceWeight"
          />
          <TagFactCaption :text="describeTagDensity(decision.density)" :source="decision.density" />
        </q-item-section>
        <q-item-section side>
          <div class="row no-wrap q-gutter-xs">
            <q-btn
              flat
              dense
              round
              color="deep-orange"
              icon="local_fire_department"
              :aria-label="`Kalorie ${decision.ingredient.name}`"
              :loading="busy"
              @click="editCalories(decision)"
            />
            <q-btn
              flat
              dense
              round
              color="brown"
              icon="scale"
              :aria-label="`Waga sztuki ${decision.ingredient.name}`"
              :loading="busy"
              @click="editPieceWeight(decision)"
            />
            <q-btn
              flat
              dense
              round
              color="blue"
              icon="water_drop"
              :aria-label="`Gęstość ${decision.ingredient.name}`"
              :loading="busy"
              @click="editDensity(decision)"
            />
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
        <q-item-section class="text-grey">Brak tagów i propozycji.</q-item-section>
      </q-item>
    </q-list>

    <q-card-section class="row q-col-gutter-sm items-center">
      <div class="col">
        <IngredientPicker v-model="chosen" label="Dodaj tag" />
      </div>
      <div class="col-auto">
        <q-btn
          color="primary"
          no-caps
          label="Dodaj"
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
import { formatQuantity } from '@/shared/formatQuantity';
import { useDialogs } from '@/shared/useDialogs';
import {
  describeTagCalories,
  describeTagDensity,
  describeTagPieceWeight,
  isDensityInput,
  isKcalInput,
  isPieceWeightInput,
  toOptionalDecimalPayload,
  type Ingredient,
  type Product,
  type ProductIngredientDecision,
  type ProductIngredientStatus,
} from '../model';
import { useProductDecisions } from '../useProductDecisions';
import IngredientPicker from './IngredientPicker.vue';
import TagFactCaption from './TagFactCaption.vue';

const STATUS_LABELS: Readonly<Record<ProductIngredientStatus, string>> = {
  proposed: 'Do decyzji',
  confirmed: 'Potwierdzony',
  rejected: 'Odrzucony',
};

const props = defineProps<{ product: Product }>();

const quasar = useQuasar();
const dialogs = useDialogs();
const {
  decisions,
  busy,
  isAnalyzing,
  confirm,
  reject,
  setCalories,
  setPieceWeight,
  setDensity,
  analyze,
} = useProductDecisions(props.product.id);
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

async function editCalories(decision: ProductIngredientDecision): Promise<void> {
  const calories = decision.calories;
  const prompt = {
    title: `Kalorie: ${decision.ingredient.name}`,
    label: 'kcal na 100 g (puste pole usuwa wartość)',
    initial: calories === null ? '' : formatQuantity(calories.kcalPer100g),
  };
  const entered = await dialogs.promptOptionalText(prompt, isKcalInput);
  if (entered === null) {
    return;
  }
  const kcalPer100g = toOptionalDecimalPayload(entered);
  await setCalories(decision.ingredient.id, kcalPer100g);
}

async function editPieceWeight(decision: ProductIngredientDecision): Promise<void> {
  const pieceWeight = decision.pieceWeight;
  const prompt = {
    title: `Waga sztuki: ${decision.ingredient.name}`,
    label: 'gramy na sztukę (puste pole usuwa wartość)',
    initial: pieceWeight === null ? '' : formatQuantity(pieceWeight.gramsPerPiece),
  };
  const entered = await dialogs.promptOptionalText(prompt, isPieceWeightInput);
  if (entered === null) {
    return;
  }
  const gramsPerPiece = toOptionalDecimalPayload(entered);
  await setPieceWeight(decision.ingredient.id, gramsPerPiece);
}

async function editDensity(decision: ProductIngredientDecision): Promise<void> {
  const density = decision.density;
  const prompt = {
    title: `Gęstość: ${decision.ingredient.name}`,
    label: 'gramy na mililitr (puste pole usuwa wartość)',
    initial: density === null ? '' : formatQuantity(density.gramsPerMl),
  };
  const entered = await dialogs.promptOptionalText(prompt, isDensityInput);
  if (entered === null) {
    return;
  }
  const gramsPerMl = toOptionalDecimalPayload(entered);
  await setDensity(decision.ingredient.id, gramsPerMl);
}

async function analyzeAgain(): Promise<void> {
  const proposedCount = await analyze();
  const message =
    proposedCount === 0
      ? 'Model nie znalazł nowych tagów.'
      : `Model przypisał tagi: ${proposedCount}.`;
  quasar.notify({ type: 'info', message });
}
</script>
