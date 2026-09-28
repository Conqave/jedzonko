<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Zakupy</div>
    <q-banner v-if="households.selectedId === null" class="bg-grey-3">
      Wybierz gospodarstwo domowe, aby zobaczyć listy zakupów.
    </q-banner>

    <template v-else>
      <div class="row q-col-gutter-sm items-start q-mb-md">
        <div class="col-12 col-sm-7 col-md-6 shopping-list-toolbar">
          <q-select
            v-model="selectedListId"
            dense
            outlined
            emit-value
            map-options
            option-value="id"
            :options="listOptions"
            label="Lista"
            :loading="loadingLists"
            @update:model-value="loadItems"
          />
          <q-btn
            v-if="selectedListId !== null"
            flat
            round
            icon="more_vert"
            aria-label="Opcje listy"
          >
            <q-menu>
              <q-list style="min-width: 220px">
                <q-item clickable v-close-popup @click="openRenameList">
                  <q-item-section avatar><q-icon name="edit" /></q-item-section>
                  <q-item-section>Zmień nazwę</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="openCreateList">
                  <q-item-section avatar><q-icon name="add" /></q-item-section>
                  <q-item-section>Utwórz nową listę</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="runSynchronize">
                  <q-item-section avatar><q-icon name="sync" /></q-item-section>
                  <q-item-section>Uzupełnij minimalne zapasy</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="openPromotionSplit">
                  <q-item-section avatar><q-icon name="local_offer" /></q-item-section>
                  <q-item-section>Porównaj ceny i promocje</q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable v-close-popup class="text-negative" @click="confirmDeleteList">
                  <q-item-section avatar><q-icon name="delete" color="negative" /></q-item-section>
                  <q-item-section>Usuń listę</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
      </div>

      <q-form v-if="!advancedAdd" class="row q-col-gutter-sm q-mb-md" @submit.prevent="submitItem">
        <div class="col">
          <q-input
            v-model="form.freeText"
            dense
            outlined
            label="Dodaj produkt…"
            placeholder="np. 2 litry mleka"
          />
        </div>
        <div class="col-auto">
          <q-btn
            type="submit"
            color="primary"
            icon="add"
            no-caps
            aria-label="Dodaj pozycję"
            :loading="savingItem"
            :disable="selectedListId === null"
          />
        </div>
        <div class="col-auto flex items-center">
          <q-btn flat dense no-caps label="Opcje zaawansowane" @click="advancedAdd = true" />
        </div>
      </q-form>

      <q-form v-else class="row q-col-gutter-sm q-mb-md" @submit.prevent="submitItem">
        <div class="col-12">
          <q-btn
            flat
            dense
            no-caps
            icon="arrow_back"
            label="Proste dodawanie"
            @click="advancedAdd = false"
          />
        </div>
        <div class="col-12 col-sm-3">
          <q-select
            v-model="itemMode"
            dense
            outlined
            emit-value
            map-options
            label="Rodzaj pozycji"
            :options="[
              { label: 'Produkt gospodarstwa', value: 'product' },
              { label: 'Tekst własny', value: 'free_text' },
            ]"
          />
        </div>
        <div class="col-12 col-sm-4">
          <product-picker
            v-if="itemMode === 'product' && households.selectedId !== null"
            v-model="form.product"
            :household-id="households.selectedId"
            :units="units"
          />
          <q-input v-else v-model="form.freeText" dense outlined label="Pozycja" />
        </div>
        <div class="col-6 col-sm-2">
          <q-input
            v-model="form.quantity"
            dense
            outlined
            label="Ilość"
            :rules="[(value) => !!value || 'Podaj ilość']"
          />
        </div>
        <div class="col-6 col-sm-2">
          <q-select
            v-model="form.unitCode"
            dense
            outlined
            clearable
            emit-value
            map-options
            option-value="code"
            option-label="name"
            label="Jednostka"
            :options="units"
          />
        </div>
        <div class="col-12 col-sm-1">
          <q-btn
            type="submit"
            color="primary"
            icon="add"
            no-caps
            aria-label="Dodaj pozycję"
            :loading="savingItem"
            :disable="selectedListId === null"
          />
        </div>
      </q-form>

      <q-banner v-if="!loadingItems && items.length === 0" class="bg-grey-3">
        Lista jest pusta.
      </q-banner>
      <div v-if="selectedReanalysisIds.length > 0" class="row items-center q-gutter-sm q-mb-sm">
        <span class="text-body2">Zaznaczono: {{ selectedReanalysisIds.length }}</span>
        <q-btn
          color="primary"
          no-caps
          icon="refresh"
          label="Ponów analizę zaznaczonych"
          :loading="reanalyzingSelected"
          @click="reanalyzeSelected"
        />
        <q-btn flat no-caps label="Wyczyść zaznaczenie" @click="selectedReanalysisIds = []" />
      </div>
      <div
        v-else-if="reanalysisSelectionMode && pendingItems.length > 0"
        class="row justify-end q-mb-sm"
      >
        <q-btn flat dense no-caps label="Anuluj wybór" @click="reanalysisSelectionMode = false" />
      </div>
      <div v-else-if="pendingItems.length > 0" class="row justify-end q-mb-sm">
        <q-btn
          flat
          dense
          no-caps
          icon="checklist"
          label="Wybierz do analizy"
          @click="reanalysisSelectionMode = true"
        />
      </div>
      <q-list v-if="!loadingItems && items.length > 0" bordered separator>
        <q-item class="shopping-row shopping-row-header bg-grey-2 text-caption text-grey-8">
          <q-item-section>Pozycja</q-item-section>
          <q-item-section side>Ilość</q-item-section>
          <q-item-section side class="shopping-tags-column">Tagi</q-item-section>
          <q-item-section side class="shopping-item-actions" />
        </q-item>
        <q-item
          v-for="item in pendingItems"
          :key="item.id ?? `pending-${item.free_text}`"
          class="shopping-row"
        >
          <q-item-section side top>
            <q-checkbox
              :model-value="item.is_purchased"
              @update:model-value="togglePurchased(item)"
            />
          </q-item-section>
          <q-item-section v-if="reanalysisSelectionMode" side top>
            <q-checkbox
              :model-value="item.id !== null && selectedReanalysisIds.includes(item.id)"
              :disable="item.id === null"
              :aria-label="`Zaznacz do ponownej analizy: ${item.product_name ?? item.free_text ?? ''}`"
              @update:model-value="toggleReanalysisSelection(item)"
            />
          </q-item-section>
          <q-item-section class="shopping-product-column">
            <q-item-label :class="item.is_purchased ? 'text-strike text-grey' : ''">
              {{ item.product_name ?? item.free_text }}
            </q-item-label>
          </q-item-section>
          <q-item-section side class="shopping-quantity-column">
            {{ formatQuantity(item.quantity) }} {{ item.unit_code ?? '' }}
          </q-item-section>
          <q-item-section side class="shopping-tags-column">
            <div v-if="item.tag_names.length > 0" class="row justify-end q-gutter-xs">
              <q-chip
                v-for="tag in item.tag_names"
                :key="tag"
                dense
                square
                color="blue-1"
                text-color="primary"
                >{{ tag }}</q-chip
              >
            </div>
            <span v-else class="text-grey-6">—</span>
          </q-item-section>
          <q-item-section side top class="shopping-item-actions">
            <q-btn flat dense round icon="more_vert" aria-label="Więcej">
              <q-menu>
                <q-list style="min-width: 150px">
                  <q-item
                    clickable
                    v-close-popup
                    class="text-negative"
                    @click="confirmDelete(item)"
                  >
                    <q-item-section avatar
                      ><q-icon name="delete" color="negative"
                    /></q-item-section>
                    <q-item-section>Usuń pozycję</q-item-section>
                  </q-item>
                  <q-item clickable v-close-popup @click="reanalyzeTag(item)">
                    <q-item-section avatar
                      ><q-icon name="refresh" color="primary"
                    /></q-item-section>
                    <q-item-section>Ponów analizę tagu</q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </q-item-section>
        </q-item>
        <q-expansion-item
          v-if="purchasedItems.length > 0"
          icon="check_circle"
          :label="`Kupione (${purchasedItems.length})`"
          header-class="text-grey-8"
        >
          <div class="q-px-md q-pt-sm text-caption text-grey-7">
            Kupione produkty zostały dodane do zapasów automatycznie.
          </div>
          <q-item v-for="item in purchasedItems" :key="item.id ?? `bought-${item.free_text}`">
            <q-item-section side top>
              <q-checkbox
                :model-value="item.is_purchased"
                @update:model-value="togglePurchased(item)"
              />
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-strike text-grey">{{
                item.product_name ?? item.free_text
              }}</q-item-label>
              <q-item-label caption
                >{{ formatQuantity(item.quantity) }} {{ item.unit_code ?? '' }}</q-item-label
              >
              <div v-if="item.tag_names.length > 0" class="row q-gutter-xs q-mt-xs">
                <q-chip
                  v-for="tag in item.tag_names"
                  :key="tag"
                  dense
                  square
                  color="grey-3"
                  text-color="grey-8"
                >
                  {{ tag }}
                </q-chip>
              </div>
            </q-item-section>
          </q-item>
        </q-expansion-item>
      </q-list>
    </template>

    <q-dialog v-model="renameListDialogOpen">
      <q-card style="min-width: 320px; max-width: 90vw">
        <q-card-section class="text-h6">Zmień nazwę listy</q-card-section>
        <q-card-section>
          <q-input
            v-model="renameListName"
            autofocus
            outlined
            label="Nazwa listy"
            @keyup.enter="submitRenameList"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Anuluj" no-caps />
          <q-btn
            color="primary"
            label="Zapisz"
            no-caps
            :loading="renamingList"
            :disable="renameListName.trim().length === 0"
            @click="submitRenameList"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="createListDialogOpen">
      <q-card style="min-width: 320px">
        <q-card-section class="text-h6">Nowa lista zakupów</q-card-section>
        <q-form @submit.prevent="submitCreateList">
          <q-card-section>
            <q-input
              v-model="newListName"
              autofocus
              dense
              outlined
              label="Nazwa"
              :rules="[(value) => !!value || 'Podaj nazwę']"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat label="Anuluj" no-caps />
            <q-btn type="submit" color="primary" label="Utwórz" no-caps :loading="creatingList" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="promotionSplitDialogOpen">
      <q-card style="width: min(680px, 95vw); max-width: 680px">
        <q-card-section class="text-h6">Podziel zakupy według promocji</q-card-section>
        <q-card-section class="q-pt-none">
          <div class="text-body2 q-mb-md">
            Na liście jest {{ pendingItems.length }} niekupionych pozycji. Oryginalna lista zostanie
            zachowana.
          </div>
          <q-banner v-if="pendingItems.length === 0" class="bg-grey-3 q-mb-md">
            Ta lista nie ma jeszcze niekupionych pozycji do podziału.
          </q-banner>
          <q-option-group
            v-model="promotionSplitMode"
            inline
            :options="[
              { label: 'Jeden sklep', value: 'single' },
              { label: 'Wiele sklepów', value: 'multiple' },
            ]"
          />
          <q-select
            v-model="selectedPromotionShops"
            class="q-mt-md"
            dense
            outlined
            emit-value
            map-options
            :multiple="promotionSplitMode === 'multiple'"
            :options="favouriteShopOptions"
            label="Ulubione sklepy"
            hint="Wybierz sklep, do którego chcesz iść"
            :loading="loadingPromotionCoverage"
          />
          <q-banner v-if="promotionCoverage.length > 0" class="bg-orange-1 q-mt-md">
            <template #avatar><q-icon name="local_offer" color="deep-orange" /></template>
            <div v-for="coverage in promotionCoverage" :key="coverage.shop_slug" class="q-mb-sm">
              <strong>{{ coverage.shop_name }}</strong> — {{ coverage.matched_query_count }} z
              {{ pendingItems.length }} pozycji ma promocję.
              <div class="text-caption">
                Oferty: {{ coverageStats(coverage).offers }} · suma cen promocyjnych:
                <strong>{{ coverageStats(coverage).total }} zł</strong> · średnio:
                {{ coverageStats(coverage).average }} zł
              </div>
            </div>
            <div class="text-caption text-grey-8 q-mt-sm">
              Suma obejmuje tylko oferty z podaną ceną i nie uwzględnia ilości produktów.
            </div>
          </q-banner>
          <div v-if="promotionCoverage.length > 0" class="q-mt-md">
            <div class="text-subtitle2 q-mb-sm">Porównanie cen jednostkowych</div>
            <q-markup-table dense flat bordered wrap-cells>
              <thead>
                <tr>
                  <th class="text-left">Produkt / tag</th>
                  <th v-for="shop in promotionCoverage" :key="shop.shop_slug" class="text-right">
                    {{ shop.shop_name }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in priceComparisonRows" :key="row.label">
                  <td>{{ row.label }}</td>
                  <td
                    v-for="cell in row.cells"
                    :key="cell.shopSlug"
                    class="text-right"
                    :class="cell.isBest ? 'text-positive text-weight-bold' : ''"
                  >
                    <a v-if="cell.url !== null" :href="cell.url" target="_blank" rel="noopener">
                      {{ cell.price === null ? 'Gazetka' : `${cell.price.toFixed(2)} zł` }}
                    </a>
                    <span v-else>—</span>
                  </td>
                </tr>
              </tbody>
            </q-markup-table>
            <div class="text-caption text-grey-8 q-mt-xs">
              Zielona cena jest najniższą znalezioną ceną oferty. To porównanie cen ofertowych, nie
              pełna cena za kilogram, jeśli gazetka nie podaje jednostki.
            </div>
          </div>
          <q-banner v-if="favouriteShopOptions.length === 0" class="bg-grey-3 q-mt-md">
            Najpierw wybierz ulubione sklepy w sekcji Promocje.
          </q-banner>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat label="Anuluj" no-caps />
          <q-btn
            color="deep-orange"
            label="Utwórz podzielone listy"
            no-caps
            :loading="splittingByPromotions"
            :disable="!canSplitByPromotions"
            @click="splitByPromotions"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style scoped>
.shopping-row {
  display: flex;
  align-items: start;
}

.shopping-list-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.shopping-list-toolbar .q-select {
  flex: 1 1 auto;
  min-width: 0;
}

.shopping-row > .q-item__section {
  min-width: 0;
}

.shopping-product-column {
  flex: 1 1 auto;
}

.shopping-quantity-column {
  flex: 0 0 110px;
  width: 110px;
}

.shopping-tags-column {
  flex: 0 0 220px;
  width: 220px;
  max-width: 220px;
}

.shopping-item-actions {
  min-width: 48px;
}

@media (max-width: 599px) {
  .shopping-list-toolbar {
    align-items: stretch;
  }

  .shopping-row {
    flex-wrap: wrap;
  }

  .shopping-row-header,
  .shopping-quantity-column {
    display: none;
  }

  .shopping-tags-column {
    display: block;
    flex: 1 0 100%;
    width: 100%;
    max-width: none;
    justify-self: start;
    padding-top: 0;
  }
}
</style>

<script setup lang="ts">
import { formatQuantity } from '@/shared/formatQuantity';
import { computed, onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { fetchUnits } from '@/features/products/api';
import { fetchTagAnalysisStatus, startTagAnalysis } from '@/features/products/api';
import type { MeasurementUnit, Product } from '@/features/products/models';
import ProductPicker from '@/features/products/ProductPicker.vue';
import {
  addShoppingItem,
  buyShoppingItem,
  restorePurchasedShoppingItem,
  createShoppingList,
  deleteShoppingItem,
  deleteShoppingList,
  renameShoppingList,
  fetchShoppingItems,
  fetchShoppingLists,
  synchronizeMinimumStock,
} from '@/features/shopping/api';
import { compareStoreCoverage, fetchFavouriteShops } from '@/features/promotions/api';
import type { FavouriteShop, StorePromotionCoverage } from '@/features/promotions/models';
import { describeShoppingError } from '@/features/shopping/errors';
import type { ShoppingItem, ShoppingList } from '@/features/shopping/models';
import { useHouseholdStore } from '@/features/households/store';

const quasar = useQuasar();
const households = useHouseholdStore();

const lists = ref<ShoppingList[]>([]);
const selectedListId = ref<number | null>(null);
const items = ref<ShoppingItem[]>([]);
const units = ref<MeasurementUnit[]>([]);
const loadingLists = ref(false);
const loadingItems = ref(false);
const synchronizing = ref(false);
const savingItem = ref(false);
const createListDialogOpen = ref(false);
const newListName = ref('');
const creatingList = ref(false);
const renameListDialogOpen = ref(false);
const renameListName = ref('');
const renamingList = ref(false);
const itemMode = ref<'product' | 'free_text'>('product');
const promotionSplitDialogOpen = ref(false);
const promotionSplitMode = ref<'single' | 'multiple'>('single');
const selectedPromotionShops = ref<string | string[]>('');
const favouriteShops = ref<FavouriteShop[]>([]);
const promotionCoverage = ref<StorePromotionCoverage[]>([]);
const loadingPromotionCoverage = ref(false);
const splittingByPromotions = ref(false);
const reanalyzingItemId = ref<number | null>(null);
const selectedReanalysisIds = ref<number[]>([]);
const reanalysisSelectionMode = ref(false);
const reanalyzingSelected = ref(false);

const form = ref<{
  product: Product | null;
  freeText: string;
  quantity: string;
  unitCode: string | null;
}>({ product: null, freeText: '', quantity: '', unitCode: null });
const advancedAdd = ref(false);
const shoppingTaggingStatus = ref<{
  active: boolean;
  processed: number;
  total: number;
  status: string;
} | null>(null);
let taggingNotification: (() => void) | null = null;
let lastTaggingNotificationState = '';

function refreshShoppingTaggingStatus(): void {
  const raw = localStorage.getItem('jedzonko.shopping-tagging');
  shoppingTaggingStatus.value = raw === null ? null : JSON.parse(raw);
  const status = shoppingTaggingStatus.value;
  if (status === null) return;
  const state = `${status.status}:${status.processed}:${status.total}`;
  if (state === lastTaggingNotificationState) return;
  if (
    (status.status === 'completed' || status.status === 'failed') &&
    localStorage.getItem('jedzonko.shopping-tagging-dismissed') === state
  ) {
    lastTaggingNotificationState = state;
    return;
  }
  lastTaggingNotificationState = state;
  taggingNotification?.();
  const finished = status.status === 'completed' || status.status === 'failed';
  taggingNotification = quasar.notify({
    type: status.status === 'failed' ? 'negative' : finished ? 'positive' : 'info',
    message:
      status.status === 'failed'
        ? `Przetwarzanie składników nie powiodło się (${status.processed}/${status.total}).`
        : finished
          ? `Przetwarzanie składników zakończone (${status.processed}/${status.total}).`
          : `Przetwarzanie składników: ${status.processed}/${status.total}`,
    timeout: 0,
    actions: [
      {
        label: 'Zamknij',
        color: 'white',
        handler: () => {
          localStorage.setItem('jedzonko.shopping-tagging-dismissed', state);
          taggingNotification = null;
        },
      },
    ],
    group: 'shopping-tagging-progress',
  });
}

const listOptions = computed(() =>
  lists.value.map((list) => ({
    id: list.id,
    label: list.name,
  })),
);
const selectedList = computed(() => lists.value.find((list) => list.id === selectedListId.value));
const pendingItems = computed(() => items.value.filter((item) => !item.is_purchased));
const purchasedItems = computed(() => items.value.filter((item) => item.is_purchased));
const favouriteShopOptions = computed(() =>
  favouriteShops.value.map((shop) => ({ label: shop.name, value: shop.slug })),
);
const chosenShopSlugs = computed(() =>
  typeof selectedPromotionShops.value === 'string'
    ? selectedPromotionShops.value
      ? [selectedPromotionShops.value]
      : []
    : selectedPromotionShops.value,
);
const canSplitByPromotions = computed(
  () => chosenShopSlugs.value.length > 0 && pendingItems.value.length > 0,
);

function coverageStats(coverage: StorePromotionCoverage): {
  offers: number;
  total: string;
  average: string;
} {
  const prices = coverage.offers
    .map((offer) =>
      Number.parseFloat((offer.price ?? '').replace(',', '.').replace(/[^0-9.]/g, '')),
    )
    .filter((price) => Number.isFinite(price));
  const total = prices.reduce((sum, price) => sum + price, 0);
  return {
    offers: prices.length,
    total: total.toFixed(2),
    average: prices.length === 0 ? '—' : (total / prices.length).toFixed(2),
  };
}

const priceComparisonRows = computed(() => {
  const normalize = (value: string) =>
    value.toLocaleLowerCase('pl-PL').replace(/[^a-z0-9ąćęłńóśźż ]/g, ' ');
  return pendingItems.value.map((item) => {
    const label = item.tag_names[0] ?? item.product_name ?? item.free_text ?? 'Pozycja';
    const words = normalize(label)
      .split(/\s+/)
      .filter((word) => word.length > 2);
    const cells = promotionCoverage.value.map((shop) => {
      const matches = shop.offers.filter((offer) => {
        const offerName = normalize(offer.name);
        return words.length > 0 && words.every((word) => offerName.includes(word));
      });
      const prices = matches
        .map((offer) =>
          Number.parseFloat((offer.price ?? '').replace(',', '.').replace(/[^0-9.]/g, '')),
        )
        .filter((price) => Number.isFinite(price));
      const bestOffer = matches.find((offer) =>
        prices.includes(
          Number.parseFloat((offer.price ?? '').replace(',', '.').replace(/[^0-9.]/g, '')),
        ),
      );
      return {
        shopSlug: shop.shop_slug,
        price: prices.length ? Math.min(...prices) : null,
        url: bestOffer?.leaflet_url ?? null,
        isBest: false,
      };
    });
    const available = cells
      .map((cell) => cell.price)
      .filter((price): price is number => price !== null);
    const best = available.length ? Math.min(...available) : null;
    cells.forEach((cell) => {
      cell.isBest = best !== null && cell.price === best;
    });
    return { label, cells };
  });
});

function notifyError(error: unknown): void {
  quasar.notify({ type: 'negative', message: describeShoppingError(error) });
}

async function loadItems(): Promise<void> {
  if (selectedListId.value === null) {
    items.value = [];
    return;
  }
  loadingItems.value = true;
  try {
    items.value = await fetchShoppingItems(selectedListId.value);
  } catch (error) {
    items.value = [];
    notifyError(error);
  } finally {
    loadingItems.value = false;
  }
}

async function loadLists(): Promise<void> {
  if (households.selectedId === null) {
    lists.value = [];
    selectedListId.value = null;
    items.value = [];
    return;
  }
  loadingLists.value = true;
  try {
    lists.value = await fetchShoppingLists(households.selectedId);
    const current = lists.value.find((list) => list.id === selectedListId.value);
    if (current === undefined) {
      const primary = lists.value.find((list) => list.is_primary) ?? lists.value[0];
      selectedListId.value = primary?.id ?? null;
    }
    await loadItems();
  } catch (error) {
    lists.value = [];
    notifyError(error);
  } finally {
    loadingLists.value = false;
  }
}

function confirmDeleteList(): void {
  const list = selectedList.value;
  if (list === undefined) return;
  quasar
    .dialog({
      title: 'Usunąć listę zakupów?',
      message: `Lista „${list.name}” i jej pozycje zostaną usunięte.`,
      cancel: true,
      persistent: true,
    })
    .onOk(() => {
      void doDeleteList(list.id);
    });
}

function openRenameList(): void {
  const list = selectedList.value;
  if (list === undefined) return;
  renameListName.value = list.name;
  renameListDialogOpen.value = true;
}

async function submitRenameList(): Promise<void> {
  const list = selectedList.value;
  const name = renameListName.value.trim();
  if (list === undefined || name.length === 0) return;
  renamingList.value = true;
  try {
    await renameShoppingList(list.id, name);
    renameListDialogOpen.value = false;
    await loadLists();
    quasar.notify({ type: 'positive', message: 'Nazwa listy została zmieniona.' });
  } catch (error) {
    notifyError(error);
  } finally {
    renamingList.value = false;
  }
}

async function doDeleteList(listId: number): Promise<void> {
  try {
    await deleteShoppingList(listId);
    await loadLists();
    quasar.notify({ type: 'positive', message: 'Lista została usunięta.' });
  } catch (error) {
    notifyError(error);
  }
}

async function loadUnits(): Promise<void> {
  try {
    units.value = await fetchUnits();
  } catch (error) {
    notifyError(error);
  }
}

function openCreateList(): void {
  newListName.value = '';
  createListDialogOpen.value = true;
}

async function submitCreateList(): Promise<void> {
  if (households.selectedId === null) {
    return;
  }
  creatingList.value = true;
  try {
    const list = await createShoppingList(households.selectedId, newListName.value.trim());
    lists.value = [...lists.value, list];
    selectedListId.value = list.id;
    createListDialogOpen.value = false;
    await loadItems();
  } catch (error) {
    notifyError(error);
  } finally {
    creatingList.value = false;
  }
}

async function submitItem(): Promise<void> {
  if (selectedListId.value === null) {
    return;
  }
  const product = form.value.product;
  const freeText = form.value.freeText.trim();
  const mode = advancedAdd.value ? itemMode.value : 'free_text';
  if (mode === 'product' && product === null) {
    quasar.notify({ type: 'warning', message: 'Wybierz produkt.' });
    return;
  }
  if (mode === 'free_text' && freeText === '') {
    quasar.notify({ type: 'warning', message: 'Podaj nazwę pozycji.' });
    return;
  }
  savingItem.value = true;
  try {
    const item = await addShoppingItem(selectedListId.value, {
      ...(mode === 'product' && product !== null
        ? { product_id: product.id }
        : { free_text: freeText }),
      quantity: form.value.quantity.trim() || '1',
      ...(form.value.unitCode === null ? {} : { unit_code: form.value.unitCode }),
    });
    items.value = [...items.value, item];
    form.value = { product: null, freeText: '', quantity: '', unitCode: null };
  } catch (error) {
    notifyError(error);
  } finally {
    savingItem.value = false;
  }
}

async function togglePurchased(item: ShoppingItem): Promise<void> {
  if (item.id === null) return;
  try {
    if (item.is_purchased) {
      await restorePurchasedShoppingItem(item.id);
    } else {
      await buyShoppingItem(item.id);
    }
    items.value = items.value.map((entry) =>
      entry.id === item.id ? { ...entry, is_purchased: !item.is_purchased } : entry,
    );
  } catch (error) {
    notifyError(error);
    await loadItems();
  }
}

function confirmDelete(item: ShoppingItem): void {
  quasar
    .dialog({
      title: 'Usunąć pozycję?',
      message: `Czy usunąć ${item.product_name ?? item.free_text ?? ''} z listy?`,
      cancel: true,
      persistent: true,
    })
    .onOk(() => {
      void doDelete(item);
    });
}

async function doDelete(item: ShoppingItem): Promise<void> {
  if (item.id === null) {
    return;
  }
  const deletedId = item.id;
  try {
    await deleteShoppingItem(deletedId);
    items.value = items.value.filter((entry) => entry.id !== deletedId);
  } catch (error) {
    notifyError(error);
  }
}

async function reanalyzeTag(item: ShoppingItem): Promise<void> {
  if (households.selectedId === null) return;
  const text = item.free_text ?? item.product_name ?? '';
  if (item.id === null || (!item.product_id && !text.trim())) {
    quasar.notify({ type: 'warning', message: 'Brak tekstu pozycji do analizy.' });
    return;
  }
  reanalyzingItemId.value = item.id;
  try {
    const jobId = await startTagAnalysis(
      households.selectedId,
      item.product_id ?? undefined,
      item.product_id === null ? { id: item.id, text: text.trim() } : undefined,
    );
    localStorage.setItem(
      'jedzonko.shopping-tagging',
      JSON.stringify({ active: true, processed: 0, total: 1, status: 'running' }),
    );
    let status = await fetchTagAnalysisStatus(jobId);
    while (status.status === 'running') {
      await new Promise((resolve) => window.setTimeout(resolve, 400));
      status = await fetchTagAnalysisStatus(jobId);
      localStorage.setItem(
        'jedzonko.shopping-tagging',
        JSON.stringify({
          active: true,
          processed: status.processed,
          total: status.total || 1,
          status: 'running',
        }),
      );
    }
    localStorage.setItem(
      'jedzonko.shopping-tagging',
      JSON.stringify({
        active: false,
        processed: status.processed,
        total: status.total || 1,
        status: status.status,
      }),
    );
    await loadItems();
  } catch (error) {
    notifyError(error);
  } finally {
    reanalyzingItemId.value = null;
  }
}

function toggleReanalysisSelection(item: ShoppingItem): void {
  if (item.id === null) return;
  selectedReanalysisIds.value = selectedReanalysisIds.value.includes(item.id)
    ? selectedReanalysisIds.value.filter((id) => id !== item.id)
    : [...selectedReanalysisIds.value, item.id];
}

async function reanalyzeSelected(): Promise<void> {
  const selected = pendingItems.value.filter(
    (item) => item.id !== null && selectedReanalysisIds.value.includes(item.id),
  );
  if (selected.length === 0) return;
  reanalyzingSelected.value = true;
  try {
    for (const item of selected) {
      await reanalyzeTag(item);
    }
    selectedReanalysisIds.value = [];
    quasar.notify({
      type: 'positive',
      message: `Ponownie przeanalizowano ${selected.length} pozycji.`,
    });
  } finally {
    reanalyzingSelected.value = false;
  }
}

async function runSynchronize(): Promise<void> {
  if (selectedListId.value === null) {
    return;
  }
  synchronizing.value = true;
  try {
    await synchronizeMinimumStock(selectedListId.value);
    await loadItems();
    quasar.notify({ type: 'positive', message: 'Zsynchronizowano minimalne zapasy.' });
  } catch (error) {
    notifyError(error);
  } finally {
    synchronizing.value = false;
  }
}

async function openPromotionSplit(): Promise<void> {
  promotionSplitDialogOpen.value = true;
  promotionCoverage.value = [];
  loadingPromotionCoverage.value = true;
  try {
    favouriteShops.value = await fetchFavouriteShops();
    const first = favouriteShops.value[0]?.slug ?? '';
    selectedPromotionShops.value = promotionSplitMode.value === 'multiple' ? [] : first;
    if (first) await loadPromotionCoverage();
  } catch (error) {
    notifyError(error);
  } finally {
    loadingPromotionCoverage.value = false;
  }
}

async function loadPromotionCoverage(): Promise<void> {
  if (!canSplitByPromotions.value) {
    promotionCoverage.value = [];
    return;
  }
  loadingPromotionCoverage.value = true;
  try {
    promotionCoverage.value = await compareStoreCoverage(
      pendingItems.value.map((item) => item.product_name ?? item.free_text ?? '').filter(Boolean),
      chosenShopSlugs.value,
    );
  } catch (error) {
    promotionCoverage.value = [];
    notifyError(error);
  } finally {
    loadingPromotionCoverage.value = false;
  }
}

async function splitByPromotions(): Promise<void> {
  if (households.selectedId === null || !canSplitByPromotions.value) return;
  splittingByPromotions.value = true;
  try {
    const coverageByShop = new Map(
      promotionCoverage.value.map((entry) => [entry.shop_slug, entry]),
    );
    const assignments = new Map<string, ShoppingItem[]>();
    const selected = chosenShopSlugs.value;
    for (const item of pendingItems.value) {
      const label = item.product_name ?? item.free_text ?? '';
      const normalize = (value: string) => value.trim().toLocaleLowerCase('pl-PL');
      const matchingShop = selected
        .map((slug) => coverageByShop.get(slug))
        .filter((entry): entry is StorePromotionCoverage => entry !== undefined)
        .sort(
          (a, b) =>
            Number(b.matched_queries.some((query) => normalize(query) === normalize(label))) -
            Number(a.matched_queries.some((query) => normalize(query) === normalize(label))),
        )[0];
      const slug = matchingShop?.shop_slug ?? 'other';
      const name = matchingShop?.shop_name ?? 'Pozostałe';
      const key = `${slug}|${name}`;
      const group = assignments.get(key) ?? [];
      group.push(item);
      assignments.set(key, group);
    }
    const created: ShoppingList[] = [];
    for (const [key, group] of assignments) {
      const name = key.split('|')[1] ?? 'Pozostałe';
      const list = await createShoppingList(households.selectedId, `Zakupy — ${name}`);
      created.push(list);
      for (const item of group) {
        await addShoppingItem(list.id, {
          ...(item.product_id !== null
            ? { product_id: item.product_id }
            : { free_text: item.free_text ?? item.product_name ?? '' }),
          quantity: item.quantity,
          ...(item.unit_code ? { unit_code: item.unit_code } : {}),
        });
      }
    }
    lists.value = [...lists.value, ...created];
    promotionSplitDialogOpen.value = false;
    quasar.notify({ type: 'positive', message: `Utworzono ${created.length} podzielonych list.` });
  } catch (error) {
    notifyError(error);
  } finally {
    splittingByPromotions.value = false;
  }
}

watch([promotionSplitMode, selectedPromotionShops], () => {
  void loadPromotionCoverage();
});

watch(promotionSplitMode, (mode) => {
  if (mode === 'single' && Array.isArray(selectedPromotionShops.value)) {
    selectedPromotionShops.value = selectedPromotionShops.value[0] ?? '';
  } else if (mode === 'multiple' && typeof selectedPromotionShops.value === 'string') {
    selectedPromotionShops.value = selectedPromotionShops.value
      ? [selectedPromotionShops.value]
      : [];
  }
});

onMounted(() => {
  refreshShoppingTaggingStatus();
  setInterval(refreshShoppingTaggingStatus, 500);
  void loadUnits();
  void loadLists();
});

watch(
  () => households.selectedId,
  () => {
    void loadLists();
  },
);
</script>

<style scoped>
.shopping-item-actions {
  align-self: flex-start;
  min-width: 48px;
}
</style>
