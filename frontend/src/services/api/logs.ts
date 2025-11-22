import { apiClient, handleApiResponse } from './client'
import type { LogsResponse } from '@/types/api'

export async function getGlobalLogs(lastIndex = 0, maxLines = 500): Promise<LogsResponse> {
  const response = await apiClient.get('/logs', {
    params: { last_index: lastIndex, max_lines: maxLines },
  })
  return handleApiResponse<LogsResponse>(response.data)
}

export async function downloadLogs(): Promise<Blob> {
  const response = await apiClient.get('/logs/download', {
    responseType: 'blob',
  })
  return response.data
}

export async function downloadJobLogs(jobId: string): Promise<Blob> {
  const response = await apiClient.get(`/jobs/${jobId}/logs/download`, {
    responseType: 'blob',
  })
  return response.data
}

