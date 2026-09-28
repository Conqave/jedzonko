<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 320px">
      <q-card-section class="text-h6">Zdjęcie: {{ item.productName }}</q-card-section>
      <q-card-section class="q-gutter-sm">
        <q-img v-if="item.photoUrl !== null" :src="item.photoUrl" style="max-height: 220px" />
        <div v-else class="text-center text-h2">{{ productEmoji(item.productName) }}</div>
        <q-file
          v-model="photo"
          dense
          outlined
          clearable
          accept="image/jpeg,image/png,image/webp"
          label="Wybierz zdjęcie"
        />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn
          v-if="item.photoUrl !== null"
          flat
          no-caps
          color="negative"
          label="Usuń zdjęcie"
          @click="onDialogOK(null)"
        />
        <q-btn flat no-caps label="Zamknij" @click="onDialogCancel" />
        <q-btn
          color="primary"
          no-caps
          label="Zapisz"
          :disable="photo === null"
          @click="onDialogOK(photo)"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import { productEmoji } from '@/shared/productEmoji';
import type { InventoryItem } from '../model';

defineProps<{ item: InventoryItem }>();

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const photo = ref<File | null>(null);
</script>
