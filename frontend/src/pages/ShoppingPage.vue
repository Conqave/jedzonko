<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Listy zakupów</div>

    <q-banner v-if="households.selectedId === null" class="bg-grey-3">
      Wybierz gospodarstwo domowe, aby zobaczyć listy zakupów.
    </q-banner>

    <template v-else>
      <div class="row q-col-gutter-sm items-start q-mb-md">
        <div class="col-12 col-sm-5">
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
        </div>
        <div class="col-12 col-sm-7 q-gutter-sm">
          <q-btn color="primary" icon="add" label="Nowa lista" no-caps @click="openCreateList" />
          <q-btn
            color="secondary"
            icon="sync"
            label="Uzupełnij minimalne zapasy"
            no-caps
            :disable="selectedListId === null"
            :loading="synchronizing"
            @click="runSynchronize"
          />
        </div>
      </div>

      <q-form class="row q-col-gutter-sm q-mb-md" @submit.prevent="submitItem">
        <div class="col-12 col-sm-3">
          <q-select
            v-model="itemMode"
            dense
            outlined
            emit-value
            map-options
            label="Rodzaj pozycji"
            :options="[
              { label: 'Składnik z katalogu', value: 'ingredient' },
              { label: 'Tekst własny', value: 'free_text' },
            ]"
          />
        </div>
        <div class="col-12 col-sm-4">
          <q-select
            v-if="itemMode === 'ingredient'"
            v-model="form.ingredient"
            dense
            outlined
            use-input
            input-debounce="300"
            label="Składnik"
            option-label="name"
            :options="ingredientOptions"
            :loading="searchingIngredients"
            @filter="filterIngredients"
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
      <q-list v-else bordered separator>
        <q-item v-for="item in items" :key="item.id">
          <q-item-section side top>
            <q-checkbox
              :model-value="item.is_purchased"
              :disable="item.is_purchased"
              @update:model-value="markPurchased(item)"
            />
          </q-item-section>
          <q-item-section>
            <q-item-label :class="item.is_purchased ? 'text-strike text-grey' : ''">
              {{ item.ingredient_name ?? item.free_text }}
            </q-item-label>
            <q-item-label caption>{{ item.quantity }} {{ item.unit_code ?? '' }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn
              flat
              dense
              round
              color="negative"
              icon="delete"
              aria-label="Usuń"
              @click="confirmDelete(item)"
            />
          </q-item-section>
        </q-item>
      </q-list>
    </template>

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
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { fetchUnits, searchIngredients } from '@/features/catalog/api';
import type { Ingredient, MeasurementUnit } from '@/features/catalog/models';
import {
  addShoppingItem,
  buyShoppingItem,
  createShoppingList,
  deleteShoppingItem,
  fetchShoppingItems,
  fetchShoppingLists,
  synchronizeMinimumStock,
} from '@/features/shopping/api';
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
const itemMode = ref<'ingredient' | 'free_text'>('ingredient');
const ingredientOptions = ref<Ingredient[]>([]);
const searchingIngredients = ref(false);

const form = ref<{
  ingredient: Ingredient | null;
  freeText: string;
  quantity: string;
  unitCode: string | null;
}>({ ingredient: null, freeText: '', quantity: '', unitCode: null });

const listOptions = computed(() =>
  lists.value.map((list) => ({
    id: list.id,
    label: list.is_primary ? `${list.name} (główna)` : list.name,
  })),
);

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

async function loadUnits(): Promise<void> {
  try {
    units.value = await fetchUnits();
  } catch (error) {
    notifyError(error);
  }
}

function filterIngredients(search: string, update: (callback: () => void) => void): void {
  searchingIngredients.value = true;
  void searchIngredients(search)
    .then((found) => {
      update(() => {
        ingredientOptions.value = found;
      });
    })
    .catch((error: unknown) => {
      update(() => {
        ingredientOptions.value = [];
      });
      notifyError(error);
    })
    .finally(() => {
      searchingIngredients.value = false;
    });
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
  const ingredient = form.value.ingredient;
  const freeText = form.value.freeText.trim();
  if (itemMode.value === 'ingredient' && ingredient === null) {
    quasar.notify({ type: 'warning', message: 'Wybierz składnik.' });
    return;
  }
  if (itemMode.value === 'free_text' && freeText === '') {
    quasar.notify({ type: 'warning', message: 'Podaj nazwę pozycji.' });
    return;
  }
  savingItem.value = true;
  try {
    const item = await addShoppingItem(selectedListId.value, {
      ...(itemMode.value === 'ingredient' && ingredient !== null
        ? { ingredient_id: ingredient.id }
        : { free_text: freeText }),
      quantity: form.value.quantity.trim(),
      ...(form.value.unitCode === null ? {} : { unit_code: form.value.unitCode }),
    });
    items.value = [...items.value, item];
    form.value = { ingredient: null, freeText: '', quantity: '', unitCode: null };
  } catch (error) {
    notifyError(error);
  } finally {
    savingItem.value = false;
  }
}

async function markPurchased(item: ShoppingItem): Promise<void> {
  try {
    await buyShoppingItem(item.id);
    items.value = items.value.map((entry) =>
      entry.id === item.id ? { ...entry, is_purchased: true } : entry,
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
      message: `Czy usunąć ${item.ingredient_name ?? item.free_text ?? ''} z listy?`,
      cancel: true,
      persistent: true,
    })
    .onOk(() => {
      void doDelete(item);
    });
}

async function doDelete(item: ShoppingItem): Promise<void> {
  try {
    await deleteShoppingItem(item.id);
    items.value = items.value.filter((entry) => entry.id !== item.id);
  } catch (error) {
    notifyError(error);
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

onMounted(() => {
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
