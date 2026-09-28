<template>
  <q-list bordered separator>
    <q-item v-for="household in households" :key="household.id">
      <q-item-section>
        <q-item-label>{{ household.name }}</q-item-label>
        <q-item-label caption>
          Można przywrócić do {{ household.purgeAfter.toLocaleString('pl-PL') }}
        </q-item-label>
      </q-item-section>
      <q-item-section side>
        <q-btn
          flat
          no-caps
          color="primary"
          icon="restore"
          label="Przywróć"
          @click="emit('restore', household.id)"
        />
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import type { DeletedHousehold } from '../model';

defineProps<{ households: DeletedHousehold[] }>();

const emit = defineEmits<{ restore: [householdId: number] }>();
</script>
