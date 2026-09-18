import { api } from '@/boot/api';
import type { Ingredient, MeasurementUnit } from './models';

export async function searchIngredients(search: string): Promise<Ingredient[]> {
  const response = await api.get<Ingredient[]>('/catalog/ingredients/', { params: { search } });
  return response.data;
}

export async function fetchUnits(): Promise<MeasurementUnit[]> {
  const response = await api.get<MeasurementUnit[]>('/catalog/units/');
  return response.data;
}
