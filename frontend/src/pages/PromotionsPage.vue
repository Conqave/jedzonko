<template>
  <q-page padding>
    <q-tabs v-model="tab" align="left" class="q-mb-md" dense outside-arrows mobile-arrows>
      <q-tab name="favourites" label="Ulubione" no-caps />
      <q-tab name="search" label="Szukaj" no-caps />
      <q-tab name="coverage" label="Gdzie się opłaca" no-caps />
    </q-tabs>

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="favourites" class="q-pa-none">
        <q-banner v-if="store.loaded && !store.hasFavourites" class="bg-grey-3 q-mb-md">
          Nie masz jeszcze ulubionych sklepów. Bez nich wyszukiwanie i porównanie obejmują wszystkie
          sklepy.
        </q-banner>

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
            options-dense
            clearable
            dropdown-icon="expand_more"
            :loading="store.loading || store.saving"
            hint="Zmiany zapisują się automatycznie."
            @filter="filterShops"
            @update:model-value="saveFavourites"
          >
            <template #no-option>
              <q-item>
                <q-item-section class="text-grey">Brak pasujących sklepów.</q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>
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

        <template v-else-if="offers.length > 0">
          <div class="text-caption text-grey-8 q-mb-sm">
            Znaleziono {{ offers.length }} promocji. Strona {{ offerPage }} z {{ offerPageCount }}.
          </div>

          <q-list bordered separator>
            <template v-for="group in offerGroups" :key="group.shop_slug">
              <q-item-label header>{{ group.shop_name }}</q-item-label>
              <q-item v-for="(offer, index) in group.offers" :key="`${group.shop_slug}-${index}`">
                <q-item-section avatar>
                  <q-avatar rounded>
                    <img :src="offer.image_url" :alt="offer.name" />
                  </q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ offer.name }}</q-item-label>
                  <q-item-label caption>
                    <span v-if="offer.product_brand_name">{{ offer.product_brand_name }} · </span>
                    do {{ offer.valid_until }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-item-label class="text-weight-bold">{{
                    formatPrice(offer.price)
                  }}</q-item-label>
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
            </template>
          </q-list>

          <div v-if="offerPageCount > 1" class="row justify-center q-mt-md">
            <q-pagination
              v-model="offerPage"
              :max="offerPageCount"
              :max-pages="7"
              boundary-numbers
            />
          </div>
        </template>
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
          <q-card v-if="topShops.length > 0" flat bordered class="bg-green-1 q-mb-md">
            <q-card-section>
              <div class="text-overline text-green-8">
                {{ topShops.length === 1 ? 'Najlepiej się opłaca' : 'Największe pokrycie' }}
              </div>
              <div class="text-h6">
                {{ topShopNames.join(', ') }} — {{ topShops[0]?.matched_query_count }} z
                {{ comparedItems.length }} produktów w promocji
              </div>
              <div v-if="topShops.length > 1" class="text-caption text-grey-8 q-mt-xs">
                Te sklepy mają takie samo pokrycie listy — kolejność nie oznacza przewagi.
              </div>
              <div v-if="topMissing.length > 0" class="text-caption text-grey-8 q-mt-xs">
                Brak w promocji: {{ topMissing.join(', ') }}
              </div>
            </q-card-section>
            <q-card-actions>
              <q-btn
                v-for="entry in topShops"
                :key="entry.shop_slug"
                flat
                dense
                no-caps
                :label="`Strona sklepu: ${entry.shop_name}`"
                type="a"
                :href="entry.shop_url"
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

interface OfferGroup {
  shop_slug: string;
  shop_name: string;
  offers: PromotionOffer[];
}

function formatPrice(price: string | null): string {
  return price === null ? 'brak ceny' : `${price} zł`;
}

const tab = ref<'favourites' | 'search' | 'coverage'>('favourites');

const favouriteSelection = ref<string[]>([]);
const filteredShops = ref<Shop[]>([]);

const query = ref('');
const searchShops = ref<string[]>([]);
const offers = ref<PromotionOffer[]>([]);
const searching = ref(false);
const searched = ref(false);
const offerPage = ref(1);

const OFFERS_PER_PAGE = 20;

const offerPageCount = computed(() =>
  Math.max(1, Math.ceil(offers.value.length / OFFERS_PER_PAGE)),
);

const offerGroups = computed<OfferGroup[]>(() => {
  const start = (offerPage.value - 1) * OFFERS_PER_PAGE;
  const groups = new Map<string, OfferGroup>();
  for (const offer of offers.value.slice(start, start + OFFERS_PER_PAGE)) {
    const existing = groups.get(offer.shop_slug);
    if (existing === undefined) {
      groups.set(offer.shop_slug, {
        shop_slug: offer.shop_slug,
        shop_name: offer.shop_name,
        offers: [offer],
      });
      continue;
    }
    existing.offers.push(offer);
  }
  return [...groups.values()];
});

const requestedItems = ref<string[]>([]);
const comparedItems = ref<string[]>([]);
const coverageShops = ref<string[]>([]);
const coverage = ref<StorePromotionCoverage[]>([]);
const comparing = ref(false);
const compared = ref(false);

const topShops = computed<StorePromotionCoverage[]>(() => {
  const best = coverage.value[0];
  if (best === undefined || best.matched_query_count === 0) {
    return [];
  }
  return coverage.value.filter((entry) => entry.matched_query_count === best.matched_query_count);
});

const topShopNames = computed(() => topShops.value.map((entry) => entry.shop_name));

const topMissing = computed<string[]>(() => {
  const only = topShops.value.length === 1 ? topShops.value[0] : undefined;
  return only === undefined ? [] : missingFor(only);
});

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
      message: describePromotionError(error),
    });
  }
});

async function saveFavourites(selection: string[]): Promise<void> {
  try {
    await store.saveFavourites(selection);
    quasar.notify({ type: 'positive', message: 'Zapisano ulubione sklepy.' });
  } catch (error) {
    quasar.notify({
      type: 'negative',
      message: describePromotionError(error),
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
    offerPage.value = 1;
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
      message: describePromotionError(error),
    });
  } finally {
    comparing.value = false;
  }
}
</script>
