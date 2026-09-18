<template>
  <q-page padding>
    <q-tabs v-model="tab" align="left" class="q-mb-md">
      <q-tab name="favourites" label="Ulubione sklepy" no-caps />
      <q-tab name="search" label="Szukaj produktu" no-caps />
      <q-tab name="coverage" label="Gdzie się opłaca" no-caps />
    </q-tabs>

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="favourites" class="q-pa-none">
        <q-banner v-if="store.loaded && !store.hasFavourites" class="bg-grey-3 q-mb-md">
          Nie masz jeszcze ulubionych sklepów. Bez nich wyszukiwanie i porównanie obejmują wszystkie
          sklepy.
        </q-banner>

        <q-form class="row q-col-gutter-sm items-start" @submit.prevent="saveFavourites">
          <div class="col-12 col-sm-8">
            <q-select
              v-model="favouriteSelection"
              dense
              outlined
              multiple
              use-chips
              use-input
              emit-value
              map-options
              input-debounce="0"
              label="Ulubione sklepy"
              option-label="name"
              option-value="slug"
              :options="filteredShops"
              :loading="store.loading"
              @filter="filterShops"
            >
              <template #no-option>
                <q-item>
                  <q-item-section class="text-grey">Brak pasujących sklepów.</q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>
          <div class="col-12 col-sm-4">
            <q-btn
              type="submit"
              color="primary"
              label="Zapisz"
              no-caps
              :loading="store.saving"
              :disable="store.loading"
            />
          </div>
        </q-form>
      </q-tab-panel>

      <q-tab-panel name="search" class="q-pa-none">
        <q-form class="row q-col-gutter-sm items-start q-mb-md" @submit.prevent="runSearch">
          <div class="col-12 col-sm-5">
            <q-input v-model="query" dense outlined label="Produkt lub składnik" clearable />
          </div>
          <div class="col-12 col-sm-4">
            <q-select
              v-model="searchShops"
              dense
              outlined
              multiple
              use-chips
              use-input
              emit-value
              map-options
              input-debounce="0"
              label="Zawęź do sklepów (opcjonalnie)"
              option-label="name"
              option-value="slug"
              :options="filteredShops"
              @filter="filterShops"
            />
          </div>
          <div class="col-12 col-sm-3">
            <q-btn type="submit" color="primary" label="Szukaj" :loading="searching" no-caps />
          </div>
        </q-form>

        <div class="q-mb-md">
          <div class="text-caption text-grey-8">{{ scopeCaption }}</div>
          <div v-if="scopeShopNames.length > 0" class="q-gutter-xs q-mt-xs">
            <q-chip v-for="name in scopeShopNames" :key="name" dense square>{{ name }}</q-chip>
          </div>
        </div>

        <q-banner v-if="searched && offers.length === 0 && !searching" class="bg-grey-3">
          Brak promocji dla podanego zapytania.
        </q-banner>

        <q-list v-else-if="offers.length > 0" bordered separator>
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
        <q-form class="row q-col-gutter-sm items-start q-mb-md" @submit.prevent="runCoverage">
          <div class="col-12 col-sm-5">
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
            <q-select
              v-model="coverageShops"
              dense
              outlined
              multiple
              use-chips
              use-input
              emit-value
              map-options
              input-debounce="0"
              label="Zawęź do sklepów (opcjonalnie)"
              option-label="name"
              option-value="slug"
              :options="filteredShops"
              @filter="filterShops"
            />
          </div>
          <div class="col-12 col-sm-3">
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

        <div class="text-caption text-grey-8 q-mb-md">{{ coverageScopeCaption }}</div>

        <q-banner v-if="compared && coverage.length === 0 && !comparing" class="bg-grey-3">
          Żaden sklep nie ma obecnie tych produktów w promocji.
        </q-banner>

        <template v-else-if="coverage.length > 0">
          <q-card v-if="bestShop !== null" flat bordered class="bg-green-1 q-mb-md">
            <q-card-section>
              <div class="text-overline text-green-8">Najlepiej się opłaca</div>
              <div class="text-h6">
                {{ bestShop.shop_name }} — {{ bestShop.matched_query_count }} z
                {{ comparedItems.length }} produktów w promocji
              </div>
              <div v-if="missingFor(bestShop).length > 0" class="text-caption text-grey-8 q-mt-xs">
                Brak w promocji: {{ missingFor(bestShop).join(', ') }}
              </div>
            </q-card-section>
            <q-card-actions>
              <q-btn
                flat
                dense
                no-caps
                label="Strona sklepu"
                type="a"
                :href="bestShop.shop_url"
                target="_blank"
              />
            </q-card-actions>
          </q-card>

          <q-list bordered separator>
            <q-expansion-item
              v-for="entry in coverage"
              :key="entry.shop_slug"
              :label="entry.shop_name"
              :caption="coverageCaption(entry)"
            >
              <div v-if="missingFor(entry).length > 0" class="q-pa-md text-caption text-grey-8">
                Brak w promocji: {{ missingFor(entry).join(', ') }}
              </div>
              <q-list separator>
                <q-item v-for="(offer, index) in entry.offers" :key="index">
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
        </template>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { compareStoreCoverage, searchPromotions } from '@/features/promotions/api';
