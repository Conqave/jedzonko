<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 340px">
      <q-card-section>
        <div class="text-h6">Podziel według promocji</div>
        <div class="text-caption text-grey-8">
          Niekupione pozycje trafią na osobne listy sklepów z promocją. Oryginalna lista zostaje.
        </div>
      </q-card-section>
      <q-card-section>
        <q-banner v-if="shops.length === 0" class="bg-grey-3">
          Nie masz ulubionych sklepów. Wybierz je na stronie promocji.
        </q-banner>
        <q-option-group v-else v-model="chosenSlugs" type="checkbox" :options="shopOptions" />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
        <q-btn
          color="primary"
          no-caps
          label="Podziel"
          :disable="chosenSlugs.length === 0"
          @click="onDialogOK(chosenSlugs)"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { computed, ref } from 'vue';
import type { ShopOption } from '../model';

const props = defineProps<{ shops: ShopOption[] }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const chosenSlugs = ref<string[]>(props.shops.map((shop) => shop.slug));

const shopOptions = computed(() =>
  props.shops.map((shop) => ({ label: shop.name, value: shop.slug })),
);
</script>
