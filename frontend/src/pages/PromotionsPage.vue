<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Promocje i sklepy</div>
    <q-tabs v-model="tab" align="left" class="q-mb-md" dense outside-arrows mobile-arrows>
      <q-tab name="favourites" label="Ulubione" no-caps />
      <q-tab name="search" label="Szukaj" no-caps />
      <q-tab name="coverage" label="Gdzie się opłaca" no-caps />
    </q-tabs>

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="favourites" class="q-pa-none">
        <q-banner v-if="isLoaded && favouriteSlugs.length === 0" class="bg-grey-3 q-mb-md">
          Nie masz jeszcze ulubionych sklepów. Bez nich wyszukiwanie i porównanie obejmują wszystkie
          sklepy.
        </q-banner>
        <ShopSelect
          :model-value="favouriteSlugs"
          :shops="shops"
          :busy="isFavouriteBusy"
          label="Ulubione sklepy"
          hint="Zmiany zapisują się automatycznie."
          @update:model-value="updateFavourites"
        />
      </q-tab-panel>

      <q-tab-panel name="search" class="q-pa-none">
        <q-form class="row q-col-gutter-sm items-start q-mb-md" @submit="runSearch">
          <div class="col-12 col-sm-5">
            <q-input v-model="query" dense outlined clearable label="Produkt lub składnik" />
          </div>
          <div class="col-12 col-sm-4">
            <ShopSelect
              v-model="searchShops"
              :shops="shops"
              label="Zawęź do sklepów (opcjonalnie)"
            />
          </div>
          <div class="col-12 col-sm-3">
            <q-btn type="submit" color="primary" label="Szukaj" no-caps :loading="isSearching" />
          </div>
        </q-form>

        <div class="text-caption text-grey-8 q-mb-md">{{ describeScope(searchShops) }}</div>

        <q-banner v-if="hasSearched && offers.length === 0 && !isSearching" class="bg-grey-3">
          Brak promocji dla podanego zapytania.
        </q-banner>
        <template v-else-if="offers.length > 0">
          <div class="text-caption text-grey-8 q-mb-sm">
            Znaleziono {{ offers.length }} promocji. Strona {{ page }} z {{ pageCount }}.
          </div>
          <OfferGroupList :groups="pageGroups" />
          <div v-if="pageCount > 1" class="row justify-center q-mt-md">
            <q-pagination v-model="page" :max="pageCount" :max-pages="7" boundary-numbers />
          </div>
        </template>
      </q-tab-panel>

      <q-tab-panel name="coverage" class="q-pa-none">
        <q-form class="row q-col-gutter-sm items-start q-mb-md" @submit="runCoverage">
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
            <ShopSelect
              v-model="coverageShops"
              :shops="shops"
              label="Zawęź do sklepów (opcjonalnie)"
            />
          </div>
          <div class="col-12 col-sm-3">
            <q-btn
              type="submit"
              color="primary"
              label="Porównaj"
              no-caps
              :loading="isComparing"
              :disable="requestedItems.length === 0"
            />
          </div>
        </q-form>

        <div class="text-caption text-grey-8 q-mb-md">{{ describeScope(coverageShops) }}</div>

        <q-banner v-if="hasCompared && coverage.length === 0 && !isComparing" class="bg-grey-3">
          Żaden sklep nie ma obecnie tych produktów w promocji.
        </q-banner>
        <ShopCoverageList
          v-else-if="coverage.length > 0"
          :coverage="coverage"
          :best-shops="bestShops"
          :queries="comparedQueries"
        />
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import OfferGroupList from '@/features/promotions/components/OfferGroupList.vue';
import ShopCoverageList from '@/features/promotions/components/ShopCoverageList.vue';
import ShopSelect from '@/features/promotions/components/ShopSelect.vue';
import { useFavouriteShops } from '@/features/promotions/useFavouriteShops';
import { useOfferSearch } from '@/features/promotions/useOfferSearch';
import { useShopCoverage } from '@/features/promotions/useShopCoverage';
import { useDialogs } from '@/shared/useDialogs';

const tab = ref<'favourites' | 'search' | 'coverage'>('favourites');
const query = ref('');
const searchShops = ref<string[]>([]);
const requestedItems = ref<string[]>([]);
const coverageShops = ref<string[]>([]);

const dialogs = useDialogs();
const {
  shops,
  favouriteSlugs,
  favouriteShops,
  isLoaded,
  busy: isFavouriteBusy,
  findShopNames,
  load,
  saveFavourites,
} = useFavouriteShops();
const {
  offers,
  page,
  pageCount,
  pageGroups,
  hasSearched,
  busy: isSearching,
  search,
} = useOfferSearch();
const {
  coverage,
  comparedQueries,
  bestShops,
  hasCompared,
  busy: isComparing,
  compare,
} = useShopCoverage();

function describeScope(chosenSlugs: string[]): string {
  if (chosenSlugs.length > 0) {
    const names = findShopNames(chosenSlugs);
    return `Obejmuje wybrane sklepy: ${names.join(', ')}.`;
  }
  if (favouriteShops.value.length > 0) {
    const names = favouriteShops.value.map((shop) => shop.name);
    return `Obejmuje Twoje ulubione sklepy: ${names.join(', ')}.`;
  }
  return 'Obejmuje wszystkie sklepy, bo nie masz ulubionych sklepów.';
}

async function updateFavourites(slugs: string[]): Promise<void> {
  const isSaved = await saveFavourites(slugs);
  if (isSaved) {
    dialogs.notifySuccess('Zapisano ulubione sklepy.');
  }
}

async function runSearch(): Promise<void> {
  const trimmed = query.value.trim();
  if (trimmed === '') {
    return;
  }
  await search(trimmed, searchShops.value);
}

async function runCoverage(): Promise<void> {
  await compare(requestedItems.value, coverageShops.value);
}

onMounted(load);
</script>
