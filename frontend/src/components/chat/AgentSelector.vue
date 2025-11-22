<template>
  <div class="agent-selector">
    <div class="selector-header">
      <h3>Agent Types</h3>
      <p class="subtitle">Select research capabilities</p>
    </div>
    <div class="agent-options">
      <div
        v-for="agent in agents"
        :key="agent.name"
        :class="['agent-option', { active: selectedAgents.includes(agent.name) }]"
        @click="toggleAgent(agent.name)"
      >
        <div class="agent-checkbox">
          <svg v-if="selectedAgents.includes(agent.name)" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M13.3333 4L6 11.3333L2.66667 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="agent-info">
          <h4>{{ agent.name }}</h4>
          <p>{{ agent.description }}</p>
          <p v-if="agent.name === 'Paper Generation Agent'" class="agent-warning">
            ⚠️ Requires a completed research job first. Run "Detailed Idea Description" or "Reference-Based Ideation" before using this agent.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Agent {
  name: string
  description: string
}

const props = defineProps<{
  agents: Agent[]
  modelValue: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const selectedAgents = ref<string[]>([...props.modelValue])

watch(() => props.modelValue, (newValue) => {
  selectedAgents.value = [...newValue]
}, { deep: true })

function toggleAgent(agentName: string) {
  const index = selectedAgents.value.indexOf(agentName)
  if (index > -1) {
    selectedAgents.value.splice(index, 1)
  } else {
    selectedAgents.value.push(agentName)
  }
  emit('update:modelValue', [...selectedAgents.value])
}
</script>

<style scoped>
.agent-selector {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.selector-header {
  margin-bottom: var(--spacing-lg);
}

.selector-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 var(--spacing-xs) 0;
}

.subtitle {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.agent-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.agent-option {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--transition);
  background: var(--color-surface-elevated);
}

.agent-option:hover {
  border-color: var(--color-border-light);
  background: var(--color-surface);
}

.agent-option.active {
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.1);
}

.agent-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
  transition: all var(--transition);
  background: var(--color-surface);
}

.agent-option.active .agent-checkbox {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-info h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 var(--spacing-xs) 0;
}

.agent-info p {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.agent-warning {
  margin-top: var(--spacing-xs) !important;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid var(--color-warning);
  border-radius: var(--radius-sm);
  color: var(--color-warning) !important;
  font-size: 0.8125rem !important;
  font-weight: 500;
}
</style>

