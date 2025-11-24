<template>
  <div class="chat-view">
    <div class="chat-container">
      <!-- Chat Messages -->
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="welcome-content">
            <h1 class="welcome-title">
              <span class="gradient-text">AI Researcher</span>
            </h1>
            <p class="welcome-subtitle">
              Your agentic co-scientist. Ask me anything about research, and I'll help you from idea generation to experimental validation.
            </p>
          </div>
        </div>

        <div
          v-for="(message, index) in messages"
          :key="`message-${index}-${message.jobId || ''}`"
        >
          <UserMessage
            v-if="message.role === 'user'"
            :message="message.content"
          />
          <AgentMessage
            v-else
            :message="message.content"
            :isLoading="message.isLoading"
            :isStreaming="message.isStreaming"
            :progress="message.progress"
          />
        </div>
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <!-- Agent Quick Select - Show when no active response and ready for new prompt -->
        <div v-if="showAgentQuickSelect && !isWaitingForResponse" class="agent-quick-select">
          <div class="quick-select-item" @click="selectAgent('Idea Spark')">
            <span class="agent-icon">💡</span>
            <div class="agent-details">
              <strong>Idea Spark</strong>
            </div>
          </div>
          <div class="quick-select-item" @click="selectAgent('Deep Survey')">
            <span class="agent-icon">🔍</span>
            <div class="agent-details">
              <strong>Deep Survey</strong>
            </div>
          </div>
          <div class="quick-select-item" @click="selectAgent('Auto Experiment')">
            <span class="agent-icon">⚗️</span>
            <div class="agent-details">
              <strong>Auto Experiment</strong>
            </div>
          </div>
        </div>
        
        <!-- File Upload for References -->
        <div v-if="attachedFiles.length > 0" class="attached-files">
          <div
            v-for="(file, index) in attachedFiles"
            :key="index"
            class="file-badge"
          >
            <span class="file-name">{{ file.name }}</span>
            <button @click="removeFile(index)" class="remove-file">×</button>
          </div>
        </div>
        <form @submit.prevent="handleSendMessage" class="input-form">
          <div class="input-wrapper">
            <label for="file-input" class="file-upload-button" title="Attach reference files">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 8H12.5V5.5C12.5 3.57 10.93 2 9 2S5.5 3.57 5.5 5.5V8H3V18H17V8H15ZM7 5.5C7 4.67 7.67 4 8.5 4S10 4.67 10 5.5V8H7V5.5ZM15 16H5V10H15V16Z" fill="currentColor"/>
              </svg>
            </label>
            <input
              id="file-input"
              type="file"
              ref="fileInputRef"
              class="file-input"
              multiple
              accept=".txt,.md,.pdf"
              @change="handleFileSelect"
            />
            <textarea
              v-model="inputMessage"
              ref="inputRef"
              class="message-input"
              placeholder="@Idea Spark, @Deep Survey, or @Auto Experiment to start..."
              rows="1"
              @keydown="handleKeyDown"
              @input="handleInputChange"
            ></textarea>
            <button
              type="submit"
              class="send-button"
              :disabled="!inputMessage.trim() || isWaitingForResponse"
            >
              <svg v-if="!isWaitingForResponse" width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <div v-else class="spinner-small"></div>
            </button>
          </div>
        </form>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useJobStore } from '@/stores/job'
import { useEnvironmentStore } from '@/stores/environment'
import { useLogsStore } from '@/stores/logs'
import { useLogStreaming } from '@/composables/useLogStreaming'
import * as jobApi from '@/services/api/jobs'
import UserMessage from '@/components/chat/UserMessage.vue'
import AgentMessage from '@/components/chat/AgentMessage.vue'
import type { RunRequest } from '@/types/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  isLoading?: boolean
  isStreaming?: boolean
  progress?: string[]
  jobId?: string
}

const router = useRouter()
const jobStore = useJobStore()
const environmentStore = useEnvironmentStore()
const logsStore = useLogsStore()

const messages = ref<ChatMessage[]>([])
const inputMessage = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const messagesContainer = ref<HTMLDivElement | null>(null)
const isWaitingForResponse = ref(false)
const error = ref<string | null>(null)
const attachedFiles = ref<File[]>([])
const activePollingIntervals = ref<Map<string, NodeJS.Timeout>>(new Map())
const showAgentQuickSelect = ref(true)
const selectedAgent = ref<RunRequest['mode'] | null>(null)

onMounted(async () => {
  // No need to fetch modes anymore - we auto-detect
})

