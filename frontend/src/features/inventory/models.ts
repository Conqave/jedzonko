export interface InventoryItem {
  id: number;
  ingredient_id: number;
  ingredient_name: string;
  quantity: string;
  unit_code: string;
  minimum_quantity: string | null;
  category_name: string | null;
  photo_url: string | null;
  below_minimum: boolean;
}

export interface NewInventoryItem {
  household_id: number;
  ingredient_id: number;
  quantity: string;
  unit_code: string;
  minimum_quantity?: string;
}
