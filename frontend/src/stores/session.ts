import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'ai-researcher-session'

interface SessionData {
  activeJobIds: string[]
  viewMode: 'compact' | 'detailed'
  autoRefresh: boolean
  refreshInterval: number
  theme: 'light' | 'dark'
}

export const useSessionStore = defineStore('session', () => {
  const activeJobIds = ref<string[]>([])
  const viewMode = ref<'compact' | 'detailed'>('detailed')
  const autoRefresh = ref(true)
  const refreshInterval = ref(3000) // Default 3 seconds instead of 2
  const theme = ref<'light' | 'dark'>('dark')

  const hasActiveJobs = computed(() => activeJobIds.value.length > 0)

  function loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const data: SessionData = JSON.parse(stored)
        activeJobIds.value = data.activeJobIds || []
        viewMode.value = data.viewMode || 'detailed'
        autoRefresh.value = data.autoRefresh !== false
        refreshInterval.value = data.refreshInterval || 2000
        theme.value = data.theme || 'dark'
      }
    } catch (err) {
      console.error('Failed to load session from storage:', err)
    }
  }

  function saveToStorage(): void {
    try {
      const data: SessionData = {
        activeJobIds: activeJobIds.value,
        viewMode: viewMode.value,
        autoRefresh: autoRefresh.value,
        refreshInterval: refreshInterval.value,
        theme: theme.value,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (err) {
      console.error('Failed to save session to storage:', err)
    }
  }

  function addActiveJob(jobId: string): void {
    if (!activeJobIds.value.includes(jobId)) {
      activeJobIds.value.push(jobId)
      saveToStorage()
    }
  }

  function removeActiveJob(jobId: string): void {
    const index = activeJobIds.value.indexOf(jobId)
    if (index !== -1) {
      activeJobIds.value.splice(index, 1)
      saveToStorage()
    }
  }

  function setViewMode(mode: 'compact' | 'detailed'): void {
    viewMode.value = mode
    saveToStorage()
  }

  function setAutoRefresh(enabled: boolean): void {
    autoRefresh.value = enabled
    saveToStorage()
  }

  function setRefreshInterval(interval: number): void {
    refreshInterval.value = interval
    saveToStorage()
  }

  function setTheme(newTheme: 'light' | 'dark'): void {
    theme.value = newTheme
    saveToStorage()
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  // Initialize from storage
  loadFromStorage()

  return {
    activeJobIds,
    viewMode,
    autoRefresh,
    refreshInterval,
    theme,
    hasActiveJobs,
    addActiveJob,
    removeActiveJob,
    setViewMode,
    setAutoRefresh,
    setRefreshInterval,
    setTheme,
    saveToStorage,
    loadFromStorage,
  }
})

