<template>
  <q-page padding>
    <q-tabs v-model="tab" align="left" class="q-mb-md">
      <q-tab name="search" label="Szukaj produktu" no-caps />
      <q-tab name="coverage" label="Porównaj sklepy" no-caps />
    </q-tabs>

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="search" class="q-pa-none">
        <q-form class="row q-col-gutter-sm q-mb-md" @submit.prevent="runSearch">
          <div class="col-12 col-sm-8">
            <q-input v-model="query" dense outlined label="Produkt lub składnik" clearable />
          </div>
          <div class="col-12 col-sm-4">
            <q-btn type="submit" color="primary" label="Szukaj" :loading="searching" no-caps />
          </div>
        </q-form>

        <q-banner v-if="searched && offers.length === 0 && !searching" class="bg-grey-3">
          Brak promocji dla podanego zapytania.
        </q-banner>

        <q-list v-else bordered separator>
          <q-item v-for="(offer, index) in offers" :key="index">
            <q-item-section avatar>
              <q-avatar rounded>
                <img :src="offer.image_url" :alt="offer.name" />
              </q-avatar>
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ offer.name }}</q-item-label>
              <q-item-label caption>
                {{ offer.shop_name }}
                <span v-if="offer.product_brand_name"> · {{ offer.product_brand_name }}</span>
                · do {{ offer.valid_until }}
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-item-label class="text-weight-bold">{{ formatPrice(offer.price) }}</q-item-label>
              <q-btn
                flat
                dense
                no-caps
                size="sm"
                label="Gazetka"
                type="a"
                :href="offer.leaflet_url"
                target="_blank"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </q-tab-panel>

      <q-tab-panel name="coverage" class="q-pa-none">
        <q-form class="row q-col-gutter-sm q-mb-md" @submit.prevent="runCoverage">
          <div class="col-12 col-sm-8">
            <q-select
              v-model="requestedItems"
              dense
              outlined
              multiple
              use-input
              use-chips
              hide-dropdown-icon
              new-value-mode="add-unique"
              label="Lista produktów"
              :options="[]"
            />
          </div>
          <div class="col-12 col-sm-4">
            <q-btn
              type="submit"
              color="primary"
              label="Porównaj"
              :loading="comparing"
              :disable="requestedItems.length === 0"
              no-caps
            />
          </div>
        </q-form>

        <q-banner v-if="compared && coverage.length === 0 && !comparing" class="bg-grey-3">
          Żaden sklep nie ma obecnie tych produktów w promocji.
        </q-banner>

        <q-list v-else bordered separator>
          <q-expansion-item
            v-for="store in coverage"
            :key="store.shop_name"
            :label="store.shop_name"
            :caption="`${store.matched_query_count} z ${requestedItems.length} produktów w promocji`"
          >
            <q-list separator>
              <q-item v-for="(offer, index) in store.offers" :key="index">
                <q-item-section>
                  <q-item-label>{{ offer.name }}</q-item-label>
                  <q-item-label caption>do {{ offer.valid_until }}</q-item-label>
                </q-item-section>
                <q-item-section side class="text-weight-bold">
                  {{ formatPrice(offer.price) }}
                </q-item-section>
              </q-item>
            </q-list>
          </q-expansion-item>
        </q-list>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { compareStoreCoverage, searchPromotions } from '@/features/promotions/api';
import { describePromotionError } from '@/features/promotions/errors';
import type { PromotionOffer, StorePromotionCoverage } from '@/features/promotions/models';

const quasar = useQuasar();

function formatPrice(price: string | null): string {
  return price === null ? 'brak ceny' : `${price} zł`;
}

const tab = ref<'search' | 'coverage'>('search');

const query = ref('');
const offers = ref<PromotionOffer[]>([]);
const searching = ref(false);
const searched = ref(false);

const requestedItems = ref<string[]>([]);
const coverage = ref<StorePromotionCoverage[]>([]);
const comparing = ref(false);
const compared = ref(false);

async function runSearch(): Promise<void> {
  if (query.value.trim() === '') {
    return;
  }
  searching.value = true;
  try {
    offers.value = await searchPromotions(query.value.trim());
    searched.value = true;
  } catch (error) {
    quasar.notify({ type: 'negative', message: describePromotionError(error) });
  } finally {
    searching.value = false;
  }
}

async function runCoverage(): Promise<void> {
  comparing.value = true;
  try {
    coverage.value = await compareStoreCoverage(requestedItems.value);
    compared.value = true;
  } catch (error) {
    quasar.notify({ type: 'negative', message: describePromotionError(error) });
  } finally {
    comparing.value = false;
  }
}
</script>
