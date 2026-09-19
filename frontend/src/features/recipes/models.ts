export interface RecipeSummary {
  id: number;
  name: string;
  description: string;
  servings: number;
  preparation_time_minutes: number;
  cooking_time_minutes: number;
  difficulty: string;
  category_name: string | null;
  tags: string[];
  image_url: string | null;
}

export interface RecipeStep {
  position: number;
  text: string;
}

export interface RecipeIngredient {
  name: string;
  quantity: string;
  unit_code: string;
}

export interface RecipeDetail extends RecipeSummary {
  steps: RecipeStep[];
  ingredients: RecipeIngredient[];
}

export interface MissingItem {
  name: string;
  amount: string;
  unit_code: string;
}

export interface RecipeSuggestion {
  recipe_id: number;
  recipe_name: string;
  available_item_count: number;
  missing_item_count: number;
  missing_items: MissingItem[];
}
