<template>
  <div class="user-message">
    <div class="message-content">
      <div class="message-avatar">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 10C12.7614 10 15 7.76142 15 5C15 2.23858 12.7614 0 10 0C7.23858 0 5 2.23858 5 5C5 7.76142 7.23858 10 10 10Z" fill="currentColor"/>
          <path d="M10 12C5.58172 12 2 13.7909 2 16V20H18V16C18 13.7909 14.4183 12 10 12Z" fill="currentColor"/>
        </svg>
      </div>
      <div class="message-text">
        <p>{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<style scoped>
.user-message {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--spacing-lg);
  animation: slideIn 0.3s ease;
}

.message-content {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  max-width: 75%;
  flex-direction: row-reverse;
}

@media (min-width: 1920px) {
  .message-content {
    max-width: 70%;
  }
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.message-text {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border: none;
  border-radius: var(--radius-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: var(--shadow-lg);
}

.message-text p {
  margin: 0;
  color: white;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
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

@media (max-width: 768px) {
  .message-content {
    max-width: 95%;
  }
}
</style>

