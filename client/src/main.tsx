import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { toast } from 'sonner'
import App from './App'
import { AuthProvider } from './auth/AuthProvider'
import { Toaster } from './components/ui/sonner'
import { TooltipProvider } from './components/ui/tooltip'
import { ApiError } from './lib/api'
import './index.css'

const queryClient = new QueryClient({
  // One place turns every failed write into a message. Reads render their own error state.
  mutationCache: new MutationCache({ onError: (error) => toast.error(error.message) }),
  queryCache: new QueryCache(),
  defaultOptions: {
    queries: {
      staleTime: 5_000,
      // Do not retry what the server said no to (401/403/404); retry transient failures only.
      retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
      refetchOnWindowFocus: true,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <TooltipProvider>
            <App />
          </TooltipProvider>
          <Toaster richColors position="bottom-right" />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
