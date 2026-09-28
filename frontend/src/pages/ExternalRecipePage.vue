<template>
  <q-page padding>
    <q-inner-loading :showing="loading" />

    <template v-if="recipe !== null">
      <div class="row items-center q-mb-sm">
        <div class="text-h5">{{ recipe.name }}</div>
        <q-space />
        <q-btn flat no-caps icon="arrow_back" label="Przepisy" :to="{ name: 'recipes' }" />
      </div>

      <div class="q-mb-md">
        <q-badge color="deep-orange" :label="recipe.source_name" />
        <q-btn
          flat
          dense
          no-caps
          size="sm"
          icon="open_in_new"
          label="Zobacz oryginał"
          type="a"
          :href="recipe.source_url"
          target="_blank"
          rel="noopener"
        />
      </div>

      <q-img
        v-if="recipe.image_url !== null"
        :src="recipe.image_url"
        :alt="recipe.name"
        style="max-height: 280px"
        class="q-mb-md rounded-borders"
      />

      <div class="text-body2 q-mb-md">{{ recipe.description }}</div>

      <q-list bordered separator class="q-mb-md">
        <q-item>
          <q-item-section>Przygotowanie</q-item-section>
          <q-item-section side>{{ recipe.preparation_time_minutes }} min</q-item-section>
        </q-item>
        <q-item>
          <q-item-section>Gotowanie</q-item-section>
          <q-item-section side>{{ recipe.cooking_time_minutes }} min</q-item-section>
        </q-item>
        <q-item v-if="recipe.yield_label">
          <q-item-section>Wydajność</q-item-section>
          <q-item-section side>{{ recipe.yield_label }}</q-item-section>
        </q-item>
      </q-list>

      <div class="text-h6 q-mb-sm">Składniki</div>
      <q-banner v-if="missingIngredients.length > 0" class="bg-orange-1 q-mb-md">
        <div class="row items-center q-col-gutter-sm">
          <div class="col">Brakuje {{ missingIngredients.length }} składników</div>
          <q-btn
            color="primary"
            no-caps
            label="Dodaj do listy zakupów"
            :loading="addingToShoppingList"
            @click="openShoppingDialog"
          />
        </div>
      </q-banner>
      <q-banner v-else class="bg-green-2 q-mb-md">Masz wszystkie składniki tego przepisu.</q-banner>
      <q-list bordered separator class="q-mb-md">
        <q-item v-for="(ingredient, index) in recipe.ingredients" :key="index">
          <q-item-section>{{ ingredient.source_text }}</q-item-section>
        </q-item>
      </q-list>

      <q-dialog v-model="shoppingDialogOpen">
        <q-card style="min-width: min(420px, 92vw)">
          <q-card-section class="text-h6">Dodaj brakujące składniki</q-card-section>
          <q-card-section>
            <div class="text-caption q-mb-sm">
              {{ missingIngredients.map((item) => item.source_text).join(', ') }}
            </div>
            <q-select
              v-model="selectedListId"
              :options="shoppingListOptions"
              emit-value
              map-options
              label="Istniejąca lista"
              clearable
              class="q-mb-sm"
            />
            <q-input
              v-model="newListName"
              label="albo utwórz nową listę"
              hint="Pozostaw puste, aby użyć wybranej listy"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat no-caps label="Anuluj" v-close-popup />
            <q-btn
              color="primary"
              no-caps
              label="Dodaj składniki"
              :disable="selectedListId === null && newListName.trim() === ''"
              :loading="addingToShoppingList"
              @click="addMissingToShoppingList"
            />
          </q-card-actions>
        </q-card>
      </q-dialog>

      <div class="text-h6 q-mb-sm">Przygotowanie</div>
      <q-list bordered separator>
        <q-item v-for="(step, index) in recipe.steps" :key="index">
          <q-item-section avatar>
            <q-avatar color="primary" text-color="white" size="28px">{{ index + 1 }}</q-avatar>
          </q-item-section>
          <q-item-section>{{ step }}</q-item-section>
        </q-item>
      </q-list>

      <div v-if="recipe.tags.length > 0" class="q-mt-md">
        <q-chip v-for="tag in recipe.tags" :key="tag" dense square outline>{{ tag }}</q-chip>
      </div>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRoute } from 'vue-router';
import { fetchExternalRecipe } from '@/features/recipes/api';
import { fetchInventory } from '@/features/inventory/api';
import type { InventoryItem } from '@/features/inventory/models';
import {
  addShoppingItem,
  createShoppingList,
  fetchShoppingLists,
} from '@/features/shopping/api';
import type { ShoppingList } from '@/features/shopping/models';
import { useHouseholdStore } from '@/features/households/store';
import { describeRecipeError } from '@/features/recipes/errors';
import type { ExternalRecipe } from '@/features/recipes/models';

