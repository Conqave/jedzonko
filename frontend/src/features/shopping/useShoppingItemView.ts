import { computed, type Ref } from 'vue';
import { TAG_FILTERS } from '@/features/catalog/model';
import { useListQuery } from '@/shared/useRouteQuery';
import {
  SHOPPING_SORTS,
  SHOPPING_STATUS_FILTERS,
  arrangeShoppingItems,
  type ShoppingItem,
  type ShoppingItemView,
} from './model';

export function useShoppingItemView(
  items: Ref<ShoppingItem[]>,
  findProductTags: (productId: number) => string[],
) {
  const { query, search, sort, isReversed } = useListQuery(SHOPPING_SORTS, 'added');
  const status = query.choiceParam('status', SHOPPING_STATUS_FILTERS, 'all');
  const tag = query.choiceParam('tag', TAG_FILTERS, 'all');

  const view = computed<ShoppingItemView>(() => ({
    search: search.value,
    status: status.value,
    tag: tag.value,
    sort: sort.value,
    isReversed: isReversed.value,
  }));
  const visibleItems = computed(() =>
    arrangeShoppingItems(items.value, view.value, findProductTags),
  );
  const pendingItems = computed(() =>
    visibleItems.value.filter((item) => item.status === 'pending'),
  );
  const purchasedItems = computed(() =>
    visibleItems.value.filter((item) => item.status === 'purchased'),
  );
  const isFiltered = computed(() => visibleItems.value.length < items.value.length);

  return { search, status, tag, sort, isReversed, pendingItems, purchasedItems, isFiltered };
}
