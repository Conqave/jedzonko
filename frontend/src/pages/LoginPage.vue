<template>
  <q-page class="flex flex-center">
    <q-card flat bordered style="width: 320px">
      <q-card-section>
        <div class="text-h6">Zaloguj się</div>
      </q-card-section>
      <q-form @submit.prevent="submit">
        <q-card-section class="q-gutter-md">
          <q-input
            v-model="username"
            label="Login"
            autocomplete="username"
            :rules="[(value) => !!value || 'Podaj login']"
          />
          <q-input
            v-model="password"
            type="password"
            label="Hasło"
            autocomplete="current-password"
            :rules="[(value) => !!value || 'Podaj hasło']"
          />
        </q-card-section>
        <q-card-actions>
          <q-btn type="submit" color="primary" class="full-width" label="Zaloguj" :loading="busy" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import { useAccountStore } from '@/features/accounts/store';

const username = ref('');
const password = ref('');
const busy = ref(false);

const accounts = useAccountStore();
const router = useRouter();
const route = useRoute();
const quasar = useQuasar();

async function submit(): Promise<void> {
  busy.value = true;
  try {
    await accounts.signIn(username.value, password.value);
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : null;
    await (redirect ? router.push(redirect) : router.push({ name: 'home' }));
  } catch {
    quasar.notify({ type: 'negative', message: 'Nieprawidłowy login lub hasło.' });
  } finally {
    busy.value = false;
  }
}
</script>
