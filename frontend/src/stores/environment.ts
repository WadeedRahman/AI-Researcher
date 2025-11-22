import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as envApi from '@/services/api/environment'
import type { EnvVarInfo, EnvValidationResponse, Mode, EnvItem } from '@/types/api'

export const useEnvironmentStore = defineStore('environment', () => {
  const envVars = ref<Record<string, EnvVarInfo>>({})
  const validation = ref<EnvValidationResponse | null>(null)
  const modes = ref<Mode[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const requiredVarsForMode = computed(() => {
    return (mode: string): string[] => {
      const modeData = modes.value.find((m) => m.name === mode)
      return modeData?.required_env_vars || []
    }
  })

  const isEnvValidForMode = computed(() => {
    return (mode: string): boolean => {
      if (!validation.value || validation.value.mode !== mode) return false
      return validation.value.valid
    }
  })

  async function fetchModes(): Promise<void> {
    try {
      isLoading.value = true
      error.value = null
      modes.value = await envApi.getModes()
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch modes'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchEnvVars(): Promise<void> {
    try {
      isLoading.value = true
      error.value = null
      envVars.value = await envApi.getEnvVars()
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch environment variables'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateEnvVar(key: string, value: string): Promise<void> {
    try {
      error.value = null
      await envApi.updateEnvVar(key, value)
      await fetchEnvVars() // Refresh
    } catch (err: any) {
      error.value = err.message || 'Failed to update environment variable'
      throw err
    }
  }

  async function updateEnvVars(vars: EnvItem[]): Promise<void> {
    try {
      error.value = null
      await envApi.updateEnvVars(vars)
      await fetchEnvVars() // Refresh
    } catch (err: any) {
      error.value = err.message || 'Failed to update environment variables'
      throw err
    }
  }

  async function deleteEnvVar(key: string): Promise<void> {
    try {
      error.value = null
      await envApi.deleteEnvVar(key)
      await fetchEnvVars() // Refresh
    } catch (err: any) {
      error.value = err.message || 'Failed to delete environment variable'
      throw err
    }
  }

  async function validateEnv(mode: string): Promise<void> {
    try {
      error.value = null
      validation.value = await envApi.validateEnv(mode)
    } catch (err: any) {
      error.value = err.message || 'Failed to validate environment'
      throw err
    }
  }

  return {
    envVars,
    validation,
    modes,
    isLoading,
    error,
    requiredVarsForMode,
    isEnvValidForMode,
    fetchModes,
    fetchEnvVars,
    updateEnvVar,
    updateEnvVars,
    deleteEnvVar,
    validateEnv,
  }
})

