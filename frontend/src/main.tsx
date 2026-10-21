import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider, App as AntApp } from 'antd'
import zhTW from 'antd/locale/zh_TW'
import App from './App'
import ErrorBoundary from './ErrorBoundary'
import './index.css'

// 全域錯誤處理：把未捕捉的錯誤顯示在畫面上，避免整頁空白
window.addEventListener('unhandledrejection', (event) => {
  const root = document.getElementById('root')
  if (root && !root.textContent?.trim()) {
    root.innerHTML = `<div style="padding:24px;font-family:monospace;color:#cf1322">
      <h2>發生未處理的錯誤</h2><pre>${String(event.reason?.stack ?? event.reason)}</pre></div>`
  }
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhTW} theme={{ token: { colorPrimary: '#1677ff' } }}>
      <AntApp>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <ErrorBoundary>
              <App />
            </ErrorBoundary>
          </BrowserRouter>
        </QueryClientProvider>
      </AntApp>
    </ConfigProvider>
  </React.StrictMode>,
)
