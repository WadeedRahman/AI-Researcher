import { apiClient, handleApiResponse } from './client'
import type { HealthResponse } from '@/types/api'

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<{ status: 'success'; result?: HealthResponse }>('/health')
  // Health endpoint returns data directly, not wrapped in ApiResponse
  return response.data as unknown as HealthResponse
}

