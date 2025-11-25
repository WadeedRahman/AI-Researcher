<template>
  <div class="agent-message" :class="{ loading: isLoading }">
    <div class="message-content">
      <div class="message-avatar">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 0C4.47715 0 0 4.47715 0 10C0 15.5228 4.47715 20 10 20C15.5228 20 20 15.5228 20 10C20 4.47715 15.5228 0 10 0ZM10 18C5.58172 18 2 14.4183 2 10C2 5.58172 5.58172 2 10 2C14.4183 2 18 5.58172 18 10C18 14.4183 14.4183 18 10 18Z" fill="currentColor"/>
          <path d="M9 5H11V7H9V5ZM9 9H11V15H9V9Z" fill="currentColor"/>
        </svg>
      </div>
      <div class="message-body">
        <div v-if="isLoading" class="loading-container">
          <div class="loading-content">
            <div class="loading-spinner">
              <div class="spinner-ring"></div>
              <div class="spinner-ring"></div>
              <div class="spinner-ring"></div>
            </div>
            <div class="loading-text">
              <span class="loading-title">Processing your request...</span>
              <span class="loading-subtitle">This may take a few moments</span>
            </div>
          </div>
          <!-- Overall Progress Indicator -->
          <div v-if="overallProgress > 0" class="overall-progress-container">
            <div class="overall-progress-header">
              <span class="overall-progress-label">Overall Progress</span>
              <span class="overall-progress-percentage">{{ overallProgress }}%</span>
            </div>
            <div class="overall-progress-bar">
              <div class="overall-progress-fill" :style="{ width: overallProgress + '%' }"></div>
            </div>
          </div>
          <div v-if="progress && progress.length > 0" class="progress-container">
            <div class="progress-card" v-for="(item, index) in progress" :key="index">
              <div class="progress-icon">
                <svg v-if="item.includes('Current Agent')" width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 0L10.5 5.5L16 8L10.5 10.5L8 16L5.5 10.5L0 8L5.5 5.5L8 0Z" fill="currentColor"/>
                </svg>
                <svg v-else-if="item.includes('Step')" width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 2L14 2L14 4L2 4L2 2ZM2 6L14 6L14 8L2 8L2 6ZM2 10L14 10L14 12L2 12L2 10ZM2 14L10 14L10 16L2 16L2 14Z" fill="currentColor"/>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 0C3.58 0 0 3.58 0 8C0 12.42 3.58 16 8 16C12.42 16 16 12.42 16 8C16 3.58 12.42 0 8 0ZM6.5 12L2.5 8L3.91 6.59L6.5 9.17L12.09 3.58L13.5 5L6.5 12Z" fill="currentColor"/>
                </svg>
              </div>
              <div class="progress-info">
                <span class="progress-label">{{ formatProgressLabel(item) }}</span>
                <div v-if="item.includes('subtasks')" class="progress-bar-container">
                  <div class="progress-bar">
                    <div class="progress-bar-fill" :style="{ width: getProgressPercentage(item) + '%' }"></div>
                  </div>
                  <span class="progress-percentage">{{ getProgressPercentage(item) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="message" class="message-text">
          <div v-if="isStreaming" class="streaming-content">
            <div class="markdown-content" v-html="formatMarkdown(message)"></div>
            <span class="cursor">▋</span>
          </div>
          <div v-else class="markdown-content" v-html="formatMarkdown(message)"></div>
          <div v-if="progress && progress.length > 0" class="progress-container-inline">
            <div class="progress-badge" v-for="(item, index) in progress" :key="index">
              <span class="progress-badge-icon">●</span>
              <span>{{ formatProgressLabel(item) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  message?: string
  isLoading?: boolean
  isStreaming?: boolean
  progress?: string[]
}>()

function formatProgressLabel(item: string): string {
  // Remove prefixes like "Current Agent:", "Step:", "Progress:"
  return item.replace(/^(Current Agent|Step|Progress):\s*/i, '').trim()
}

function getProgressPercentage(item: string): number {
  // Extract percentage from "Progress: X/Y subtasks completed"
  const match = item.match(/(\d+)\/(\d+)/)
  if (match) {
    const completed = parseInt(match[1])
    const total = parseInt(match[2])
    return total > 0 ? Math.round((completed / total) * 100) : 0
  }
  return 0
}

// Calculate overall progress percentage from all progress items
const overallProgress = computed(() => {
  if (!props.progress || props.progress.length === 0) {
    return 0
  }
  
  // Find the subtasks progress item
  const subtasksItem = props.progress.find(item => item.includes('subtasks'))
  if (subtasksItem) {
    return getProgressPercentage(subtasksItem)
  }
  
  // If no subtasks but we have progress info, estimate based on current agent
  // This gives at least some indication of progress
  const currentAgentItem = props.progress.find(item => item.includes('Current Agent'))
  if (currentAgentItem) {
    // Estimate progress based on which agent is running
    // This is a rough estimate: each agent represents ~15-20% progress
    const agentNames = ['Prepare Agent', 'Survey Agent', 'Plan Agent', 'ML Agent', 'Judge Agent', 'Exp Analyser']
    const currentAgent = formatProgressLabel(currentAgentItem)
    const agentIndex = agentNames.findIndex(name => currentAgent.includes(name))
    if (agentIndex >= 0) {
      // Base progress: (agent_index + 1) * 15%, capped at 90% until completion
      return Math.min((agentIndex + 1) * 15, 90)
    }
  }
  
  return 0
})

// Simple markdown formatter (basic support for headers, bold, italic, code blocks, lists)
function formatMarkdown(text: string): string {
  if (!text) return ''
  
  let html = text
  
  // Code blocks (triple backticks) - process FIRST before escaping
  const codeBlockPlaceholders: string[] = []
  html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
    const placeholder = `__CODEBLOCK_${codeBlockPlaceholders.length}__`
    codeBlockPlaceholders.push(code)
    return placeholder
  })
  
  // Escape HTML (but preserve code block placeholders)
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // Restore code blocks with proper escaping
  codeBlockPlaceholders.forEach((code, index) => {
    const escapedCode = code
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    html = html.replace(`__CODEBLOCK_${index}__`, `<pre><code>${escapedCode}</code></pre>`)
  })
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/__(.*?)__/g, '<strong>$1</strong>')
  
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  html = html.replace(/_(.*?)_/g, '<em>$1</em>')
  
  // Inline code (single backticks) - after code blocks
  html = html.replace(/`([^`\n]+?)`/g, '<code>$1</code>')
  
  // Unordered lists
  html = html.replace(/^\* (.+)$/gim, '<li>$1</li>')
  html = html.replace(/^- (.+)$/gim, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
  
  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gim, '<li>$1</li>')
  
  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>')
  html = html.replace(/\n/g, '<br>')
  
  // Wrap in paragraph if not already wrapped
  if (!html.startsWith('<h') && !html.startsWith('<ul') && !html.startsWith('<pre')) {
    html = '<p>' + html + '</p>'
  }
  
  return html
}
</script>

<style scoped>
.agent-message {
  display: flex;
  justify-content: flex-start;
  margin-bottom: var(--spacing-lg);
  animation: slideIn 0.3s ease;
}

.message-content {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  max-width: 75%;
  width: 100%;
  box-sizing: border-box;
}

@media (min-width: 1920px) {
  .message-content {
    max-width: 70%;
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border: 2px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: var(--shadow);
  transition: all var(--transition);
}

.agent-message.loading .message-avatar {
  animation: pulse 2s ease-in-out infinite;
  box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7);
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(99, 102, 241, 0);
  }
}

.message-body {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.message-text {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg) var(--spacing-xl);
  box-shadow: var(--shadow-lg);
  border-left: 4px solid var(--color-primary);
  width: 100%;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
  overflow-x: hidden;
  box-sizing: border-box;
}

.message-text p {
  margin: 0 0 1em 0;
  color: var(--color-text);
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  max-width: 100%;
}

.message-text p:last-child {
  margin-bottom: 0;
}

.markdown-content {
  color: var(--color-text);
  line-height: 1.6;
  width: 100%;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
  overflow-x: hidden;
  box-sizing: border-box;
}

.markdown-content h1 {
  font-size: 1.5em;
  font-weight: 600;
  margin: 1em 0 0.5em 0;
  color: var(--color-text);
  border-bottom: 2px solid var(--color-border);
  padding-bottom: 0.3em;
}

.markdown-content h2 {
  font-size: 1.3em;
  font-weight: 600;
  margin: 0.8em 0 0.4em 0;
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.2em;
}

.markdown-content h3 {
  font-size: 1.1em;
  font-weight: 600;
  margin: 0.6em 0 0.3em 0;
  color: var(--color-text);
}

.markdown-content code {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: 3px;
  padding: 2px 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: var(--color-primary);
}

.markdown-content pre {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--spacing-md);
  overflow-x: auto;
  overflow-y: auto;
  max-width: 100%;
  margin: 1em 0;
  word-wrap: break-word;
  word-break: break-word;
  white-space: pre-wrap;
}

.markdown-content pre code {
  background: transparent;
  border: none;
  padding: 0;
  color: var(--color-text);
}

.markdown-content ul,
.markdown-content ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.markdown-content li {
  margin: 0.3em 0;
  color: var(--color-text);
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.markdown-content table {
  width: 100%;
  max-width: 100%;
  border-collapse: collapse;
  overflow-x: auto;
  display: block;
  word-wrap: break-word;
}

.markdown-content table td,
.markdown-content table th {
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.markdown-content strong {
  font-weight: 600;
  color: var(--color-text);
}

.markdown-content em {
  font-style: italic;
}

.streaming-content {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.cursor {
  color: var(--color-primary);
  animation: blink 1s infinite;
  font-weight: bold;
}

.loading-container {
  background: linear-gradient(135deg, var(--color-surface-elevated) 0%, var(--color-surface) 100%);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-lg);
  border-left: 4px solid var(--color-primary);
}

.loading-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.loading-spinner {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-ring:nth-child(2) {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  border-top-color: var(--color-secondary);
  animation-delay: -0.3s;
}

.spinner-ring:nth-child(3) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  border-top-color: var(--color-accent);
  animation-delay: -0.6s;
}

.loading-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  flex: 1;
}

.loading-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.loading-subtitle {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.overall-progress-container {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  border-left: 4px solid var(--color-primary);
}

.overall-progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.overall-progress-label {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text);
}

.overall-progress-percentage {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}

.overall-progress-bar {
  width: 100%;
  height: 12px;
  background: var(--color-surface-elevated);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.overall-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: 6px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.overall-progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 1.5s infinite;
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.progress-container-inline {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.progress-card {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--transition);
}

.progress-card:hover {
  border-color: var(--color-primary);
  background: var(--color-surface-elevated);
  transform: translateX(4px);
}

.progress-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
}

.progress-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  min-width: 0;
}

.progress-label {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--color-text);
  line-height: 1.4;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xs);
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--color-surface-elevated);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: 3px;
  transition: width 0.5s ease;
  position: relative;
  overflow: hidden;
}

.progress-bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 2s infinite;
}

.progress-percentage {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-primary);
  min-width: 45px;
  text-align: right;
}

.progress-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}

.progress-badge-icon {
  color: var(--color-primary);
  font-size: 0.625rem;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@media (max-width: 768px) {
  .message-content {
    max-width: 95%;
  }
}
</style>

