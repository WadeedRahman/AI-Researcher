import { computed } from 'vue'
import { useJobStore } from '@/stores/job'
import { useLogsStore } from '@/stores/logs'
import { useSessionStore } from '@/stores/session'
import { usePolling } from '@/utils/polling'
import type { RunRequest, JobStatus } from '@/types/api'

export function useJobManagement() {
  const jobStore = useJobStore()
  const logsStore = useLogsStore()
  const sessionStore = useSessionStore()
  const { poll, stopPolling } = usePolling()

  async function submitAndPoll(payload: RunRequest) {
    const jobId = await jobStore.submitJob(payload)
    sessionStore.addActiveJob(jobId)
    jobStore.setCurrentJob(jobId)

    // Use keys to prevent duplicate polling - only poll from job management, not from detail page
    // The detail page will handle its own polling when user navigates there

    return {
      jobId,
      stop: () => {
        // Stop polling will be handled by the detail page or when job completes
        stopPolling()
      },
    }
  }

  async function cancelJob(jobId: string) {
    await jobStore.cancelJob(jobId)
    sessionStore.removeActiveJob(jobId)
    stopPolling()
  }

  const currentJob = computed(() => jobStore.currentJob)

  return {
    submitAndPoll,
    cancelJob,
    currentJob,
    isLoading: computed(() => jobStore.isLoading),
    error: computed(() => jobStore.error),
  }
}