// Cleanup polling on unmount
onUnmounted(() => {
  activePollingIntervals.value.forEach((interval) => {
    clearInterval(interval)
  })
  activePollingIntervals.value.clear()
})

watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function autoResize(event: Event) {
  const textarea = event.target as HTMLTextAreaElement
  textarea.style.height = 'auto'
  textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
}

function handleInputChange(event: Event) {
  autoResize(event)
  // Hide quick select when user starts typing
  if (inputMessage.value.length > 0) {
    showAgentQuickSelect.value = false
  } else if (!isWaitingForResponse.value) {
    // Show again when input is cleared and not waiting
    showAgentQuickSelect.value = true
  }
}

function selectAgent(agentName: RunRequest['mode']) {
  selectedAgent.value = agentName
  inputMessage.value = `@${agentName.replace(/\s+/g, '')} `
  showAgentQuickSelect.value = false
  if (inputRef.value) {
    inputRef.value.focus()
  }
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) {
    const newFiles = Array.from(target.files)
    attachedFiles.value.push(...newFiles)
    // Reset input to allow selecting the same file again
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

function removeFile(index: number) {
  attachedFiles.value.splice(index, 1)
}

async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      // For PDFs, we can't read them as text directly, so show a note
      if (file.name.endsWith('.pdf')) {
        resolve(`[PDF file: ${file.name} - content extraction not yet supported, please provide text summary]`)
      } else {
        resolve(content)
      }
    }
    reader.onerror = reject
    // Try to read as text for text-based files
    if (file.name.endsWith('.pdf')) {
      // For PDF, we'd need a PDF parser library, for now just return a note
      resolve(`[PDF file: ${file.name} - please provide a text summary of the paper content]`)
    } else {
      reader.readAsText(file)
    }
  })
}

async function handleSendMessage() {
  if (!inputMessage.value.trim() || isWaitingForResponse.value) return

  const userMessage = inputMessage.value.trim()
  
  // Use pre-selected agent if available
  let selectedMode: RunRequest['mode'] | null = selectedAgent.value
  
  // Check for @ mentions (novix.science style)
  const mentionPattern = /@(\w+)/i
  const mentions = userMessage.match(new RegExp(mentionPattern.source, 'gi'))
  
  if (!selectedMode && mentions) {
    const mentionMap: Record<string, RunRequest['mode']> = {
      'ideaspark': 'Idea Spark',
      'idea': 'Idea Spark',
      'spark': 'Idea Spark',
      'deepsurvey': 'Deep Survey',
      'survey': 'Deep Survey',
      'deep': 'Deep Survey',
      'autoexperiment': 'Auto Experiment',
      'experiment': 'Auto Experiment',
      'exp': 'Auto Experiment',
      'auto': 'Auto Experiment',
    }
    
    for (const mention of mentions) {
      const agentName = mention.replace('@', '').toLowerCase()
      if (mentionMap[agentName]) {
        selectedMode = mentionMap[agentName]
        break
      }
    }
  }
  
  // Auto-detect mode based on whether references are provided
  let reference = ''
  let mode: RunRequest['mode'] = selectedMode || 'Idea Spark' // Default to Idea Spark (simplest)
  
  // Check for references in multiple ways:
  // 1. Attached files (highest priority - clear indication of references)
  if (attachedFiles.value.length > 0) {
    // If no explicit mode selected, use Deep Survey for files (more comprehensive)
    if (!selectedMode) {
      mode = 'Deep Survey'
    }
    // Read file contents and add to reference
    const fileContents = await Promise.all(
      attachedFiles.value.map(file => 
        readFileAsText(file).then(content => 
          `File: ${file.name}\n${content}`
        ).catch(() => `File: ${file.name} (could not read content)`)
      )
    )
    reference = fileContents.join('\n\n---\n\n')
  }
  
  // 2. Check if message contains explicit "reference:" or "references:" prefix
  const referencePrefixMatch = userMessage.match(/(?:reference|references):\s*(.+)/i)
  if (!reference && referencePrefixMatch) {
    if (!selectedMode) {
      mode = 'Deep Survey' // References suggest comprehensive research
    }
    reference = referencePrefixMatch[1].trim()
  }
  
  // 3. Check for explicit paper citations or arxiv IDs (more specific patterns)
  const arxivPattern = /arxiv:?\s*(\d{4}\.\d{4,5})/i
  const citationPattern = /(?:paper|papers|cite|citation|publication).*?:/i
  if (!reference && (arxivPattern.test(userMessage) || citationPattern.test(userMessage))) {
    if (!selectedMode) {
      mode = 'Deep Survey' // Citations suggest comprehensive research
    }
    // Extract the reference portion (everything after the citation keyword)
    const match = userMessage.match(/(?:paper|papers|cite|citation|publication).*?:\s*(.+)/i)
    reference = match ? match[1].trim() : userMessage
  }
  
  // 4. Check for experiment-related keywords
  const experimentKeywords = ['experiment', 'train', 'test', 'evaluate', 'implement', 'run', 'execute']
  if (!selectedMode && experimentKeywords.some(keyword => userMessage.toLowerCase().includes(keyword))) {
    mode = 'Auto Experiment'
  }
  
  // 5. Check for survey/research keywords
  const surveyKeywords = ['survey', 'review', 'analyze', 'research', 'literature', 'comprehensive']
  if (!selectedMode && !reference && surveyKeywords.some(keyword => userMessage.toLowerCase().includes(keyword))) {
    mode = 'Deep Survey'
  }

  // Add user message
  messages.value.push({
    role: 'user',
    content: userMessage + (attachedFiles.value.length > 0 ? `\n[${attachedFiles.value.length} file(s) attached]` : ''),
  })

  inputMessage.value = ''
  attachedFiles.value = []
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }

  // Reset error and clear selection
  error.value = null
  isWaitingForResponse.value = true
  selectedAgent.value = null
  showAgentQuickSelect.value = false

  try {
    const payload: RunRequest = {
      question: userMessage,
      reference: reference || '', // Standardize to empty string instead of undefined
      mode: mode,
    }

    // Submit job
    const jobId = await jobStore.submitJob(payload)
    
    // Add loading message
    const loadingMessageIndex = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      isLoading: true,
      jobId,
    })

      // Start polling for updates
      pollJobStatus(jobId, loadingMessageIndex)
  } catch (err: any) {
    error.value = err.message || 'Failed to send message'
    // Remove loading message
    messages.value = messages.value.filter(m => !m.isLoading || m.jobId)
    isWaitingForResponse.value = false
    // Show agent selector after error
    showAgentQuickSelect.value = true
  }
}

