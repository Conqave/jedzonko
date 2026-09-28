<template>
  <q-form class="row q-col-gutter-sm q-mb-md" @submit="submit">
    <div class="col-12 col-sm-6">
      <q-input
        v-model="username"
        dense
        outlined
        label="Nazwa użytkownika"
        :rules="[(value: string) => value.trim() !== '' || 'Podaj nazwę użytkownika']"
      />
    </div>
    <div class="col-12 col-sm-4">
      <q-btn type="submit" color="primary" label="Dodaj osobę" no-caps :loading="busy" />
    </div>
  </q-form>

  <q-list bordered separator>
    <q-item v-for="member in members" :key="member.userId">
      <q-item-section>{{ member.username }}</q-item-section>
      <q-item-section side>
        <q-btn
          flat
          dense
          round
          color="negative"
          icon="person_remove"
          :aria-label="`Usuń ${member.username}`"
          @click="emit('remove', member)"
        />
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { HouseholdMember } from '../model';

const props = defineProps<{
  members: HouseholdMember[];
  busy: boolean;
  addMember: (username: string) => Promise<boolean>;
}>();

const emit = defineEmits<{ remove: [member: HouseholdMember] }>();

const username = ref('');

async function submit(): Promise<void> {
  const isAdded = await props.addMember(username.value.trim());
  if (isAdded) {
    username.value = '';
  }
}
</script>
