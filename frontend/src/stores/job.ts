import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as jobApi from '@/services/api/jobs'
import type { JobInfo, RunRequest, JobStatus, ListJobsParams } from '@/types/api'

export const useJobStore = defineStore('job', () => {
  const jobs = ref<Map<string, JobInfo>>(new Map())
  const currentJobId = ref<string | null>(null)
  const jobList = ref<JobInfo[]>([])
  const filters = ref<ListJobsParams>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const currentJob = computed(() => {
    if (!currentJobId.value) return null
    return jobs.value.get(currentJobId.value) || null
  })

  const filteredJobs = computed(() => {
    return jobList.value
  })

  const activeJobs = computed(() => {
    return jobList.value.filter(
      (job) => job.status === 'pending' || job.status === 'running'
    )
  })

  const completedJobs = computed(() => {
    return jobList.value.filter(
      (job) => job.status === 'succeeded' || job.status === 'failed' || job.status === 'cancelled'
    )
  })

  async function submitJob(payload: RunRequest): Promise<string> {
    try {
      isLoading.value = true
      error.value = null
      const jobId = await jobApi.submitJob(payload)
      // Fetch job details immediately
      await fetchJob(jobId)
      currentJobId.value = jobId
      return jobId
    } catch (err: any) {
      error.value = err.message || 'Failed to submit job'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchJob(jobId: string): Promise<void> {
    try {
      const job = await jobApi.getJob(jobId)
      jobs.value.set(jobId, job)
      // Update in jobList if present
      const index = jobList.value.findIndex((j) => j.id === jobId)
      if (index !== -1) {
        jobList.value[index] = job
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch job'
      throw err
    }
  }

  async function fetchJobList(params?: ListJobsParams): Promise<void> {
    try {
      isLoading.value = true
      error.value = null
      filters.value = params || {}
      const response = await jobApi.listJobs(params)
      
      // Ensure response.jobs is an array and filter out any null/undefined values
      const jobsArray = Array.isArray(response?.jobs) ? response.jobs : []
      jobList.value = jobsArray.filter((job) => job && job.id)
      
      // Update jobs map
      jobList.value.forEach((job) => {
        if (job && job.id) {
          jobs.value.set(job.id, job)
        }
      })
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch job list'
      // Set empty array on error to prevent undefined errors
      jobList.value = []
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function cancelJob(jobId: string): Promise<void> {
    try {
      await jobApi.cancelJob(jobId)
      await fetchJob(jobId) // Refresh job status
    } catch (err: any) {
      error.value = err.message || 'Failed to cancel job'
      throw err
    }
  }

  async function pollJobStatus(jobId: string): Promise<JobInfo | null> {
    try {
      await fetchJob(jobId)
      return jobs.value.get(jobId) || null
    } catch (err: any) {
      error.value = err.message || 'Failed to poll job status'
      return null
    }
  }

  function setCurrentJob(jobId: string | null): void {
    currentJobId.value = jobId
  }

  function clearJobs(): void {
    jobs.value.clear()
    jobList.value = []
    currentJobId.value = null
  }

  return {
    jobs,
    currentJobId,
    jobList,
    filters,
    isLoading,
    error,
    currentJob,
    filteredJobs,
    activeJobs,
    completedJobs,
    submitJob,
    fetchJob,
    fetchJobList,
    cancelJob,
    pollJobStatus,
    setCurrentJob,
    clearJobs,
  }
})