const quasar = useQuasar();
const route = useRoute();
const households = useHouseholdStore();

const recipe = ref<ExternalRecipe | null>(null);
const loading = ref(false);
const inventory = ref<InventoryItem[]>([]);
const shoppingLists = ref<ShoppingList[]>([]);
const shoppingDialogOpen = ref(false);
const selectedListId = ref<number | null>(null);
const newListName = ref('');
const addingToShoppingList = ref(false);
const shoppingProgress = ref(0);
let progressNotification: (() => void) | null = null;

const missingIngredients = computed(() => {
  if (recipe.value === null) return [];
  const stocked = inventory.value.flatMap((item) => [item.product_name, ...item.tags]);
  return recipe.value.ingredients.filter(
    (ingredient) => !stocked.some((name) => normalize(name).includes(normalize(ingredient.name))),
  );
});

const shoppingIngredients = computed(() =>
  missingIngredients.value.flatMap((ingredient) => {
    const match = ingredient.name.match(/^przyprawy?\s*:\s*(.+)$/i);
    if (match === null) return [ingredient];
    return (match[1] ?? '')
      .split(/,|\s+lub\s+/i)
      .map((name) => name.trim())
      .filter(Boolean)
      .map((name) => ({ ...ingredient, name, quantity: null, unit_code: null }));
  }),
);

const shoppingListOptions = computed(() =>
  shoppingLists.value.map((list) => ({ label: `${list.name} (${list.item_count})`, value: list.id })),
);

function normalize(value: string): string {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

async function openShoppingDialog(): Promise<void> {
  if (households.selectedId === null) return;
  shoppingLists.value = await fetchShoppingLists(households.selectedId);
  selectedListId.value = shoppingLists.value.find((list) => list.is_primary)?.id ?? null;
  newListName.value = '';
  shoppingDialogOpen.value = true;
}

async function addMissingToShoppingList(): Promise<void> {
  if (households.selectedId === null || recipe.value === null) return;
  addingToShoppingList.value = true;
  shoppingProgress.value = 0;
  progressNotification?.();
  progressNotification = quasar.notify({
    type: 'info',
    message: `Dodawanie składników: 0/${shoppingIngredients.value.length}`,
    timeout: 0,
    actions: [{ label: 'Zamknij', color: 'white', handler: () => { progressNotification = null; } }],
    group: 'shopping-tagging-progress',
  });
  localStorage.setItem('jedzonko.shopping-tagging', JSON.stringify({ active: true, processed: 0, total: shoppingIngredients.value.length, status: 'running' }));
  try {
    let listId = selectedListId.value;
    if (newListName.value.trim() !== '') {
      const created = await createShoppingList(households.selectedId, newListName.value.trim());
      listId = created.id;
    }
    if (listId === null) return;
    for (const ingredient of shoppingIngredients.value) {
      await addShoppingItem(listId, {
          free_text: ingredient.name,
          quantity: ingredient.quantity ?? '1',
          ...(ingredient.unit_code === null ? {} : { unit_code: ingredient.unit_code }),
      });
      shoppingProgress.value += 1;
      progressNotification?.();
      progressNotification = quasar.notify({
        type: 'info',
        message: `Dodawanie składników: ${shoppingProgress.value}/${shoppingIngredients.value.length}`,
        timeout: 0,
        actions: [{ label: 'Zamknij', color: 'white', handler: () => { progressNotification = null; } }],
        group: 'shopping-tagging-progress',
      });
      localStorage.setItem('jedzonko.shopping-tagging', JSON.stringify({ active: true, processed: shoppingProgress.value, total: shoppingIngredients.value.length, status: 'running' }));
    }
    localStorage.setItem('jedzonko.shopping-tagging', JSON.stringify({ active: false, processed: shoppingProgress.value, total: shoppingIngredients.value.length, status: 'completed' }));
    shoppingDialogOpen.value = false;
    progressNotification?.();
    progressNotification = null;
    quasar.notify({ type: 'positive', message: 'Brakujące składniki dodano do listy zakupów.' });
  } catch (error) {
    localStorage.setItem('jedzonko.shopping-tagging', JSON.stringify({ active: false, processed: shoppingProgress.value, total: shoppingIngredients.value.length, status: 'failed' }));
    progressNotification?.();
    progressNotification = null;
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    addingToShoppingList.value = false;
  }
}

onMounted(async () => {
  const reference = String(route.params.reference);
  loading.value = true;
  try {
    recipe.value = await fetchExternalRecipe(reference);
    if (households.selectedId !== null) {
      inventory.value = await fetchInventory(households.selectedId);
    }
  } catch (error) {
    quasar.notify({ type: 'negative', message: describeRecipeError(error) });
  } finally {
    loading.value = false;
  }
});
</script>