import { describePromotionError } from '@/features/promotions/errors';
import { usePromotionsStore } from '@/features/promotions/store';
import type { PromotionOffer, Shop, StorePromotionCoverage } from '@/features/promotions/models';

const quasar = useQuasar();
const store = usePromotionsStore();

function formatPrice(price: string | null): string {
  return price === null ? 'brak ceny' : `${price} zł`;
}

const tab = ref<'favourites' | 'search' | 'coverage'>('search');

const favouriteSelection = ref<string[]>([]);
const filteredShops = ref<Shop[]>([]);

const query = ref('');
const searchShops = ref<string[]>([]);
const offers = ref<PromotionOffer[]>([]);
const searching = ref(false);
const searched = ref(false);

const requestedItems = ref<string[]>([]);
const comparedItems = ref<string[]>([]);
const coverageShops = ref<string[]>([]);
const coverage = ref<StorePromotionCoverage[]>([]);
const comparing = ref(false);
const compared = ref(false);

const bestShop = computed<StorePromotionCoverage | null>(() => coverage.value[0] ?? null);

function shopNames(slugs: string[]): string[] {
  return slugs.map((slug) => store.shops.find((shop) => shop.slug === slug)?.name ?? slug);
}

const scopeShopNames = computed(() => {
  if (searchShops.value.length > 0) {
    return shopNames(searchShops.value);
  }
  return store.favourites.map((shop) => shop.name);
});

const scopeCaption = computed(() => {
  if (searchShops.value.length > 0) {
    return 'Wyniki ograniczone do wybranych sklepów:';
  }
  if (store.hasFavourites) {
    return 'Wyniki ograniczone do Twoich ulubionych sklepów:';
  }
  return 'Wyniki obejmują wszystkie sklepy — nie masz ulubionych sklepów.';
});

const coverageScopeCaption = computed(() => {
  if (coverageShops.value.length > 0) {
    return `Porównanie obejmuje: ${shopNames(coverageShops.value).join(', ')}.`;
  }
  if (store.hasFavourites) {
    const names = store.favourites.map((shop) => shop.name).join(', ');
    return `Porównanie obejmuje Twoje ulubione sklepy: ${names}.`;
  }
  return 'Porównanie obejmuje wszystkie sklepy — nie masz ulubionych sklepów.';
});

function missingFor(entry: StorePromotionCoverage): string[] {
  return comparedItems.value.filter((item) => !entry.matched_queries.includes(item));
}

function coverageCaption(entry: StorePromotionCoverage): string {
  return `${entry.matched_query_count} z ${comparedItems.value.length} produktów w promocji`;
}

function filterShops(value: string, update: (callback: () => void) => void): void {
  update(() => {
    const needle = value.toLowerCase();
    filteredShops.value =
      needle === ''
        ? store.shops
        : store.shops.filter((shop) => shop.name.toLowerCase().includes(needle));
  });
}

watch(
  () => store.favouriteSlugs,
  (slugs) => {
    favouriteSelection.value = [...slugs];
  },
  { immediate: true },
);

onMounted(async () => {
  try {
    await store.load();
    filteredShops.value = store.shops;
  } catch (error) {
    quasar.notify({
      type: 'negative',
      message: describePromotionError(error, 'Nie udało się pobrać listy sklepów.'),
    });
  }
});

async function saveFavourites(): Promise<void> {
  try {
    await store.saveFavourites(favouriteSelection.value);
    quasar.notify({ type: 'positive', message: 'Zapisano ulubione sklepy.' });
  } catch (error) {
    quasar.notify({
      type: 'negative',
      message: describePromotionError(error, 'Nie udało się zapisać ulubionych sklepów.'),
    });
  }
}

async function runSearch(): Promise<void> {
  if (query.value.trim() === '') {
    return;
  }
  searching.value = true;
  try {
    offers.value = await searchPromotions(query.value.trim(), searchShops.value);
    searched.value = true;
  } catch (error) {
    quasar.notify({ type: 'negative', message: describePromotionError(error) });
  } finally {
    searching.value = false;
  }
}

async function runCoverage(): Promise<void> {
  comparing.value = true;
  const items = [...requestedItems.value];
  try {
    coverage.value = await compareStoreCoverage(items, coverageShops.value);
    comparedItems.value = items;
    compared.value = true;
  } catch (error) {
    quasar.notify({
      type: 'negative',
      message: describePromotionError(error, 'Nie udało się porównać sklepów.'),
    });
  } finally {
    comparing.value = false;
  }
}
</script>
