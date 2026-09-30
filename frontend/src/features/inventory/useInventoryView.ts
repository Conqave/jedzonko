import { computed, type Ref } from 'vue';
import { TAG_FILTERS, type MeasurementUnit } from '@/features/catalog/model';
import { useListQuery } from '@/shared/useRouteQuery';
import {
  INVENTORY_SORTS,
  arrangeInventoryItems,
  type InventoryItem,
  type InventoryView,
} from './model';

export function useInventoryView(
  items: Ref<InventoryItem[]>,
  findTags: (productId: number) => string[],
  units: Ref<MeasurementUnit[]>,
) {
  const { query, search, sort, isReversed } = useListQuery(INVENTORY_SORTS, 'name');
  const tag = query.choiceParam('tag', TAG_FILTERS, 'all');
  const isBelowMinimumOnly = query.flagParam('low');

  const view = computed<InventoryView>(() => ({
    search: search.value,
    tag: tag.value,
    isBelowMinimumOnly: isBelowMinimumOnly.value,
    sort: sort.value,
    isReversed: isReversed.value,
  }));
  const visibleItems = computed(() =>
    arrangeInventoryItems(items.value, view.value, findTags, units.value),
  );
  const isFiltered = computed(() => visibleItems.value.length < items.value.length);

  return { search, tag, isBelowMinimumOnly, sort, isReversed, visibleItems, isFiltered };
}
