// 前端煙霧測試：用 headless Edge 實際渲染每個頁面，檢查有沒有 console 錯誤與空白頁。
//
// 執行前置：
//   1) 後端啟動：cd backend && ..\.venv\Scripts\python.exe -m flask run --port 5000
//   2) 前端啟動：cd frontend && npm run dev
//   3) 執行：node frontend/scripts/smoke.mjs
//
// 這支腳本抓到過「頁面整片空白」的 bug（ReportsPage 漏 import Space），
// 純 API 測試抓不到這類前端渲染錯誤。

import { spawn, execSync } from 'node:child_process'
import { existsSync, mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const APP = 'http://localhost:5173'
const API = 'http://127.0.0.1:5000/api'
// 每次用不同 port，避免連到殘留的 Edge 實例
const DEBUG_PORT = 9300 + Math.floor(Math.random() * 400)
const EDGE_CANDIDATES = [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
]

const ROUTES = [
  { path: '/items', expect: ['商品', '供應商'] },
  { path: '/stock', expect: ['庫存現況', '在手', '可用'] },
  { path: '/purchase-orders', expect: ['採購單', 'PO-'] },
  { path: '/replenishment', expect: ['補貨建議'] },
  { path: '/sales-orders', expect: ['銷售單', 'SO-'] },
  { path: '/transfers', expect: ['調撥單', 'TO-'] },
  { path: '/reports', expect: ['業績與毛利', '銷貨員', '毛利'] },
]

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

/** 瀏覽器擴充套件造成的錯誤與本專案無關，忽略 */
function isExtensionNoise(msg = '') {
  return (
    msg.includes('chrome-extension://') ||
    msg.includes('toggleTranslatePage') ||
    msg.includes('Cannot find menu item') ||
    msg.includes('Extension context invalidated')
  )
}

function findEdge() {
  for (const p of EDGE_CANDIDATES) {
    if (existsSync(p)) return p
  }
  throw new Error('找不到 Edge / Chrome')
}

async function login() {
  const r = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'Passw0rd!' }),
  })
  const m = (r.headers.get('set-cookie') || '').match(/session=([^;]+)/)
  if (!m) throw new Error('登入失敗')
  return m[1]
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl)
  let id = 0
  const pending = new Map()
  const events = []
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data)
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg)
      pending.delete(msg.id)
    } else if (msg.method) events.push(msg)
  })
  const ready = new Promise((r) => ws.addEventListener('open', r))
  return {
    ready,
    events,
    send: (method, params = {}) => {
      const msgId = ++id
      return new Promise((resolve) => {
        pending.set(msgId, resolve)
        ws.send(JSON.stringify({ id: msgId, method, params }))
      })
    },
    close: () => ws.close(),
  }
}

async function main() {
  const edge = findEdge()
  const profile = mkdtempSync(join(tmpdir(), 'smoke-edge-'))
  const proc = spawn(
    edge,
    [
      '--headless=new',
      '--disable-gpu',
      '--no-sandbox',
      '--disable-extensions', // 避免瀏覽器擴充套件干擾測試
      `--remote-debugging-port=${DEBUG_PORT}`,
      `--user-data-dir=${profile}`,
      'about:blank',
    ],
    { detached: false, stdio: 'ignore' },
  )

  let wsUrl = null
  for (let i = 0; i < 30 && !wsUrl; i++) {
    await sleep(500)
    try {
      const list = await (await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/list`)).json()
      wsUrl = list?.[0]?.webSocketDebuggerUrl ?? null
    } catch {
      /* 還沒起來 */
    }
  }
  if (!wsUrl) throw new Error('無法連上 Edge CDP')

  const session = await login()

  let pass = 0
  const failures = []

  for (const route of ROUTES) {
    // 每個路由開一個新分頁（避免 target 狀態互相干擾）
    const target = await (
      await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/new?about:blank`, { method: 'PUT' })
    ).json()
    const cdp = connect(target.webSocketDebuggerUrl)
    await cdp.ready
    await cdp.send('Runtime.enable')
    await cdp.send('Log.enable')
    await cdp.send('Network.enable')
    await cdp.send('Page.enable')
    await cdp.send('Network.setCookie', {
      name: 'session',
      value: session,
      domain: 'localhost',
      path: '/',
    })
    await cdp.send('Page.navigate', { url: APP + route.path })

    // 輪詢等待頁面渲染完成（Vite 首次編譯可能需要數秒，且資料是非同步載入）
    let text = ''
    let missing = route.expect
    for (let i = 0; i < 40; i++) {
      await sleep(600)
      const bodyRes = await cdp.send('Runtime.evaluate', {
        expression: 'document.body.innerText',
        returnByValue: true,
      })
      text = bodyRes.result?.result?.value ?? ''
      missing = route.expect.filter((kw) => !text.includes(kw))
      if (missing.length === 0) break
    }

    const errors = []
    for (const e of cdp.events) {
      if (e.method === 'Runtime.exceptionThrown') {
        const desc =
          e.params.exceptionDetails.exception?.description?.split('\n')[0] ??
          e.params.exceptionDetails.text
        if (!isExtensionNoise(desc)) errors.push(desc)
      }
      if (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error') {
        const msg = e.params.args.map((a) => a.description || a.value).join(' ')
        if (!msg.includes('favicon') && !isExtensionNoise(msg)) {
          errors.push(msg.split('\n').slice(0, 2).join(' '))
        }
      }
    }
    const missing2 = route.expect.filter((kw) => !text.includes(kw))
    const ok = errors.length === 0 && missing2.length === 0 && text.trim().length > 30
    if (ok) {
      pass++
      console.log(`[PASS] ${route.path}  (${text.trim().length} 字)`)
    } else {
      const detail = []
      if (errors.length) detail.push(`錯誤：${errors[0]?.slice(0, 160)}`)
      if (missing2.length) detail.push(`缺少內容：${missing2.join('、')}`)
      if (text.trim().length <= 30) detail.push('頁面幾乎是空的')
      failures.push(`${route.path} — ${detail.join('；')}`)
      console.log(`[FAIL] ${route.path}  ${detail.join('；')}`)
    }
  }

  try {
    proc.kill()
  } catch {
    /* 忽略 */
  }
  try {
    rmSync(profile, { recursive: true, force: true, maxRetries: 3 })
  } catch {
    /* Edge 可能還在用這個資料夾，忽略即可 */
  }

  console.log(`\n前端煙霧測試：${pass}/${ROUTES.length} 通過`)
  if (failures.length) {
    console.log('失敗項目：')
    failures.forEach((f) => console.log('  ✗ ' + f))
    process.exit(1)
  }
}

main().catch((e) => {
  console.error('煙霧測試無法執行：', e.message)
  process.exit(2)
})
