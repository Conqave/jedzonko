<template>
  <q-dialog ref="dialogRef" persistent @hide="onDialogHide">
    <q-card style="min-width: 300px; max-width: 480px">
      <q-card-section>
        <div class="text-h6">Który produkt kupiono?</div>
        <div class="text-caption text-grey-8">
          Kilka produktów ma tag „{{ itemName }}”. Wybierz ten, który trafi do zapasów.
        </div>
      </q-card-section>
      <q-card-section>
        <q-option-group v-model="productId" type="radio" :options="options" />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
        <q-btn
          color="primary"
          no-caps
          label="Wybierz"
          :disable="productId === null"
          @click="submit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { computed, ref } from 'vue';
import type { Product } from '@/features/catalog/model';

const props = defineProps<{ itemName: string; products: Product[] }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const productId = ref<number | null>(null);
const options = computed(() =>
  props.products.map((product) => ({ label: product.name, value: product.id })),
);

function submit(): void {
  if (productId.value !== null) {
    onDialogOK(productId.value);
  }
}
</script>
