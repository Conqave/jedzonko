export interface Ingredient {
  id: number;
  name: string;
  default_unit_code: string;
}

export interface MeasurementUnit {
  code: string;
  name: string;
  dimension: 'mass' | 'volume' | 'count';
}
