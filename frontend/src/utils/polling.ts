export interface PollOptions {
  interval: number
  maxInterval?: number
  immediate?: boolean
  until?: (result: any) => boolean
}

// Track active polling instances to prevent duplicates
const activePollers = new Map<string, () => void>()

export function usePolling() {
  const pollIds = new Set<number>()

  function poll<T>(
    fn: () => Promise<T>,
    options: PollOptions,
    key?: string // Optional key to prevent duplicate polling
  ): () => void {
    // If key provided and poller already exists, stop the old one
    if (key && activePollers.has(key)) {
      const oldStop = activePollers.get(key)
      if (oldStop) oldStop()
    }

    let interval = options.interval
    let timeoutId: number | null = null
    let isActive = true
    let abortController: AbortController | null = null

    const execute = async () => {
      if (!isActive) return

      try {
        // Create abort controller for request cancellation
        abortController = new AbortController()
        
        const result = await fn()
        
        if (!isActive) return
        
        if (options.until?.(result)) {
          if (timeoutId !== null) {
            clearTimeout(timeoutId)
            pollIds.delete(timeoutId)
          }
          if (key) activePollers.delete(key)
          isActive = false
          return
        }

        // Exponential backoff (capped)
        if (options.maxInterval && interval < options.maxInterval) {
          interval = Math.min(interval * 1.2, options.maxInterval)
        }

        if (isActive) {
          timeoutId = window.setTimeout(execute, interval)
          if (timeoutId !== null) {
            pollIds.add(timeoutId)
          }
        }
      } catch (err) {
        if (!isActive) return
        console.error('Polling error:', err)
        // Continue polling even on error, but with longer interval
        if (isActive) {
          interval = Math.min(interval * 1.5, options.maxInterval || interval * 2)
          timeoutId = window.setTimeout(execute, interval)
          if (timeoutId !== null) {
            pollIds.add(timeoutId)
          }
        }
      } finally {
        abortController = null
      }
    }

    const stop = () => {
      isActive = false
      if (timeoutId !== null) {
        clearTimeout(timeoutId)
        pollIds.delete(timeoutId)
        timeoutId = null
      }
      if (abortController) {
        abortController.abort()
        abortController = null
      }
      if (key) {
        activePollers.delete(key)
      }
    }

    if (options.immediate) {
      execute()
    } else {
      timeoutId = window.setTimeout(execute, interval)
      if (timeoutId !== null) {
        pollIds.add(timeoutId)
      }
    }

    if (key) {
      activePollers.set(key, stop)
    }

    return stop
  }

  function stopPolling(): void {
    pollIds.forEach((id) => clearTimeout(id))
    pollIds.clear()
    activePollers.forEach((stop) => stop())
    activePollers.clear()
  }

  return { poll, stopPolling }
}

