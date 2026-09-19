export interface InventoryItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: string;
  unit_code: string;
  minimum_quantity: string | null;
  category_name: string | null;
  photo_url: string | null;
  below_minimum: boolean;
}

export interface NewInventoryItem {
  household_id: number;
  product_id: number;
  quantity: string;
  unit_code: string;
  minimum_quantity?: string;
}
