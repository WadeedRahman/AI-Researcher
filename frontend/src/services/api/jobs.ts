import { apiClient, handleApiResponse } from './client'
import type {
  RunRequest,
  JobInfo,
  JobSubmissionResponse,
  JobsListResponse,
  JobProgress,
  LogsResponse,
  TokenUsage,
  JobResultResponse,
  ListJobsParams,
} from '@/types/api'

export async function submitJob(payload: RunRequest): Promise<string> {
  const response = await apiClient.post<{ status: 'queued'; job_id: string }>('/jobs', payload)
  return response.data.job_id
}

export async function getJob(jobId: string): Promise<JobInfo> {
  const response = await apiClient.get(`/jobs/${jobId}`)
  return handleApiResponse<JobInfo>(response.data)
}

export async function listJobs(params?: ListJobsParams): Promise<JobsListResponse> {
  const response = await apiClient.get('/jobs', { params })
  const result = handleApiResponse<JobsListResponse>(response.data)
  
  // Ensure jobs array exists and is valid
  if (!result || !result.jobs) {
    return {
      jobs: [],
      total: 0,
      limit: params?.limit || 10,
      offset: params?.offset || 0,
    }
  }
  
  // Filter out any invalid jobs
  result.jobs = result.jobs.filter((job) => job && job.id)
  
  return result
}

export async function getJobProgress(jobId: string): Promise<JobProgress> {
  const response = await apiClient.get(`/jobs/${jobId}/progress`)
  return handleApiResponse<JobProgress>(response.data)
}

export async function getJobLogs(
  jobId: string,
  lastIndex = 0,
  maxLines = 500
): Promise<LogsResponse> {
  const response = await apiClient.get(`/jobs/${jobId}/logs`, {
    params: { last_index: lastIndex, max_lines: maxLines },
  })
  return handleApiResponse<LogsResponse>(response.data)
}

export async function getJobTokens(jobId: string): Promise<TokenUsage> {
  const response = await apiClient.get(`/jobs/${jobId}/tokens`)
  return handleApiResponse<TokenUsage>(response.data)
}

export async function getJobResult(jobId: string): Promise<JobResultResponse> {
  const response = await apiClient.get(`/jobs/${jobId}/result`)
  return handleApiResponse<JobResultResponse>(response.data)
}

export async function cancelJob(jobId: string): Promise<void> {
  await apiClient.post(`/jobs/${jobId}/cancel`)
}

export async function runAgentSync(payload: RunRequest): Promise<{
  answer: string
  token_count: string
  status: string
}> {
  const response = await apiClient.post('/run', payload)
  return handleApiResponse<{
    answer: string
    token_count: string
    status: string
  }>(response.data)
}

