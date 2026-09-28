import { computed, ref } from 'vue';
import { useApiAction } from '@/shared/useApiAction';
import { searchOffers } from './api';
import { PROMOTION_ERROR_MESSAGES } from './errors';
import { groupOffersByShop, type PromotionOffer } from './model';

const OFFERS_PER_PAGE = 20;

export function useOfferSearch() {
  const offers = ref<PromotionOffer[]>([]);
  const page = ref(1);
  const hasSearched = ref(false);
  const { busy, run } = useApiAction(PROMOTION_ERROR_MESSAGES);

  const pageCount = computed(() => Math.max(1, Math.ceil(offers.value.length / OFFERS_PER_PAGE)));

  const pageGroups = computed(() => {
    const start = (page.value - 1) * OFFERS_PER_PAGE;
    const pageOffers = offers.value.slice(start, start + OFFERS_PER_PAGE);
    return groupOffersByShop(pageOffers);
  });

  async function search(query: string, shopSlugs: string[]): Promise<void> {
    await run(async () => {
      offers.value = await searchOffers(query, shopSlugs);
      page.value = 1;
      hasSearched.value = true;
    });
  }

  return { offers, page, pageCount, pageGroups, hasSearched, busy, search };
}
