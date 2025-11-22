import { computed, onUnmounted } from 'vue'
import { useLogsStore } from '@/stores/logs'
import { useSessionStore } from '@/stores/session'
import { usePolling } from '@/utils/polling'

export function useLogStreaming(jobId?: string) {
  const logsStore = useLogsStore()
  const sessionStore = useSessionStore()
  const { poll, stopPolling } = usePolling()

  let stopStreaming: (() => void) | null = null

  function startStreaming() {
    if (stopStreaming) {
      stopStreaming()
    }

    // Use jobId as key to prevent duplicate polling for the same job
    const pollKey = jobId ? `logs-${jobId}` : 'logs-global'
    
    stopStreaming = poll(
      async () => {
        if (jobId) {
          await logsStore.fetchJobLogs(jobId)
        } else {
          await logsStore.fetchGlobalLogs()
        }
      },
      {
        interval: Math.max(sessionStore.refreshInterval, 3000), // Minimum 3 seconds
        maxInterval: 10000, // Cap at 10 seconds
        immediate: false, // Don't poll immediately, wait for interval
      },
      pollKey // Prevent duplicate polling
    )
  }

  function stop() {
    if (stopStreaming) {
      stopStreaming()
      stopStreaming = null
    }
    stopPolling()
  }

  onUnmounted(() => {
    stop()
  })

  const logs = computed(() =>
    jobId ? logsStore.getJobLogs(jobId) : logsStore.globalLogs
  )

  return {
    startStreaming,
    stop,
    logs,
    isLoading: computed(() => logsStore.isLoading),
    error: computed(() => logsStore.error),
  }
}

