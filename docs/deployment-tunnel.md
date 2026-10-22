# 用 Cloudflare Tunnel 把庫存系統丟到公開網址

> 這份文件記錄「本機 → 公開網址」的部署方式。**這不是正式上線環境**，是展示／測試用的外網入口。

## 架構

```
瀏覽器
  ↓ https://<隨機字串>.trycloudflare.com
Cloudflare Edge
  ↓ Quick Tunnel (cloudflared)
127.0.0.1:4173   vite preview  ← 服務正式建置產物 frontend/dist
  ↓ /api 代理
127.0.0.1:5000   Flask (backend)
  ↓
PostgreSQL 127.0.0.1:5432   ← 沒有對外
```

- 只有 **4173** 對外。資料庫與 Flask 都只綁 `127.0.0.1`。
- 走的是 `npm run build` 的**正式建置產物**（已壓縮、無 HMR、無 source map），
  不是 dev server。`frontend/vite.config.ts` 的 `preview` 區塊負責 `/api` 代理與 `allowedHosts`。

## 現在怎麼查公開網址

```powershell
Get-Content "$env:TEMP\opencode\tunnel-url.txt"
```

或在桌面雙擊 **`庫存系統網址.cmd`**（會直接開瀏覽器）。

> **Quick Tunnel 的網址是隨機的，每次 cloudflared 重啟就會換一個。**
> 舊網址會直接回 530 / 1033。需要固定網址請看文末「升級成自有網域」。

## 服務是誰在管

Windows 工作排程器（Task Scheduler）底下的四個工作，**登入時自動啟動**：

| 工作 | 內容 | 埠 |
|---|---|---|
| `InventoryFlask` | Flask backend | 5000 |
| `InventoryPreview` | `vite preview`（正式產物，`--strictPort`） | 4173 |
| `InventoryDev` | `vite dev`（本機煙霧測試用） | 5173 |
| `InventoryTunnel` | `cloudflared tunnel --url http://127.0.0.1:4173` | — |

**每個工作的 PowerShell 腳本本身是 supervisor**：外層 `while ($true)` 會一直檢查子行程還在不在，
不在就重新拉起（間隔 10 秒）。

> 為什麼不靠工作排程器的「失敗後重新啟動」？
> 實測 `RestartOnFailure`（Count=999 / Interval=PT1M）**沒有觸發**：
> 子行程被殺掉後工作狀態變成 `Ready`、`LastTaskResult=1`，但排程器沒有重跑。
> 所以改成腳本自己監看 —— 行為可預測，也可以在 `tunnel-task.log` 裡看到重啟紀錄。
>
> 排程器上的 `RestartOnFailure` 設定仍保留，當作整個腳本本身掛掉時的保險。

手動操作：

```powershell
Get-ScheduledTask -TaskName "Inventory*"          # 看狀態
Start-ScheduledTask  -TaskName "InventoryTunnel"   # 重啟 tunnel（會換網址）
Stop-ScheduledTask   -TaskName "Inventory*"        # 全部停掉
```

啟動腳本都在 `C:\Users\GIGABYTE\AppData\Local\Temp\opencode\`：

| 檔案 | 用途 |
|---|---|
| `run-flask.ps1` / `.cmd` / `-inner.ps1` | Flask 任務入口 / 輸出轉向 / 實際執行 |
| `run-preview.ps1` / `.cmd` / `-inner.ps1` | preview 任務（先清 4173，再 `--strictPort` 起） |
| `run-dev.ps1` / `.cmd` / `-inner.ps1` | dev server 任務 |
| `run-tunnel.ps1` / `.cmd` | tunnel 任務（`run-tunnel.cmd` 負責輸出轉向並記錄網址） |
| `register-tasks.ps1` | 重新註冊四個工作（改了腳本後跑一次） |
| `tunnel-task.log` | tunnel 任務的診斷記錄 |
| `tunnel-url.txt` | 目前公開網址 |

### 改了啟動腳本之後

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -File "$env:TEMP\opencode\register-tasks.ps1"
```

## 交付前檢查清單照跑

```powershell
cd frontend
npm run build                                   # 內含 tsc --noEmit
node scripts\smoke.mjs                         # 本機 5173
$env:APP_URL = Get-Content "$env:TEMP\opencode\tunnel-url.txt"
node scripts\smoke.mjs                         # 對公開網址再跑一次
```

`smoke.mjs` 支援 `APP_URL` / `API_URL` 環境變數覆寫（預設值不變）。
**兩個都跑**：只測本機不知道公開部署會不會被擋。

## 常見問題

| 症狀 | 原因 | 處理 |
|---|---|---|
| 網址回 530 / 1033 | cloudflared 掛了或還在重連 | `Start-ScheduledTask -TaskName InventoryTunnel`，網址會換新的 |
| 網址回 403 且 body 寫 `Blocked request. This host ... is not allowed` | **Vite 的 host 檢查擋的，不是 Cloudflare** | 把網域加進 `frontend/vite.config.ts` 的 `allowedHosts` |
| 頁面空白 | 前端 build 失敗或 preview 沒起 | 看 `vite-prev.err`、`vite-task.log` |
| API 全 401 | session cookie 沒綁對網域 | `smoke.mjs` 需用 `APP_URL` 指向實際網址 |

## 升級成自有網域（固定網址）

現在的帳號底下 **沒有任何 zone**，所以沒辦法建 DNS 記錄。要固定網址：

1. 把網域加進 Cloudflare（在註冊商那邊改 nameserver）。
2. 建具名 tunnel（已建好：`inventory-dev`，id `dad1ae87-2db7-4098-89e2-5c624efd1db0`，
   token 在 `~/.local/bin/cf-tunnel-token.txt`）。
3. `PUT /accounts/{acct}/cfd_tunnel/{tunnel_id}/configurations` 設 ingress：
   `https://<你的網域>` → `http://127.0.0.1:4173`。
4. 建 CNAME：`<子網域>` → `<tunnel_id>.cfargotunnel.com`。
5. 改用 `cloudflared tunnel run --token <token>`（不再是 Quick Tunnel）。
6. 把 `frontend/vite.config.ts` 的 `allowedHosts` 換成你的網域。

## 安全提醒

- 這個公開網址**沒有密碼保護以外的防護**；帳號密碼只有 7 個角色共用的 `Passw0rd!`。
  展示完請關掉 `InventoryTunnel` 工作。
- 免費方案無 SLA，Cloudflare 也明講 Quick Tunnel 隨時可能失效。
- `vite preview` 官方說不是正式伺服器，只適合展示／測試。
