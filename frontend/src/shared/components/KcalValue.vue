<template>
  <div>
    <span :class="{ 'text-grey-7': !display.isKnown }">
      {{ display.text }}
      <q-badge
        v-if="display.isEstimate"
        outline
        color="grey-8"
        class="q-ml-xs"
        :label="ESTIMATE_LABEL"
      />
      <q-tooltip v-if="display.tooltip !== null">{{ display.tooltip }}</q-tooltip>
    </span>
    <div v-if="display.caption !== null" class="text-caption text-grey-7">
      {{ display.caption }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ESTIMATE_LABEL, type KcalDisplay } from '../calories';

defineProps<{ display: KcalDisplay }>();
</script>