async function pollJobStatus(jobId: string, messageIndex: number) {
  const { logs, startStreaming, stop } = useLogStreaming(jobId)
  const logsStore = useLogsStore()
  
  // Start streaming logs
  startStreaming()

  // Store interval for cleanup
  let pollInterval: NodeJS.Timeout | null = null
  
  const cleanup = () => {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
    activePollingIntervals.value.delete(jobId)
    stop()
  }

  pollInterval = setInterval(async () => {
    try {
      // Fetch latest job status
      await jobStore.fetchJob(jobId)
      const job = jobStore.jobs.get(jobId)

      if (!job) {
        console.warn(`Job ${jobId} not found`)
        cleanup()
        return
      }

      // Wait for job to actually start - don't mark as complete if it's still pending
      if (job.status === 'pending') {
        // Job hasn't started yet, just show waiting
        const agentType = job.payload?.mode || 'Agent'
        messages.value[messageIndex] = {
          role: 'assistant',
          content: `[${agentType}] Waiting to start...`,
          isLoading: true,
          jobId,
        }
        return
      }

      // Fetch progress updates if job is running
      if (job.status === 'running') {
        try {
          const progressData = await jobApi.getJobProgress(jobId)
          // Update job progress in store
          const updatedJob = jobStore.jobs.get(jobId)
          if (updatedJob && progressData) {
            updatedJob.progress = progressData
          }
        } catch (progressErr) {
          // Progress might not be available yet, that's okay
          console.debug('Progress not available yet:', progressErr)
        }
      }

      // Update progress display
      const progress: string[] = []
      const currentJob = jobStore.jobs.get(jobId)
      if (currentJob?.progress) {
        if (currentJob.progress.current_agent) {
          progress.push(`Current Agent: ${currentJob.progress.current_agent}`)
        }
        if (currentJob.progress.current_step) {
          progress.push(`Step: ${currentJob.progress.current_step}`)
        }
        if (currentJob.progress.subtasks && currentJob.progress.subtasks.length > 0) {
          const completed = currentJob.progress.subtasks.filter((s: any) => s.status === 'completed').length
          const total = currentJob.progress.subtasks.length
          if (total > 0) {
            progress.push(`Progress: ${completed}/${total} subtasks completed`)
          }
        }
      }

      // Fetch logs
      try {
        await logsStore.fetchJobLogs(jobId)
      } catch (logErr) {
        // Logs might not be available yet, that's okay
        console.debug('Logs not available yet:', logErr)
      }

      // Get latest logs
      const getJobLogs = logsStore.getJobLogs
      const latestLogs = getJobLogs(jobId)
      let latestContent = ''

      // Build content from all assistant messages in logs
      if (latestLogs.length > 0) {
        const assistantMessages = latestLogs
          .filter(log => log.assistant)
          .map(log => log.assistant)
          .filter((msg): msg is string => msg !== null)
        
        if (assistantMessages.length > 0) {
          // Combine all assistant messages, showing the latest ones
          latestContent = assistantMessages.slice(-3).join('\n\n')
        }
      }

      // If no content yet and job is running, show status
      if (!latestContent && job.status === 'running') {
        latestContent = 'Processing your request...'
      }

      // Update message
      const isActive = job.status === 'running' || job.status === 'pending'
      messages.value[messageIndex] = {
        role: 'assistant',
        content: latestContent || (isActive ? 'Processing...' : ''),
        isLoading: isActive,
        isStreaming: job.status === 'running' && latestContent.length > 0,
        progress: progress.length > 0 ? progress : undefined,
        jobId,
      }

      // Check if job is complete
      if (job.status === 'succeeded' || job.status === 'failed' || job.status === 'cancelled') {
        cleanup()

        // Check if all active jobs are done
        const allJobsDone = Array.from(activePollingIntervals.value.keys()).length === 0
        if (allJobsDone) {
          isWaitingForResponse.value = false
          // Show agent selector again after response completes
          showAgentQuickSelect.value = true
        }

        if (job.status === 'succeeded') {
          // Simplified result extraction function
          const extractResult = (result: any): string => {
            if (!result) return ''
            
            // Handle string result
            if (typeof result === 'string') {
              return result.trim()
            }
            
            // Handle object result - check for answer field first
            if (typeof result === 'object' && result !== null) {
              // Primary: check for answer field
              if (result.answer) {
                const answer = typeof result.answer === 'string' ? result.answer : String(result.answer)
                if (answer.trim().length > 0) {
                  return answer.trim()
                }
              }
              
              // Secondary: check common result keys
              const resultKeys = ['result', 'content', 'output', 'response']
              for (const key of resultKeys) {
                if (result[key] && typeof result[key] === 'string' && result[key].trim().length > 0) {
                  return result[key].trim()
                }
              }
            }
            
            return ''
          }
          
          // Check for status messages that indicate no real content
          const isStatusMessage = (content: string): boolean => {
            if (!content || content.trim().length < 50) return true
            const statusPatterns = [
              'already in progress',
              'please wait',
              'job is already'
            ]
            return statusPatterns.some(pattern => content.toLowerCase().includes(pattern))
          }
          
          // Extract result from job.result
          let finalContent = extractResult(job.result)
          
          // If result is insufficient or looks like a status message, try logs
          if (!finalContent || isStatusMessage(finalContent)) {
            try {
              await logsStore.fetchJobLogs(jobId)
              const allLogs = logsStore.getJobLogs(jobId)
              const assistantMessages = allLogs
                .filter(log => log.assistant && typeof log.assistant === 'string' && log.assistant.trim().length > 0)
                .map(log => log.assistant as string)
              
              if (assistantMessages.length > 0) {
                const logContent = assistantMessages.join('\n\n')
                // Use log content if we don't have result, otherwise combine
                finalContent = finalContent ? `${finalContent}\n\n---\n\n${logContent}` : logContent
              }
            } catch (err) {
              console.error('Could not fetch final logs:', err)
            }
          }
          
          // Final fallback
          if (!finalContent || finalContent.trim().length === 0) {
            finalContent = 'Research completed successfully! Please check the logs for detailed results.'
          }
          
          messages.value[messageIndex] = {
            role: 'assistant',
            content: finalContent,
            isLoading: false,
            jobId,
          }
        } else if (job.status === 'failed') {
          messages.value[messageIndex] = {
            role: 'assistant',
            content: `Research failed: ${job.error || 'Unknown error'}`,
            isLoading: false,
            jobId,
          }
        } else if (job.status === 'cancelled') {
          messages.value[messageIndex] = {
            role: 'assistant',
            content: 'Research was cancelled',
            isLoading: false,
            jobId,
          }
        }
      }
    } catch (err) {
      console.error('Error polling job status:', err)
      // On persistent errors, stop polling to prevent infinite loops
      const errorMessage = err instanceof Error ? err.message : String(err)
      if (errorMessage.includes('404') || errorMessage.includes('not found')) {
        console.warn(`Job ${jobId} not found, stopping polling`)
        cleanup()
      }
      // For other errors, continue polling but log them
    }
  }, 3000) // Poll every 3 seconds

  // Store interval for cleanup
  if (pollInterval) {
    activePollingIntervals.value.set(jobId, pollInterval)
  }

  // Initial fetch
  try {
    await jobStore.fetchJob(jobId)
    await logsStore.fetchJobLogs(jobId)
  } catch (err) {
    console.debug('Initial job fetch error (may be normal):', err)
  }
}
</script>

