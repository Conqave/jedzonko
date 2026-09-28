<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card style="min-width: 320px">
      <q-card-section class="text-h6">Zmień hasło</q-card-section>
      <q-form @submit="submit">
        <q-card-section class="q-gutter-md">
          <q-input
            v-model="currentPassword"
            type="password"
            label="Obecne hasło"
            autocomplete="current-password"
            :rules="[(value: string) => value !== '' || 'Podaj obecne hasło']"
          />
          <q-input
            v-model="newPassword"
            type="password"
            label="Nowe hasło"
            autocomplete="new-password"
            :rules="[
              (value: string) =>
                value.length >= MIN_PASSWORD_LENGTH || `Co najmniej ${MIN_PASSWORD_LENGTH} znaków`,
            ]"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat no-caps label="Anuluj" @click="onDialogCancel" />
          <q-btn type="submit" color="primary" no-caps label="Zmień" :loading="busy" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import { useChangePassword } from '../useChangePassword';

const MIN_PASSWORD_LENGTH = 8;

defineEmits([...useDialogPluginComponent.emits]);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const { busy, change } = useChangePassword();
const currentPassword = ref('');
const newPassword = ref('');

async function submit(): Promise<void> {
  const isChanged = await change(currentPassword.value, newPassword.value);
  if (isChanged) {
    onDialogOK();
  }
}
</script>
