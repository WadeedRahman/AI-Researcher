<template>
  <div class="job-detail-view">
    <div class="container">
      <div v-if="isLoading" class="loading">
        <div class="spinner"></div>
        <p>Loading job details...</p>
      </div>

      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>

      <div v-else-if="job" class="job-detail">
        <div class="job-header card">
          <div class="header-top">
            <h1>Job: {{ job.id.substring(0, 8) }}...</h1>
            <span :class="['status-badge', `status-${job.status}`]">
              {{ job.status }}
            </span>
          </div>
          <div class="job-meta">
            <p><strong>Mode:</strong> {{ job.payload.mode }}</p>
            <p><strong>Created:</strong> {{ formatDate(job.created_at) }}</p>
            <p v-if="job.started_at">
              <strong>Started:</strong> {{ formatDate(job.started_at) }}
            </p>
            <p v-if="job.finished_at">
              <strong>Finished:</strong> {{ formatDate(job.finished_at) }}
            </p>
          </div>
          <div v-if="job.status === 'running' || job.status === 'pending'" class="actions">
            <button @click="handleCancel" class="button button-danger">
              Cancel Job
            </button>
          </div>
        </div>

        <div class="job-content">
          <div class="card">
            <h2>Progress</h2>
            <div v-if="job.progress.current_agent" class="progress-info">
              <p><strong>Current Agent:</strong> {{ job.progress.current_agent }}</p>
            </div>
            <div v-if="job.progress.subtasks.length > 0" class="subtasks">
              <h3>Subtasks</h3>
              <ul>
                <li
                  v-for="subtask in job.progress.subtasks"
                  :key="subtask.id"
                  :class="['subtask', `subtask-${subtask.status}`]"
                >
                  {{ subtask.name }} - {{ subtask.status }}
                </li>
              </ul>
            </div>
          </div>

          <div class="card">
            <h2>Logs</h2>
            <div class="logs-container">
              <div v-if="logs.length === 0" class="empty-logs">
                No logs available yet.
              </div>
              <div v-else class="logs">
                <div
                  v-for="(log, index) in logs"
                  :key="index"
                  class="log-entry"
                >
                  <div v-if="log.user" class="log-user">
                    <strong>User:</strong>
                    <pre>{{ log.user }}</pre>
                  </div>
                  <div v-if="log.assistant" class="log-assistant">
                    <strong>Assistant:</strong>
                    <pre>{{ log.assistant }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="job.result" class="card">
            <h2>Result</h2>
            <pre class="result-content">{{ JSON.stringify(job.result, null, 2) }}</pre>
          </div>

          <div v-if="job.error" class="card error-card">
            <h2>Error</h2>
            <p class="error-text">{{ job.error }}</p>
          </div>

          <div class="card">
            <h2>Token Usage</h2>
            <div class="token-usage">
              <p><strong>Completion Tokens:</strong> {{ job.token_usage.completion_tokens }}</p>
              <p><strong>Prompt Tokens:</strong> {{ job.token_usage.prompt_tokens }}</p>
              <p><strong>Total Tokens:</strong> {{ job.token_usage.total_tokens }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJobStore } from '@/stores/job'
import { useLogsStore } from '@/stores/logs'
import { useLogStreaming } from '@/composables/useLogStreaming'
import { usePolling } from '@/utils/polling'

const route = useRoute()
const router = useRouter()
const jobStore = useJobStore()
const logsStore = useLogsStore()

const jobId = computed(() => route.params.id as string)
const job = computed(() => jobStore.jobs.get(jobId.value))
const isLoading = computed(() => jobStore.isLoading)
const error = computed(() => jobStore.error)

const { logs, startStreaming, stop } = useLogStreaming(jobId.value)
const { poll, stopPolling } = usePolling()

let stopJobPolling: (() => void) | null = null

onMounted(async () => {
  await jobStore.fetchJob(jobId.value)
  jobStore.setCurrentJob(jobId.value)

  // Start polling for job status if still active
  // Use jobId as key to prevent duplicate polling
  const currentJob = jobStore.jobs.get(jobId.value)
  if (currentJob && ['pending', 'running'].includes(currentJob.status)) {
    stopJobPolling = poll(
      async () => {
        await jobStore.fetchJob(jobId.value)
        const updatedJob = jobStore.jobs.get(jobId.value)
        return updatedJob
      },
      {
        interval: 3000, // Increased to 3 seconds minimum
        maxInterval: 10000, // Cap at 10 seconds
        immediate: false, // Wait before first poll
        until: (currentJob) => {
          if (!currentJob) return true
          return !['pending', 'running'].includes(currentJob.status)
        },
      },
      `job-status-${jobId.value}` // Prevent duplicate polling
    )
  }

  // Start log streaming (will use its own deduplication)
  startStreaming()
})

onUnmounted(() => {
  stop()
  if (stopJobPolling) {
    stopJobPolling()
  }
  stopPolling()
})

async function handleCancel() {
  if (confirm('Are you sure you want to cancel this job?')) {
    try {
      await jobStore.cancelJob(jobId.value)
      await jobStore.fetchJob(jobId.value)
    } catch (err) {
      console.error('Failed to cancel job:', err)
    }
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}
</script>

<style scoped>
.job-detail-view {
  padding: var(--spacing-2xl) 0;
}

.loading {
  text-align: center;
  padding: var(--spacing-3xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
}

.loading p {
  color: var(--color-text-secondary);
}

.job-header {
  margin-bottom: var(--spacing-2xl);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.header-top h1 {
  margin: 0;
  font-size: clamp(1.5rem, 4vw, 2.25rem);
  color: var(--color-text);
  font-weight: 700;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.status-badge::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-pending {
  background-color: rgba(245, 158, 11, 0.2);
  color: var(--color-warning);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-pending::before {
  background-color: var(--color-warning);
  animation: pulse 2s infinite;
}

.status-running {
  background-color: rgba(59, 130, 246, 0.2);
  color: var(--color-info);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.status-running::before {
  background-color: var(--color-info);
  animation: pulse 2s infinite;
}

.status-succeeded {
  background-color: rgba(16, 185, 129, 0.2);
  color: var(--color-success);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-succeeded::before {
  background-color: var(--color-success);
}

.status-failed {
  background-color: rgba(239, 68, 68, 0.2);
  color: var(--color-error);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.status-failed::before {
  background-color: var(--color-error);
}

.status-cancelled {
  background-color: rgba(107, 114, 128, 0.2);
  color: var(--color-text-muted);
  border: 1px solid rgba(107, 114, 128, 0.3);
}

.status-cancelled::before {
  background-color: var(--color-text-muted);
}

.job-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--color-surface-elevated);
  border-radius: var(--radius);
  margin-bottom: var(--spacing-lg);
}

.job-meta p {
  margin: 0;
  font-size: 0.9375rem;
}

.job-meta strong {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-xs);
}

.actions {
  margin-top: var(--spacing-lg);
}

.job-content {
  display: grid;
  gap: var(--spacing-lg);
}

.card h2 {
  margin-top: 0;
  margin-bottom: var(--spacing-lg);
  color: var(--color-text);
  font-size: 1.5rem;
  font-weight: 600;
}

.progress-info {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-surface-elevated);
  border-radius: var(--radius);
  border-left: 3px solid var(--color-primary);
}

.progress-info p {
  margin: 0;
  font-size: 0.9375rem;
}

.progress-info strong {
  color: var(--color-text-secondary);
  margin-right: var(--spacing-sm);
}

.subtasks {
  margin-top: var(--spacing-lg);
}

.subtasks h3 {
  font-size: 1.125rem;
  margin-bottom: var(--spacing-md);
  color: var(--color-text);
}

.subtasks ul {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.subtask {
  padding: var(--spacing-md);
  border-radius: var(--radius);
  background-color: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  font-size: 0.9375rem;
  transition: all var(--transition);
}

.subtask:hover {
  border-color: var(--color-border-light);
  background-color: var(--color-surface);
}

.logs-container {
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-elevated);
}

.empty-logs {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
}

.log-entry {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.log-entry:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.log-user,
.log-assistant {
  margin-bottom: var(--spacing-md);
}

.log-user:last-child,
.log-assistant:last-child {
  margin-bottom: 0;
}

.log-user strong,
.log-assistant strong {
  display: block;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.log-user pre,
.log-assistant pre {
  margin: 0;
  padding: var(--spacing-md);
  background-color: var(--color-background);
  border-radius: var(--radius);
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.875rem;
  line-height: 1.6;
  border: 1px solid var(--color-border);
}

.result-content {
  padding: var(--spacing-lg);
  background-color: var(--color-surface-elevated);
  border-radius: var(--radius);
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
  font-size: 0.875rem;
  line-height: 1.6;
  border: 1px solid var(--color-border);
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
}

.error-card {
  border: 2px solid var(--color-error);
  background-color: rgba(239, 68, 68, 0.05);
}

.error-text {
  color: var(--color-error);
  font-weight: 500;
  padding: var(--spacing-md);
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius);
}

.token-usage {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-md);
}

.token-usage p {
  margin: 0;
  padding: var(--spacing-sm);
  background: var(--color-surface-elevated);
  border-radius: var(--radius);
  font-size: 0.9375rem;
}

.token-usage strong {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-xs);
}

@media (max-width: 768px) {
  .header-top {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .job-meta {
    grid-template-columns: 1fr;
  }
  
  .token-usage {
    grid-template-columns: 1fr;
  }
}
</style>

