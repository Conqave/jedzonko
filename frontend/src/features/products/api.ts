import { api } from '@/boot/api';
import type { TagProposal, MeasurementUnit, NewProduct, Product } from './models';

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

export async function fetchTagProposals(householdId: number): Promise<TagProposal[]> {
  const response = await api.get<TagProposal[]>(`/households/${householdId}/tag-proposals/`);
  return response.data;
}

export async function acceptTagProposal(proposalId: number): Promise<TagProposal> {
  const response = await api.post<TagProposal>(`/households/tag-proposals/${proposalId}/accept/`);
  return response.data;
}

export async function rejectTagProposal(proposalId: number): Promise<TagProposal> {
  const response = await api.post<TagProposal>(`/households/tag-proposals/${proposalId}/reject/`);
  return response.data;
}

export interface ProductTag {
  id: number;
  name: string;
  source: string;
  is_verified: boolean;
}

export async function fetchProductTags(productId: number): Promise<ProductTag[]> {
  const response = await api.get<ProductTag[]>(`/products/${productId}/tags/`);
  return response.data;
}

export async function addProductTag(productId: number, name: string): Promise<ProductTag> {
  const response = await api.post<ProductTag>(`/products/${productId}/tags/`, { name });
  return response.data;
}

export async function deleteProductTag(tagId: number): Promise<void> {
  await api.delete(`/products/tags/${tagId}/`);
}

export async function searchProductTags(householdId: number, search: string): Promise<string[]> {
  const response = await api.get<string[]>('/products/tags/', {
    params: { household_id: householdId, search },
  });
  return response.data;
}

export async function startTagAnalysis(
  householdId: number,
  productId?: number,
  item?: { id: number; text: string },
): Promise<string> {
  const payload =
    productId === undefined
      ? item === undefined
        ? {}
        : { item_id: item.id, text: item.text }
      : { product_id: productId };
  const response = await api.post<{ job_id: string }>(
    `/products/${householdId}/tag-analysis/`,
    payload,
  );
  return response.data.job_id;
}

export interface TagAnalysisStatus {
  id: string;
  status: 'running' | 'completed' | 'failed';
  processed: number;
  total: number;
  error: string | null;
}

export async function fetchTagAnalysisStatus(jobId: string): Promise<TagAnalysisStatus> {
  const response = await api.get<TagAnalysisStatus>(`/products/tag-analysis/${jobId}/`);
  return response.data;
}
