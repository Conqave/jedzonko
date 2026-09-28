export interface Product {
  id: number;
  household_id: number;
  name: string;
  default_unit_code: string;
  is_food: boolean;
  tags?: string[];
}

export interface NewProduct {
  household_id: number;
  name: string;
  default_unit_code: string;
  is_food: boolean;
}

export interface MeasurementUnit {
  code: string;
  name: string;
  dimension: 'mass' | 'volume' | 'count';
}

export interface TagProposal {
  id: number;
  household_id: number;
  requirement_name: string;
  product_id: number;
  product_name: string;
  model_name: string;
  created_at: string;
  state: 'pending' | 'accepted' | 'rejected';
}
