<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Zakupy</div>
    <q-banner v-if="households.selectedId === null" class="bg-grey-3 q-mb-md">
      Nie masz jeszcze gospodarstwa domowego albo żadne nie jest wybrane. Utwórz dom, aby zacząć.
      <template #action>
        <q-btn flat no-caps color="primary" label="Utwórz dom" :to="{ name: 'households' }" />
      </template>
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
        :describe-unit-quantity="describeUnitQuantity"
        :find-product-tags="findProductTags"
        :is-tagging="isTagging"
        @tag="tagItems"
        @buy="buyItems"
        @restore="restoreItem"
        @choose-product="chooseItemProduct"
        @tag-item="tagItem"
        @remove="removeItem"
      />
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { toRef } from 'vue';
import { useAccountStore } from '@/features/accounts/store';
import type { Product } from '@/features/catalog/model';
import { useMeasurementUnits } from '@/features/catalog/useMeasurementUnits';
import { useProductCatalog } from '@/features/catalog/useProductCatalog';
import { useHouseholdStore } from '@/features/households/store';
import { useFavouriteShops } from '@/features/promotions/useFavouriteShops';
import ChooseProductDialog from '@/features/shopping/components/ChooseProductDialog.vue';
import PromotionSplitDialog from '@/features/shopping/components/PromotionSplitDialog.vue';
import PurchaseProductDialog from '@/features/shopping/components/PurchaseProductDialog.vue';
import ShoppingItemForm from '@/features/shopping/components/ShoppingItemForm.vue';
import ShoppingItemList from '@/features/shopping/components/ShoppingItemList.vue';
import ShoppingListToolbar from '@/features/shopping/components/ShoppingListToolbar.vue';
import TagItemDialog from '@/features/shopping/components/TagItemDialog.vue';
import {
  COUNT_UNIT_CODE,
  findPurchaseProductQuestions,
  toPurchases,
  type PurchaseProductQuestion,
  type ShopOption,
  type ShoppingItem,
  type ShoppingItemTagRequest,
  type ShoppingList,
} from '@/features/shopping/model';
import { useShoppingItems } from '@/features/shopping/useShoppingItems';
import { useShoppingLists } from '@/features/shopping/useShoppingLists';
import { formatQuantity } from '@/shared/formatQuantity';
import { useDialogs } from '@/shared/useDialogs';

const quasar = useQuasar();
const accounts = useAccountStore();
const households = useHouseholdStore();
const householdId = toRef(households, 'selectedId');
const dialogs = useDialogs();
const { units, describeUnitQuantity } = useMeasurementUnits();
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
  buy: buyShoppingItems,
  restore: restoreItem,
  chooseProduct,
  tagList,
  isTagging,
  tagItem: tagShoppingItem,
  interpretItem,
  remove: removeShoppingItem,
} = useShoppingItems(selectedListId);

const { shops: promotionShops, favouriteShops, load: loadPromotionShops } = useFavouriteShops();

function findSplitShopOptions(): ShopOption[] {
  const preferred = favouriteShops.value.length > 0 ? favouriteShops.value : promotionShops.value;
  return preferred.map((shop) => ({ slug: shop.slug, name: shop.name }));
}

const { listings: productListings, load: loadProductTags } = useProductCatalog(householdId);

function findProductTags(productId: number): string[] {
  const listing = productListings.value.find((entry) => entry.product.id === productId);
  return listing === undefined ? [] : listing.tags.map((tag) => tag.name);
}

function findTagProducts(ingredientId: number): Product[] {
  const tagged = productListings.value.filter((entry) =>
    entry.tags.some((tag) => tag.id === ingredientId),
  );
  return tagged.map((entry) => entry.product);
}

function askPurchaseProduct(question: PurchaseProductQuestion): Promise<number | null> {
  const componentProps = { itemName: question.item.name, products: question.products };
  return new Promise((resolve) => {
    quasar
      .dialog({ component: PurchaseProductDialog, componentProps })
      .onOk((productId: number) => {
        resolve(productId);
      })
      .onCancel(() => {
        resolve(null);
      });
  });
}

async function buyItems(items: ShoppingItem[]): Promise<void> {
  const chosenProducts = new Map<number, number>();
  for (const question of findPurchaseProductQuestions(items, findTagProducts)) {
    const productId = await askPurchaseProduct(question);
    if (productId === null) {
      return;
    }
    chosenProducts.set(question.item.id, productId);
  }
  const purchases = toPurchases(items, chosenProducts);
  await buyShoppingItems(purchases);
  await loadProductTags();
}

function tagItem(item: ShoppingItem): void {
  const householdIdValue = households.selectedId;
  if (householdIdValue === null) {
    return;
  }
  const componentProps = {
    itemName: item.name,
    householdId: householdIdValue,
    units: units.value,
    initialIngredient:
      item.subject.kind === 'ingredient'
        ? { id: item.subject.ingredientId, name: item.name }
        : null,
    initialQuantity: formatQuantity(item.quantity),
    initialUnitCode: item.unitCode ?? COUNT_UNIT_CODE,
    interpret: () => interpretItem(item),
  };
  quasar
    .dialog({ component: TagItemDialog, componentProps })
    .onOk((request: ShoppingItemTagRequest) => {
      void tagShoppingItem(item, request.tagging, request.productId).then((isTagged) => {
        if (isTagged) {
          void loadProductTags();
        }
      });
    });
}

async function tagItems(): Promise<void> {
  const isTagged = await tagList();
  if (isTagged) {
    await loadProductTags();
    dialogs.notifySuccess('Lista otagowana.');
  }
}

function chooseItemProduct(item: ShoppingItem): void {
  const householdIdValue = households.selectedId;
  if (householdIdValue === null) {
    return;
  }
  const componentProps = { itemName: item.name, householdId: householdIdValue, units: units.value };
  quasar.dialog({ component: ChooseProductDialog, componentProps }).onOk((productId: number) => {
    void chooseProduct(item, productId);
  });
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