<style scoped>
.chat-view {
  height: calc(100vh - 70px);
  display: flex;
  flex-direction: column;
  background: var(--color-background);
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  padding: var(--spacing-xl) var(--spacing-2xl);
}

/* Responsive width for different screen sizes */
@media (min-width: 1920px) {
  .chat-container {
    max-width: 1600px;
    padding: var(--spacing-xl) var(--spacing-3xl);
  }
}

@media (min-width: 2560px) {
  .chat-container {
    max-width: 2000px;
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-xl) 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  scroll-behavior: smooth;
  max-width: 100%;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-light);
}

.welcome-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.welcome-content {
  text-align: center;
  max-width: 800px;
  padding: var(--spacing-3xl);
}

.welcome-title {
  font-size: clamp(2rem, 5vw, 4rem);
  font-weight: 800;
  margin-bottom: var(--spacing-lg);
  line-height: 1.2;
  letter-spacing: -0.03em;
}

.welcome-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
  max-width: 700px;
  margin: 0 auto;
}

.chat-input-area {
  border-top: 1px solid var(--color-border);
  padding-top: var(--spacing-lg);
  background: var(--color-background);
  position: sticky;
  bottom: 0;
  z-index: 10;
}

.agent-quick-select {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: linear-gradient(135deg, var(--color-surface) 0%, var(--color-surface-elevated) 100%);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  animation: slideDown 0.4s ease;
  box-shadow: var(--shadow-lg);
}

