<template>
  <q-page class="flex flex-center">
    <q-card flat bordered style="width: 320px">
      <q-card-section>
        <div class="text-h6">Zaloguj się</div>
      </q-card-section>
      <q-form @submit="submit">
        <q-card-section class="q-gutter-md">
          <q-input
            v-model="username"
            label="Login"
            autocomplete="username"
            :rules="[(value: string) => value !== '' || 'Podaj login']"
          />
          <q-input
            v-model="password"
            type="password"
            label="Hasło"
            autocomplete="current-password"
            :rules="[(value: string) => value !== '' || 'Podaj hasło']"
          />
        </q-card-section>
        <q-card-actions>
          <q-btn
            type="submit"
            no-caps
            color="primary"
            class="full-width"
            label="Zaloguj"
            :loading="busy"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ACCOUNT_ERROR_MESSAGES } from '@/features/accounts/errors';
import { useAccountStore } from '@/features/accounts/store';
import { useApiAction } from '@/shared/useApiAction';

const username = ref('');
const password = ref('');

const accounts = useAccountStore();
const router = useRouter();
const route = useRoute();
const { busy, run } = useApiAction(ACCOUNT_ERROR_MESSAGES);

async function submit(): Promise<void> {
  const isSignedIn = await run(() => accounts.signIn(username.value, password.value));
  if (!isSignedIn) {
    return;
  }
  const redirect = route.query.redirect;
  const target = typeof redirect === 'string' ? redirect : { name: 'home' };
  await router.push(target);
}
</script>
