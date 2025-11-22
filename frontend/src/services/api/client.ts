import axios, { AxiosInstance, AxiosError } from 'axios'
import type { ApiResponse } from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// Track pending requests to enable cancellation
const pendingRequests = new Map<string, AbortController>()

export function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Generate request key from method and URL
      const requestKey = `${config.method?.toUpperCase()}_${config.url}`
      
      // Cancel previous request with same key if exists
      if (pendingRequests.has(requestKey)) {
        const oldController = pendingRequests.get(requestKey)
        if (oldController && !oldController.signal.aborted) {
          oldController.abort()
        }
      }
      
      // Create new abort controller for this request
      const controller = new AbortController()
      if (config.signal) {
        // If signal already exists, chain it
        config.signal.addEventListener('abort', () => controller.abort())
      } else {
        config.signal = controller.signal
      }
      
      // Store new controller
      pendingRequests.set(requestKey, controller)

      // Add auth token if available
      // const token = localStorage.getItem('token')
      // if (token) {
      //   config.headers.Authorization = `Bearer ${token}`
      // }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      // Remove from pending requests on success
      const requestKey = `${response.config.method?.toUpperCase()}_${response.config.url}`
      pendingRequests.delete(requestKey)
      return response
    },
    (error: AxiosError) => {
      // Remove from pending requests on error
      if (error.config) {
        const requestKey = `${error.config.method?.toUpperCase()}_${error.config.url}`
        pendingRequests.delete(requestKey)
      }

      // Don't treat aborted requests as errors
      if (error.code === 'ERR_CANCELED' || error.name === 'CanceledError') {
        return Promise.reject(new ApiError('Request cancelled', undefined, error.response?.data))
      }

      const apiError = new ApiError(
        error.message,
        error.response?.status,
        error.response?.data
      )

      // Handle specific error cases
      if (error.response?.status === 404) {
        apiError.message = error.response.data?.detail || 'Resource not found'
      } else if (error.response?.status === 500) {
        apiError.message = error.response.data?.detail || 'Internal server error'
      }

      return Promise.reject(apiError)
    }
  )

  return client
}

export const apiClient = createApiClient()

export function handleApiResponse<T>(responseData: ApiResponse<T>): T {
  if (!responseData) {
    throw new ApiError('Invalid API response: response data is null or undefined')
  }
  
  if (responseData.status === 'error') {
    throw new ApiError(responseData.detail || 'Unknown error')
  }
  
  if (responseData.result === undefined) {
    throw new ApiError('API response missing result data')
  }
  
  return responseData.result as T
}

