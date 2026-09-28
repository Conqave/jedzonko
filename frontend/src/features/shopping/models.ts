export interface ShoppingList {
  id: number;
  name: string;
  is_primary: boolean;
  item_count: number;
}

export interface ShoppingItem {
  id: number | null;
  product_id: number | null;
  product_name: string | null;
  free_text: string | null;
  quantity: string;
  unit_code: string | null;
  is_purchased: boolean;
  tag_names: string[];
}

export interface NewShoppingItem {
  product_id?: number;
  free_text?: string;
  quantity: string;
  unit_code?: string;
}
