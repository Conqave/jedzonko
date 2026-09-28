<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 360px">
      <q-card-section>
        <div class="text-h6">{{ product.name }}</div>
        <div class="text-caption text-grey-8">
          Składnik łączy produkt z przepisami i listą zakupów.
        </div>
      </q-card-section>

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

      <q-card-actions align="right">
        <q-btn flat no-caps label="Zamknij" @click="onDialogOK" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
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

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK } = useDialogPluginComponent();
const { decisions, busy, confirm, reject } = useProductDecisions(props.product.id);
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
</script>
