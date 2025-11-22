import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as logsApi from '@/services/api/logs'
import * as jobApi from '@/services/api/jobs'
import type { Conversation } from '@/types/api'

export const useLogsStore = defineStore('logs', () => {
  const jobLogs = ref<Map<string, Conversation[]>>(new Map())
  const globalLogs = ref<Conversation[]>([])
  const lastIndex = ref<Map<string, number>>(new Map())
  const globalLastIndex = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const getJobLogs = computed(() => {
    return (jobId: string): Conversation[] => {
      return jobLogs.value.get(jobId) || []
    }
  })

  async function fetchJobLogs(jobId: string, startIndex?: number): Promise<void> {
    try {
      isLoading.value = true
      error.value = null
      const currentIndex = startIndex ?? lastIndex.value.get(jobId) ?? 0
      const response = await jobApi.getJobLogs(jobId, currentIndex)
      
      // Update last index
      lastIndex.value.set(jobId, response.last_index)
      
      // Append new conversations
      const existing = jobLogs.value.get(jobId) || []
      jobLogs.value.set(jobId, [...existing, ...response.conversations])
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch job logs'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchGlobalLogs(startIndex?: number): Promise<void> {
    try {
      isLoading.value = true
      error.value = null
      const currentIndex = startIndex ?? globalLastIndex.value
      const response = await logsApi.getGlobalLogs(currentIndex)
      
      // Update last index
      globalLastIndex.value = response.last_index
      
      // Append new conversations
      globalLogs.value = [...globalLogs.value, ...response.conversations]
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch global logs'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearJobLogs(jobId: string): void {
    jobLogs.value.delete(jobId)
    lastIndex.value.delete(jobId)
  }

  function clearGlobalLogs(): void {
    globalLogs.value = []
    globalLastIndex.value = 0
  }

  return {
    jobLogs,
    globalLogs,
    lastIndex,
    globalLastIndex,
    isLoading,
    error,
    getJobLogs,
    fetchJobLogs,
    fetchGlobalLogs,
    clearJobLogs,
    clearGlobalLogs,
  }
})

