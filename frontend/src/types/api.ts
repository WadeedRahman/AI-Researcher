// API Response Types

export interface ApiResponse<T> {
  status: 'success' | 'error'
  result?: T
  detail?: string
}

export interface HealthResponse {
  status: string
  timestamp: string
  version: string
}

export interface RunRequest {
  question: string
  reference?: string
  mode: 'Idea Spark' | 'Deep Survey' | 'Auto Experiment' | 'Detailed Idea Description' | 'Reference-Based Ideation' | 'Paper Generation Agent'
}

export interface PreflightRequest {
  mode: string
  category?: string | null
  instance_id?: string | null
}

export interface PreflightResponse {
  status: 'success' | 'error'
  valid: boolean
  errors: string[]
  warnings: string[]
  category?: string | null
  instance_id?: string | null
}

export interface Mode {
  name: string
  description: string
  required_env_vars: string[]
}

export type JobStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'cancelled'

export interface JobInfo {
  id: string
  status: JobStatus
  created_at: string
  started_at?: string | null
  finished_at?: string | null
  payload: RunRequest
  result?: any | null
  error?: string | null
  log_file?: string | null
  progress: JobProgress
  token_usage: TokenUsage
}

export interface JobProgress {
  current_agent?: string | null
  current_step?: string | null
  subtasks: Subtask[]
  estimated_time_remaining?: string | null
}

export interface Subtask {
  id: string
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
}

export interface TokenUsage {
  completion_tokens: number
  prompt_tokens: number
  total_tokens: number
}

export interface Conversation {
  user: string | null
  assistant: string | null
}

export interface LogsResponse {
  conversations: Conversation[]
  last_index: number
  job_status?: string | null
}

export interface EnvItem {
  key: string
  value: string
}

export interface EnvVarInfo {
  value: string
  source: 'System' | '.env file' | 'Frontend configuration'
  api_guide?: string | null
}

export interface EnvValidationResponse {
  valid: boolean
  missing: string[]
  incorrect: string[]
  mode: string
}

export interface ListJobsParams {
  limit?: number
  offset?: number
  status?: JobStatus
}

export interface JobsListResponse {
  jobs: JobInfo[]
  total: number
  limit: number
  offset: number
}

