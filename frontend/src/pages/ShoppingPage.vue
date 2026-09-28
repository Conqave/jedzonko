<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Zakupy</div>
    <q-banner v-if="households.selectedId === null" class="bg-grey-3">
      Wybierz gospodarstwo domowe, aby zobaczyć listy zakupów.
    </q-banner>

    <template v-else>
      <ShoppingListToolbar
        :lists="lists"
        :selected-list-id="selectedListId"
        :selected-list="selectedList"
        :can-split="accounts.canViewPromotions"
        :busy="isListBusy"
        @select="(listId) => (selectedListId = listId)"
        @create="createList"
        @refill="refillMinimumStock"
        @rename="renameList"
        @split="splitList"
        @remove="removeList"
      />
      <ShoppingItemForm
        v-if="selectedListId !== null"
        :household-id="households.selectedId"
        :units="units"
        :busy="isItemBusy"
        :add-item="addItem"
      />
      <q-linear-progress v-if="isItemBusy" indeterminate class="q-mb-sm" />
      <ShoppingItemList
        :pending-items="pendingItems"
        :purchased-items="purchasedItems"
        :find-unit-name="findUnitName"
        @buy="buyItem"
        @restore="restoreItem"
        @remove="removeItem"
      />
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { toRef } from 'vue';
import { useAccountStore } from '@/features/accounts/store';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useHouseholdStore } from '@/features/households/store';
import { useFavouriteShops } from '@/features/promotions/useFavouriteShops';
import PromotionSplitDialog from '@/features/shopping/components/PromotionSplitDialog.vue';
import ShoppingItemForm from '@/features/shopping/components/ShoppingItemForm.vue';
import ShoppingItemList from '@/features/shopping/components/ShoppingItemList.vue';
import ShoppingListToolbar from '@/features/shopping/components/ShoppingListToolbar.vue';
import type { ShopOption, ShoppingItem, ShoppingList } from '@/features/shopping/model';
import { useShoppingItems } from '@/features/shopping/useShoppingItems';
import { useShoppingLists } from '@/features/shopping/useShoppingLists';
import { useDialogs } from '@/shared/useDialogs';

const quasar = useQuasar();
const accounts = useAccountStore();
const households = useHouseholdStore();
const householdId = toRef(households, 'selectedId');
const dialogs = useDialogs();
const { units, findUnitName } = useMeasurementUnits();
const {
  lists,
  selectedListId,
  selectedList,
  busy: isListBusy,
  create,
  rename,
  remove,
  refillMinimumStock: refill,
  splitSelected,
} = useShoppingLists(householdId);
const {
  pendingItems,
  purchasedItems,
  busy: isItemBusy,
  load: loadItems,
  add: addItem,
  buy: buyItem,
  restore: restoreItem,
  remove: removeShoppingItem,
} = useShoppingItems(selectedListId);

const { shops: promotionShops, favouriteShops, load: loadPromotionShops } = useFavouriteShops();

function findSplitShopOptions(): ShopOption[] {
  const preferred = favouriteShops.value.length > 0 ? favouriteShops.value : promotionShops.value;
  return preferred.map((shop) => ({ slug: shop.slug, name: shop.name }));
}

async function createList(): Promise<void> {
  const name = await dialogs.promptText({
    title: 'Nowa lista zakupów',
    label: 'Nazwa',
    initial: '',
  });
  if (name !== null) {
    await create(name);
  }
}

async function renameList(list: ShoppingList): Promise<void> {
  const prompt = { title: 'Zmień nazwę listy', label: 'Nazwa', initial: list.name };
  const name = await dialogs.promptText(prompt);
  if (name !== null) {
    await rename(list.id, name);
  }
}

async function removeList(list: ShoppingList): Promise<void> {
  const isConfirmed = await dialogs.confirm('Usunąć listę?', `Lista „${list.name}” zniknie.`);
  if (isConfirmed) {
    await remove(list.id);
  }
}

async function refillMinimumStock(): Promise<void> {
  const isRefilled = await refill();
  if (!isRefilled) {
    return;
  }
  await loadItems();
  dialogs.notifySuccess('Brakujące minimalne zapasy są na głównej liście.');
}

async function splitList(): Promise<void> {
  await loadPromotionShops();
  const componentProps = { shops: findSplitShopOptions() };
  quasar.dialog({ component: PromotionSplitDialog, componentProps }).onOk((slugs: string[]) => {
    void splitSelected(slugs).then((isSplit) => {
      if (isSplit) {
        dialogs.notifySuccess('Utworzono listy sklepów z promocjami.');
      }
    });
  });
}

async function removeItem(item: ShoppingItem): Promise<void> {
  const isConfirmed = await dialogs.confirm('Usunąć pozycję?', `Usunąć „${item.name}” z listy?`);
  if (isConfirmed) {
    await removeShoppingItem(item);
  }
}
</script>
