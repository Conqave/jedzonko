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
  author_username: string;
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

export interface RecipeShortfall {
  missing_items: MissingItem[];
  required_item_count: number;
  available_item_count: number;
  unmeasured_ingredients: string[];
  is_ready: boolean;
}

export interface RecipeSuggestion extends RecipeShortfall {
  recipe_id: number;
  recipe_name: string;
  missing_item_count: number;
}

export interface ExternalRecipeIngredient {
  source_text: string;
  name: string;
  quantity: string | null;
  unit_code: string | null;
}

export interface ExternalRecipe {
  source_name: string;
  source_url: string;
  reference: string;
  name: string;
  description: string;
  image_url: string | null;
  yield_label: string;
  total_time_minutes: number | null;
  preparation_time_minutes: number;
  cooking_time_minutes: number;
  tags: string[];
  steps: string[];
  ingredients: ExternalRecipeIngredient[];
}

export interface RecipeInput {
  name: string;
  description: string;
  servings: number;
  preparation_time_minutes: number;
  cooking_time_minutes: number;
  difficulty: string;
  tag_names: string[];
  steps: RecipeStep[];
  ingredients: RecipeIngredient[];
}
