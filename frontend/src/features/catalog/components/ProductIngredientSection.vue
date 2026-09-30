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
      <q-item v-for="tag in groups.tags" :key="tag.ingredient.id">
        <q-item-section>
          <q-item-label>{{ tag.ingredient.name }}</q-item-label>
          <TagFactCaption :text="describeTagCalories(tag.calories)" :source="tag.calories" />
          <TagFactCaption
            :text="describeTagPieceWeight(tag.pieceWeight)"
            :source="tag.pieceWeight"
          />
          <TagFactCaption :text="describeTagDensity(tag.density)" :source="tag.density" />
        </q-item-section>
        <q-item-section side>
          <div class="row no-wrap q-gutter-xs">
            <q-btn
              flat
              dense
              round
              color="deep-orange"
              icon="local_fire_department"
              :aria-label="`Kalorie ${tag.ingredient.name}`"
              :loading="busy"
              @click="editCalories(tag)"
            />
            <q-btn
              flat
              dense
              round
              color="brown"
              icon="scale"
              :aria-label="`Waga sztuki ${tag.ingredient.name}`"
              :loading="busy"
              @click="editPieceWeight(tag)"
            />
            <q-btn
              flat
              dense
              round
              color="blue"
              icon="water_drop"
              :aria-label="`Gęstość ${tag.ingredient.name}`"
              :loading="busy"
              @click="editDensity(tag)"
            />
            <q-btn
              flat
              dense
              round
              color="negative"
              icon="close"
              :aria-label="`Usuń tag ${tag.ingredient.name}`"
              :loading="busy"
              @click="reject(tag.ingredient.id)"
            />
          </div>
        </q-item-section>
      </q-item>
      <q-item v-if="groups.tags.length === 0">
        <q-item-section class="text-grey">Brak tagów.</q-item-section>
      </q-item>
    </q-list>

    <template v-if="groups.proposals.length > 0">
      <div class="text-subtitle2 q-px-md q-pt-md">Do decyzji</div>
      <q-list separator>
        <q-item v-for="proposal in groups.proposals" :key="proposal.ingredient.id">
          <q-item-section>
            <q-item-label>{{ proposal.ingredient.name }}</q-item-label>
            <q-item-label v-if="proposal.modelName !== null" caption>
              Propozycja modelu {{ proposal.modelName }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <div class="row no-wrap q-gutter-xs">
              <q-btn
                flat
                dense
                round
                color="positive"
                icon="check"
                :aria-label="`Potwierdź ${proposal.ingredient.name}`"
                :loading="busy"
                @click="confirm(proposal.ingredient.id)"
              />
              <q-btn
                flat
                dense
                round
                color="negative"
                icon="close"
                :aria-label="`Odrzuć ${proposal.ingredient.name}`"
                :loading="busy"
                @click="reject(proposal.ingredient.id)"
              />
              <q-btn
                flat
                dense
                round
                color="grey-8"
                icon="delete_forever"
                :aria-label="`Usuń na zawsze ${proposal.ingredient.name}`"
                :loading="busy"
                @click="forgetProposal(proposal)"
              />
            </div>
          </q-item-section>
        </q-item>
      </q-list>
    </template>

    <q-expansion-item
      v-if="groups.rejections.length > 0"
      dense
      icon="block"
      :label="`Odrzucone (${groups.rejections.length})`"
      caption="Model nie zaproponuje ich ponownie."
    >
      <q-list separator>
        <q-item v-for="rejection in groups.rejections" :key="rejection.ingredient.id">
          <q-item-section>
            <q-item-label>{{ rejection.ingredient.name }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn
              flat
              dense
              no-caps
              color="negative"
              icon="delete_forever"
              label="Usuń na zawsze"
              :loading="busy"
              @click="forgetRejection(rejection)"
            />
          </q-item-section>
        </q-item>
      </q-list>
      <div class="row justify-end q-pa-sm">
        <q-btn
          flat
          no-caps
          color="negative"
          icon="delete_sweep"
          label="Usuń wszystkie odrzucone"
          :loading="busy"
          @click="forgetAllRejections"
        />
      </div>
    </q-expansion-item>

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
} from '../model';
import { useProductDecisions } from '../useProductDecisions';
import IngredientPicker from './IngredientPicker.vue';
import TagFactCaption from './TagFactCaption.vue';

const props = defineProps<{ product: Product }>();

const quasar = useQuasar();
const dialogs = useDialogs();
const {
  groups,
  busy,
  isAnalyzing,
  confirm,
  reject,
  forget,
  forgetRejections,
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

const MAY_BE_PROPOSED_AGAIN = 'Ollama może ponownie zaproponować ten tag przy kolejnej analizie.';

async function forgetProposal(proposal: ProductIngredientDecision): Promise<void> {
  const name = proposal.ingredient.name;
  const message = `Propozycja tagu „${name}” zniknie bez zapamiętania decyzji. ${MAY_BE_PROPOSED_AGAIN} Aby model jej nie powtarzał, odrzuć ją zamiast usuwać.`;
  const isConfirmed = await dialogs.confirm('Usunąć propozycję na zawsze?', message);
  if (isConfirmed) {
    await forget(proposal.ingredient.id);
  }
}

async function forgetRejection(rejection: ProductIngredientDecision): Promise<void> {
  const name = rejection.ingredient.name;
  const message = `Odrzucenie tagu „${name}” zostanie usunięte. ${MAY_BE_PROPOSED_AGAIN}`;
  const isConfirmed = await dialogs.confirm('Usunąć odrzucenie na zawsze?', message);
  if (isConfirmed) {
    await forget(rejection.ingredient.id);
  }
}

async function forgetAllRejections(): Promise<void> {
  const count = groups.value.rejections.length;
  const message = `Odrzucone tagi (${count}) zostaną usunięte. Ollama może ponownie zaproponować każdy z nich przy kolejnej analizie.`;
  const isConfirmed = await dialogs.confirm('Usunąć wszystkie odrzucone?', message);
  if (isConfirmed) {
    await forgetRejections();
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
