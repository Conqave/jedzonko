export interface ShoppingList {
  id: number;
  name: string;
  is_primary: boolean;
  item_count: number;
}

export interface ShoppingItem {
  id: number | null;
  ingredient_id: number | null;
  ingredient_name: string | null;
  free_text: string | null;
  quantity: string;
  unit_code: string | null;
  is_purchased: boolean;
}

export interface NewShoppingItem {
  ingredient_id?: number;
  free_text?: string;
  quantity: string;
  unit_code?: string;
}
