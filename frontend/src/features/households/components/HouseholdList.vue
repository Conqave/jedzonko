<template>
  <q-list bordered separator>
    <q-item
      v-for="household in households"
      :key="household.id"
      clickable
      :active="household.id === selectedId"
      active-class="bg-blue-1"
      @click="emit('select', household.id)"
    >
      <q-item-section>
        <q-item-label>{{ household.name }}</q-item-label>
        <q-item-label caption>Osoby: {{ household.memberCount }}</q-item-label>
      </q-item-section>
      <q-item-section side>
        <div class="row items-center no-wrap q-gutter-xs">
          <q-icon v-if="household.id === selectedId" name="check_circle" color="primary" />
          <q-btn flat dense round icon="more_vert" aria-label="Opcje domu" @click.stop>
            <q-menu>
              <q-list style="min-width: 180px">
                <q-item v-close-popup clickable @click="emit('rename', household)">
                  <q-item-section avatar><q-icon name="edit" /></q-item-section>
                  <q-item-section>Zmień nazwę</q-item-section>
                </q-item>
                <q-item
                  v-close-popup
                  clickable
                  class="text-negative"
                  @click="emit('remove', household)"
                >
                  <q-item-section avatar><q-icon name="delete" color="negative" /></q-item-section>
                  <q-item-section>Usuń dom</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import type { Household } from '../model';

defineProps<{ households: Household[]; selectedId: number | null }>();

const emit = defineEmits<{
  select: [householdId: number];
  rename: [household: Household];
  remove: [household: Household];
}>();
</script>
