import { createApp } from 'vue'
import { pinia } from './stores'
import router from './router'
import App from './App.vue'
import './assets/styles/main.css'

const app = createApp(App)

app.use(pinia)
app.use(router)

// Global error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err, info)
  // TODO: Send to error tracking service
}

app.mount('#app')

