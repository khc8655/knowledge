import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './globals.css'
import App from './app'

// Apply saved theme before render
const savedTheme = localStorage.getItem('kb-theme')
if (savedTheme) {
  document.documentElement.setAttribute('data-theme', savedTheme)
}
import { ToastProvider } from '@/components/ui/toast'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>,
)
