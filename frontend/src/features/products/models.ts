export interface Product {
  id: number;
  household_id: number;
  name: string;
  default_unit_code: string;
  is_food: boolean;
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
