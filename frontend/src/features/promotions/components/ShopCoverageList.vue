<template>
  <q-card v-if="bestShops.length > 0" flat bordered class="bg-green-1 q-mb-md">
    <q-card-section>
      <div class="text-overline text-green-8">
        {{ bestShops.length === 1 ? 'Najlepiej się opłaca' : 'Największe pokrycie' }}
      </div>
      <div class="text-h6">
        {{ bestShopNames }}: {{ bestShops[0]?.matchedQueryCount }} z {{ queries.length }}
        produktów w promocji
      </div>
      <div v-if="bestShops.length > 1" class="text-caption text-grey-8 q-mt-xs">
        Te sklepy mają takie samo pokrycie listy, kolejność nie oznacza przewagi.
      </div>
      <div v-if="bestMissing.length > 0" class="text-caption text-grey-8 q-mt-xs">
        Brak w promocji: {{ bestMissing.join(', ') }}
      </div>
    </q-card-section>
    <q-card-actions>
      <q-btn
        v-for="entry in bestShops"
        :key="entry.shopSlug"
        flat
        dense
        no-caps
        :label="`Strona sklepu: ${entry.shopName}`"
        type="a"
        :href="entry.shopUrl"
        target="_blank"
      />
    </q-card-actions>
  </q-card>

  <q-list bordered separator>
    <q-expansion-item
      v-for="entry in coverage"
      :key="entry.shopSlug"
      :label="entry.shopName"
      :caption="`${entry.matchedQueryCount} z ${queries.length} produktów w promocji`"
    >
      <div
        v-if="findMissingQueries(entry, queries).length > 0"
        class="q-pa-md text-caption text-grey-8"
      >
        Brak w promocji: {{ findMissingQueries(entry, queries).join(', ') }}
      </div>
      <q-list separator>
        <q-item v-for="(offer, index) in entry.offers" :key="index">
          <q-item-section>
            <q-item-label>{{ offer.name }}</q-item-label>
            <q-item-label caption>do {{ offer.validUntil }}</q-item-label>
          </q-item-section>
          <q-item-section side class="text-weight-bold">
            {{ formatPrice(offer.price) }}
          </q-item-section>
        </q-item>
      </q-list>
    </q-expansion-item>
  </q-list>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { findMissingQueries, formatPrice, type ShopCoverage } from '../model';

const props = defineProps<{
  coverage: ShopCoverage[];
  bestShops: ShopCoverage[];
  queries: string[];
}>();

const bestShopNames = computed(() => props.bestShops.map((entry) => entry.shopName).join(', '));

const bestMissing = computed(() => {
  const only = props.bestShops.length === 1 ? props.bestShops[0] : undefined;
  return only === undefined ? [] : findMissingQueries(only, props.queries);
});
</script>