.quick-select-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition);
  position: relative;
  overflow: hidden;
}

.quick-select-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  transform: scaleX(0);
  transition: transform var(--transition);
}

.quick-select-item:hover {
  border-color: var(--color-primary);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.quick-select-item:hover::before {
  transform: scaleX(1);
}

.agent-icon {
  font-size: 2rem;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  transition: transform var(--transition);
}

.quick-select-item:hover .agent-icon {
  transform: scale(1.1) rotate(5deg);
}

.agent-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  flex: 1;
}

.agent-details strong {
  font-size: 1.125rem;
  color: var(--color-text);
  font-weight: 700;
  letter-spacing: -0.01em;
  margin-bottom: var(--spacing-xs);
}

.agent-details span {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.attached-files {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.file-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, var(--color-surface-elevated) 0%, var(--color-surface) 100%);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  color: var(--color-text);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition);
}

.file-badge:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow);
}

.file-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition);
}

.remove-file:hover {
  color: var(--color-error);
}

.file-input {
  display: none;
}

.file-upload-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition);
  flex-shrink: 0;
}

.file-upload-button:hover {
  background: var(--color-surface-elevated);
  color: var(--color-primary);
  transform: scale(1.1);
}

.input-form {
  width: 100%;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-sm);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  transition: all var(--transition);
  box-shadow: var(--shadow-sm);
}

.input-wrapper:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15), var(--shadow);
  background: var(--color-surface-elevated);
}

.message-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--color-text);
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  max-height: 200px;
  overflow-y: auto;
  padding: 0;
  line-height: 1.5;
}

.message-input:focus {
  outline: none;
}

.message-input::placeholder {
  color: var(--color-text-muted);
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  border: none;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition);
  flex-shrink: 0;
  box-shadow: var(--shadow);
}

.send-button:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--color-primary-hover) 0%, var(--color-secondary) 100%);
  transform: scale(1.08) translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.error-message {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.1) 100%);
  color: var(--color-error);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(239, 68, 68, 0.3);
  font-size: 0.875rem;
  box-shadow: var(--shadow-sm);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
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

@media (max-width: 1024px) {
  .chat-container {
    max-width: 100%;
    padding: var(--spacing-lg);
  }
  
  .agent-quick-select {
    grid-template-columns: 1fr;
  }
  
  .message-content {
    max-width: 85%;
  }
}

@media (max-width: 768px) {
  .chat-container {
    padding: var(--spacing-md);
  }
  
  .welcome-content {
    padding: var(--spacing-lg);
    max-width: 100%;
  }
  
  .agent-quick-select {
    padding: var(--spacing-md);
    gap: var(--spacing-md);
  }
  
  .quick-select-item {
    padding: var(--spacing-md);
  }
  
  .message-content {
    max-width: 95%;
  }
}
</style>

