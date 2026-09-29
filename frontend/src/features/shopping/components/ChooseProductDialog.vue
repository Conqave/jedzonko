<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 340px">
      <q-card-section>
        <div class="text-h6">Wybierz produkt</div>
        <div class="text-caption text-grey-8">
          Zamiast „{{ itemName }}” kupisz konkretny produkt.
        </div>
      </q-card-section>
      <q-card-section>
        <ProductPicker v-model="product" :household-id="householdId" :units="units" />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
        <q-btn
          color="primary"
          no-caps
          label="Wybierz"
          :disable="product === null"
          @click="submit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import ProductPicker from '@/features/catalog/components/ProductPicker.vue';
import type { MeasurementUnit, Product } from '@/features/catalog/model';

defineProps<{ itemName: string; householdId: number; units: MeasurementUnit[] }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const product = ref<Product | null>(null);

function submit(): void {
  if (product.value !== null) {
    onDialogOK(product.value.id);
  }
}
</script>
