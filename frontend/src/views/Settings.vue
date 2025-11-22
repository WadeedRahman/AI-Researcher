<template>
  <div class="settings-view">
    <div class="container">
      <h1>Settings</h1>
      <p class="subtitle">Configure application preferences</p>

      <div class="card">
        <h2>Display Settings</h2>
        <div class="setting-item">
          <label for="viewMode">View Mode</label>
          <select id="viewMode" v-model="viewMode" class="input" @change="updateViewMode">
            <option value="detailed">Detailed</option>
            <option value="compact">Compact</option>
          </select>
        </div>

        <div class="setting-item">
          <label for="theme">Theme</label>
          <select id="theme" v-model="theme" class="input" @change="updateTheme">
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>

      <div class="card">
        <h2>Polling Settings</h2>
        <div class="setting-item">
          <label>
            <input
              type="checkbox"
              v-model="autoRefresh"
              @change="updateAutoRefresh"
            />
            Auto-refresh enabled
          </label>
        </div>

        <div class="setting-item">
          <label for="refreshInterval">Refresh Interval (ms)</label>
          <input
            id="refreshInterval"
            v-model.number="refreshInterval"
            type="number"
            min="1000"
            max="10000"
            step="500"
            class="input"
            @change="updateRefreshInterval"
          />
          <p class="help-text">Recommended: 2000ms (2 seconds)</p>
        </div>
      </div>

      <div class="card">
        <h2>About</h2>
        <div class="about-info">
          <p><strong>Application:</strong> AI-Researcher Frontend</p>
          <p><strong>Version:</strong> 1.0.0</p>
          <p><strong>API Base URL:</strong> {{ apiBaseUrl }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '@/stores/session'

const sessionStore = useSessionStore()

const viewMode = computed({
  get: () => sessionStore.viewMode,
  set: (value) => sessionStore.setViewMode(value),
})

const theme = computed({
  get: () => sessionStore.theme,
  set: (value) => sessionStore.setTheme(value),
})

const autoRefresh = computed({
  get: () => sessionStore.autoRefresh,
  set: (value) => sessionStore.setAutoRefresh(value),
})

const refreshInterval = computed({
  get: () => sessionStore.refreshInterval,
  set: (value) => sessionStore.setRefreshInterval(value),
})

const apiBaseUrl = computed(() => import.meta.env.VITE_API_BASE_URL || 'Not configured')

function updateViewMode() {
  sessionStore.setViewMode(viewMode.value)
}

function updateTheme() {
  sessionStore.setTheme(theme.value)
}

function updateAutoRefresh() {
  sessionStore.setAutoRefresh(autoRefresh.value)
}

function updateRefreshInterval() {
  sessionStore.setRefreshInterval(refreshInterval.value)
}
</script>

<style scoped>
.settings-view {
  padding: var(--spacing-2xl) 0;
}

h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  margin-bottom: var(--spacing-sm);
  color: var(--color-text);
}

.subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-2xl);
}

.card {
  margin-bottom: var(--spacing-xl);
}

.card h2 {
  margin-top: 0;
  margin-bottom: var(--spacing-lg);
  color: var(--color-text);
  font-size: 1.5rem;
  font-weight: 600;
}

.setting-item {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-surface-elevated);
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}

.setting-item label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  color: var(--color-text);
  font-size: 0.9375rem;
}

.setting-item input[type="checkbox"] {
  margin-right: var(--spacing-sm);
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.setting-item input[type="number"] {
  max-width: 200px;
}

.help-text {
  margin-top: var(--spacing-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-style: italic;
}

.about-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.about-info p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
}

.about-info strong {
  color: var(--color-text);
  margin-right: var(--spacing-sm);
}
</style>

