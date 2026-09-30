<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 340px; max-width: 480px">
      <q-card-section>
        <div class="text-h6">Otaguj pozycję</div>
        <div class="text-caption text-grey-8">„{{ itemName }}”</div>
      </q-card-section>
      <q-form @submit="submit">
        <q-card-section class="column q-gutter-y-sm">
          <div class="row items-center q-gutter-x-sm">
            <q-btn
              outline
              no-caps
              color="primary"
              icon="auto_awesome"
              label="Zapytaj Ollamę"
              :loading="isAsking"
              @click="ask"
            >
              <template #loading>
                <q-spinner class="q-mr-sm" />
                Pytam Ollamę...
              </template>
            </q-btn>
            <span v-if="isAsking" class="text-caption text-grey-7">
              Model może być zajęty, to może chwilę potrwać.
            </span>
            <span v-else-if="isUnrecognised" class="text-caption text-grey-7">
              Ollama nie rozpoznała tej pozycji. Wybierz tag ręcznie.
            </span>
          </div>
          <IngredientPicker v-model="ingredient" label="Tag (składnik)" />
          <div class="row q-col-gutter-x-sm">
            <div class="col-6">
              <q-input
                v-model="quantity"
                dense
                outlined
                inputmode="decimal"
                label="Ilość"
                :rules="[(value: string) => isPositiveDecimal(value) || 'Podaj dodatnią liczbę']"
              />
            </div>
            <div class="col-6">
              <q-select
                v-model="unitCode"
                dense
                outlined
                emit-value
                map-options
                option-value="code"
                option-label="name"
                label="Jednostka"
                :options="units"
              />
            </div>
          </div>
          <ProductPicker
            v-model="product"
            :household-id="householdId"
            :units="units"
            label="Produkt do zapasów (opcjonalnie)"
          />
          <div class="text-caption text-grey-7">
            Po zakupie pozycja trafi do zapasów. Bez wybranego produktu trafi do jedynego produktu z
            tym tagiem, przy kilku zapytamy o produkt, a gdy nie ma żadnego, utworzymy produkt o
            nazwie tagu.
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
          <q-btn
            type="submit"
            color="primary"
            no-caps
            label="Zapisz"
            :disable="ingredient === null || isAsking"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import IngredientPicker from '@/features/catalog/components/IngredientPicker.vue';
import ProductPicker from '@/features/catalog/components/ProductPicker.vue';
import type { Ingredient, MeasurementUnit, Product } from '@/features/catalog/model';
import { isPositiveDecimal, toDecimalText } from '@/shared/decimal';
import { formatQuantity } from '@/shared/formatQuantity';
import type {
  ShoppingItemInterpretation,
  ShoppingItemTagRequest,
  ShoppingItemTagging,
} from '../model';

const props = defineProps<{
  itemName: string;
  householdId: number;
  units: MeasurementUnit[];
  initialIngredient: Ingredient | null;
  initialQuantity: string;
  initialUnitCode: string;
  interpret: () => Promise<ShoppingItemInterpretation | null>;
}>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const ingredient = ref<Ingredient | null>(props.initialIngredient);
const quantity = ref(props.initialQuantity);
const unitCode = ref(props.initialUnitCode);
const product = ref<Product | null>(null);
const isAsking = ref(false);
const isUnrecognised = ref(false);

async function ask(): Promise<void> {
  isAsking.value = true;
  isUnrecognised.value = false;
  const interpretation = await props.interpret();
  isAsking.value = false;
  if (interpretation === null) {
    return;
  }
  isUnrecognised.value = interpretation.ingredient === null;
  if (interpretation.ingredient !== null) {
    ingredient.value = interpretation.ingredient;
  }
  if (interpretation.quantity !== null && interpretation.unitCode !== null) {
    quantity.value = formatQuantity(interpretation.quantity);
    unitCode.value = interpretation.unitCode;
  }
}

function submit(): void {
  if (ingredient.value === null) {
    return;
  }
  const tagging: ShoppingItemTagging = {
    ingredientId: ingredient.value.id,
    quantity: toDecimalText(quantity.value),
    unitCode: unitCode.value,
  };
  const request: ShoppingItemTagRequest = {
    tagging,
    productId: product.value === null ? null : product.value.id,
  };
  onDialogOK(request);
}
</script>
