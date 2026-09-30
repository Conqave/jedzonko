<template>
  <q-item-label caption>
    {{ text }}
    <template v-if="source !== null && source.referenceUrl !== null">
      ·
      <a :href="source.referenceUrl" target="_blank" rel="noopener">źródło</a>
    </template>
    <template v-else-if="source !== null">· wpisane ręcznie</template>
  </q-item-label>
</template>

<script setup lang="ts">
import type { TagFactSource } from '../model';

defineProps<{ text: string; source: TagFactSource | null }>();
</script>
