<template>
  <div class="environment-view">
    <div class="container">
      <h1>Environment Configuration</h1>
      <p class="subtitle">Manage API keys and environment variables</p>

      <div v-if="isLoading" class="loading">
        <div class="spinner"></div>
        <p>Loading environment variables...</p>
      </div>

      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>

      <div v-else>
        <div class="card">
          <h2>Environment Variables</h2>
          <div class="env-table">
            <table>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                  <th>Source</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(info, key) in envVars" :key="key">
                  <td>{{ key }}</td>
                  <td>
                    <input
                      v-model="envValues[key]"
                      type="password"
                      class="input"
                      :placeholder="maskValue(info.value)"
                    />
                  </td>
                  <td>{{ info.source }}</td>
                  <td>
                    <button
                      @click="updateEnvVar(key)"
                      class="button button-primary"
                      :disabled="isSaving"
                    >
                      Save
                    </button>
                  </td>
                </tr>
                <tr v-if="Object.keys(envVars).length === 0">
                  <td colspan="4" class="empty-state">
                    No environment variables found.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="actions">
            <button @click="refreshEnvVars" class="button button-secondary">
              Refresh
            </button>
          </div>
        </div>

        <div class="card">
          <h2>Add New Variable</h2>
          <div class="add-variable-form">
            <input
              v-model="newVarKey"
              type="text"
              class="input"
              placeholder="Variable name (e.g., OPENAI_API_KEY)"
            />
            <input
              v-model="newVarValue"
              type="password"
              class="input"
              placeholder="Variable value"
            />
            <button
              @click="addEnvVar"
              class="button button-primary"
              :disabled="!newVarKey || !newVarValue || isSaving"
            >
              Add Variable
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEnvironmentStore } from '@/stores/environment'

const environmentStore = useEnvironmentStore()

const envVars = computed(() => environmentStore.envVars)
const isLoading = computed(() => environmentStore.isLoading)
const error = computed(() => environmentStore.error)

const envValues = ref<Record<string, string>>({})
const newVarKey = ref('')
const newVarValue = ref('')
const isSaving = ref(false)

onMounted(async () => {
  await environmentStore.fetchEnvVars()
  // Initialize envValues with current values
  Object.keys(envVars.value).forEach((key) => {
    envValues.value[key] = envVars.value[key].value
  })
})

async function refreshEnvVars() {
  await environmentStore.fetchEnvVars()
  Object.keys(envVars.value).forEach((key) => {
    envValues.value[key] = envVars.value[key].value
  })
}

async function updateEnvVar(key: string) {
  isSaving.value = true
  try {
    await environmentStore.updateEnvVar(key, envValues.value[key] || '')
    alert('Environment variable updated successfully!')
    await refreshEnvVars()
  } catch (err: any) {
    alert(`Failed to update: ${err.message}`)
  } finally {
    isSaving.value = false
  }
}

async function addEnvVar() {
  if (!newVarKey.value || !newVarValue.value) return

  isSaving.value = true
  try {
    await environmentStore.updateEnvVar(newVarKey.value, newVarValue.value)
    alert('Environment variable added successfully!')
    newVarKey.value = ''
    newVarValue.value = ''
    await refreshEnvVars()
  } catch (err: any) {
    alert(`Failed to add: ${err.message}`)
  } finally {
    isSaving.value = false
  }
}

function maskValue(value: string): string {
  if (!value) return ''
  if (value.length <= 8) return '****'
  return value.substring(0, 4) + '****' + value.substring(value.length - 4)
}
</script>

<style scoped>
.environment-view {
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

.env-table {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-elevated);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background-color: var(--color-surface);
}

th,
td {
  padding: var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

th {
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  color: var(--color-text-secondary);
}

td input {
  width: 100%;
  max-width: 300px;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-secondary);
}

.actions {
  margin-top: var(--spacing-lg);
}

.add-variable-form {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: var(--spacing-md);
  align-items: end;
}

@media (max-width: 768px) {
  .add-variable-form {
    grid-template-columns: 1fr;
  }
}
</style>

