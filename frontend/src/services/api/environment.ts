import { apiClient, handleApiResponse } from './client'
import type {
  Mode,
  EnvItem,
  EnvVarInfo,
  EnvValidationResponse,
  PreflightRequest,
  PreflightResponse,
} from '@/types/api'

export async function getModes(): Promise<Mode[]> {
  const response = await apiClient.get('/modes')
  return handleApiResponse<Mode[]>(response.data)
}

export async function getEnvVars(): Promise<Record<string, EnvVarInfo>> {
  const response = await apiClient.get('/env')
  return handleApiResponse<Record<string, EnvVarInfo>>(response.data)
}

export async function updateEnvVar(key: string, value: string): Promise<void> {
  await apiClient.post('/env', [{ key, value }])
}

export async function updateEnvVars(vars: EnvItem[]): Promise<void> {
  await apiClient.put('/env', vars)
}

export async function deleteEnvVar(key: string): Promise<void> {
  await apiClient.delete(`/env/${key}`)
}

export async function validateEnv(mode: string): Promise<EnvValidationResponse> {
  const response = await apiClient.get('/env/validate', { params: { mode } })
  return handleApiResponse<EnvValidationResponse>(response.data)
}

export async function preflightCheck(request: PreflightRequest): Promise<PreflightResponse> {
  const response = await apiClient.post('/preflight', request)
  // Preflight returns data directly
  return response.data as unknown as PreflightResponse
}

