<template>
  <div class="jobs-view">
    <div class="container">
      <div class="page-header">
        <h1>Research Jobs</h1>
        <p class="subtitle">Manage and monitor your research jobs</p>
      </div>

      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading jobs...</p>
      </div>

      <div v-else-if="error" class="error-message card">
        <strong>Error:</strong> {{ error }}
      </div>

      <div v-else>
        <div v-if="!filteredJobList || filteredJobList.length === 0" class="empty-state card">
          <div class="empty-icon">📋</div>
          <h3>No jobs found</h3>
          <p>Start a new research job from the home page to get started.</p>
          <RouterLink to="/" class="button button-primary">Start Research</RouterLink>
        </div>

        <div v-else class="jobs-grid">
          <div
            v-for="job in filteredJobList"
            :key="job.id"
            class="job-card card"
            @click="navigateToJob(job.id)"
          >
            <div class="job-card-header">
              <div class="job-id">
                <span class="job-id-label">Job ID</span>
                <span class="job-id-value">{{ job.id?.substring(0, 12) || 'Unknown' }}...</span>
              </div>
              <span :class="['status-badge', `status-${job.status || 'unknown'}`]">
                <span class="status-dot"></span>
                {{ (job.status || 'unknown').toUpperCase() }}
              </span>
            </div>
            
            <div class="job-card-body">
              <div class="job-info-item">
                <span class="info-label">Mode</span>
                <span class="info-value">{{ job.payload?.mode || 'N/A' }}</span>
              </div>
              <div class="job-info-item">
                <span class="info-label">Created</span>
                <span class="info-value">{{ job.created_at ? formatDate(job.created_at) : 'N/A' }}</span>
              </div>
              <div v-if="job.finished_at" class="job-info-item">
                <span class="info-label">Finished</span>
                <span class="info-value">{{ formatDate(job.finished_at) }}</span>
              </div>
            </div>

            <div class="job-card-footer">
              <span class="view-details">View Details →</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useJobStore } from '@/stores/job'

const router = useRouter()
const jobStore = useJobStore()

const jobList = computed(() => jobStore.jobList || [])
const filteredJobList = computed(() => {
  return jobList.value.filter((job) => job && job.id && job.status)
})
const isLoading = computed(() => jobStore.isLoading)
const error = computed(() => jobStore.error)

onMounted(async () => {
  await jobStore.fetchJobList()
})

function navigateToJob(jobId: string) {
  router.push(`/jobs/${jobId}`)
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}
</script>

<style scoped>
.jobs-view {
  padding: var(--spacing-2xl) 0;
  min-height: calc(100vh - 200px);
}

.page-header {
  margin-bottom: var(--spacing-2xl);
  text-align: center;
}

.page-header h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  margin-bottom: var(--spacing-sm);
  color: var(--color-text);
}

.subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
}

.loading-state {
  text-align: center;
  padding: var(--spacing-3xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
}

.loading-state p {
  color: var(--color-text-secondary);
}

.error-message {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
  border: 1px solid var(--color-error);
  padding: var(--spacing-lg);
}

.error-message strong {
  display: block;
  margin-bottom: var(--spacing-xs);
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

.job-card {
  cursor: pointer;
  transition: all var(--transition);
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
}

.job-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
  border-color: var(--color-primary);
}

.job-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-lg);
  gap: var(--spacing-md);
}

.job-id {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  flex: 1;
}

.job-id-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.job-id-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.status-pending {
  background-color: rgba(245, 158, 11, 0.2);
  color: var(--color-warning);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.status-pending .status-dot {
  background-color: var(--color-warning);
  animation: pulse 2s infinite;
}

.status-running {
  background-color: rgba(59, 130, 246, 0.2);
  color: var(--color-info);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.status-running .status-dot {
  background-color: var(--color-info);
  animation: pulse 2s infinite;
}

.status-succeeded {
  background-color: rgba(16, 185, 129, 0.2);
  color: var(--color-success);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-succeeded .status-dot {
  background-color: var(--color-success);
}

.status-failed {
  background-color: rgba(239, 68, 68, 0.2);
  color: var(--color-error);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.status-failed .status-dot {
  background-color: var(--color-error);
}

.status-cancelled {
  background-color: rgba(107, 114, 128, 0.2);
  color: var(--color-text-muted);
  border: 1px solid rgba(107, 114, 128, 0.3);
}

.status-cancelled .status-dot {
  background-color: var(--color-text-muted);
}

.job-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.job-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.job-info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 0.875rem;
  color: var(--color-text);
  text-align: right;
}

.job-card-footer {
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}

.view-details {
  font-size: 0.875rem;
  color: var(--color-primary);
  font-weight: 500;
  transition: all var(--transition);
}

.job-card:hover .view-details {
  transform: translateX(4px);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-3xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.empty-state h3 {
  color: var(--color-text);
  margin: 0;
}

.empty-state p {
  color: var(--color-text-secondary);
  max-width: 400px;
}

@media (max-width: 768px) {
  .jobs-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    margin-bottom: var(--spacing-xl);
  }
}
</style>

