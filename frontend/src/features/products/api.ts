import { api } from '@/boot/api';
import type { MeasurementUnit, NewProduct, Product } from './models';

export async function searchProducts(householdId: number, search: string): Promise<Product[]> {
  const response = await api.get<Product[]>('/products/', {
    params: { household_id: householdId, search },
  });
  return response.data;
}

export async function createProduct(product: NewProduct): Promise<Product> {
  const response = await api.post<Product>('/products/', product);
  return response.data;
}

export async function fetchUnits(): Promise<MeasurementUnit[]> {
  const response = await api.get<MeasurementUnit[]>('/units/');
  return response.data;
}
