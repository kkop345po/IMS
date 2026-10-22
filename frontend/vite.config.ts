import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// AD-9：前端只透過 REST 存取資料；dev 與 preview 都需要把 /api 代理到 Flask
const apiProxy = {
  '/api': {
    target: 'http://127.0.0.1:5000',
    changeOrigin: true,
  },
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Vite 預設擋下未知 Host（DNS rebinding 保護），Cloudflare Tunnel 會轉發原始
    // Host（*.trycloudflare.com 或自有網域），不列入會直接回 403。
    // 只放行網域尾綴，不開 allowedHosts: true，避免開洞過大。
    allowedHosts: ['.trycloudflare.com'],
    proxy: apiProxy,
  },
  // 上線用正式建置產物（npm run build）＋ preview 伺服器，
  // 避免把 dev server（HMR、source map、未壓縮）暴露在公開網址上。
  preview: {
    host: '127.0.0.1',
    port: 4173,
    allowedHosts: ['.trycloudflare.com'],
    proxy: apiProxy,
  },
})
