export interface PromotionOffer {
  provider_offer_id: string | null;
  name: string;
  shop_name: string;
  shop_url: string;
  image_url: string;
  product_brand_name: string | null;
  price: string | null;
  leaflet_provider_id: string;
  leaflet_url: string;
  page_number: number;
  valid_from: string;
  valid_until: string;
}

export interface StorePromotionCoverage {
  shop_name: string;
  shop_url: string;
  matched_query_count: number;
  matched_queries: string[];
  offers: PromotionOffer[];
}
