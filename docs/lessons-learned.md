# 事故記錄（Lessons Learned）

> 每次出包或踩到坑就補一筆。格式：**現象 → 根因 → 為什麼沒被發現 → 教訓 → 現在的防線**。
> 專案層級的規矩在根目錄 `AGENTS.md`。

---

## 2026-10-21 · 「業績與毛利」整頁空白

**現象**：登入成功、換角色也一樣，`/reports` 是一片白（連版面、選單都沒了）。

**根因**：`frontend/src/pages/Reports.tsx` 用了 `<Space>` 但**漏了 `import { Space } from 'antd'`**。
React 渲染時拋 `ReferenceError: Space is not defined`，因為沒有 ErrorBoundary，整棵樹被卸掉 → 白畫面。
這個錯誤**從那一頁建立起就存在**。

**為什麼沒被發現**：
- `vite build` 只做轉譯不做型別檢查，漏 import 不會讓 build 失敗。
- 我的 90 項測試**全部在測 API**，沒有任何一項真的在瀏覽器裡渲染那一頁。
- headless 測試時是未登入狀態，只渲染到登入頁，進不到業績頁。

**教訓**：
> **「API 全過」不等於「頁面會顯示」。** 純後端測試永遠抓不到前端渲染錯誤。
> 交付前必須有「用真瀏覽器開一遍每個頁面」這一步。

**現在的防線**：
- `frontend/tsconfig.json` + `npm run build` 改為 `tsc --noEmit && vite build` → 漏 import 直接擋。
- `frontend/scripts/smoke.mjs`：headless Edge 帶 session cookie 開每個頁面，檢查 console 錯誤 + 內容關鍵字 + 空白頁。
- `frontend/src/ErrorBoundary.tsx` + `index.html` 全域錯誤捕捉 → 崩潰時畫面直接顯示原因，不會再是白畫面。

---

## 2026-10-21 · 登入成功但畫面不換

**現象**：按登入跳出「登入成功」訊息，但頁面停在登入畫面。

**根因**：`GET /api/auth/me` 讀的是 `g.current_user`，而 `g.current_user` **只有經過權限裝飾器才會被設定**，
但 `/auth/me` 本身不掛裝飾器 → 永遠回 401 → 前端永遠判定「未登入」。

**教訓**：
> 「我是誰」這種查詢端點要自己讀 session，不要假設有人幫你塞好 `g`。
> 另外前端不要用 `<Navigate to="/login">` 當 catch-all，會把已登入的使用者彈回登入頁。

**防線**：`verify_api.py` 加上「登入後 /auth/me 必須回傳使用者與權限」一項。

---

## 2026-10-21 · 採購單頁沒有資料

**現象**：採購單建立成功，但頁面清單是空的。

**根因**：`backend/app/api/documents.py` 漏了 `from sqlalchemy import select`，
`/api/purchase-orders` 與 `/api/sales-orders` **都 500**。

**教訓**：新增 API 端點後要用巡檢腳本把所有端點掃一遍，不要只測剛寫的那個。

**防線**：`backend/scripts/sweep_endpoints.py`（掃所有 GET）+ `test_all_features.py`（64 項涵蓋所有流程）。

---

## 2026-10-21 · 業績報表的銷售金額被重複累加

**現象**：業績報表的「銷售金額」比實際高（一張 2 品項的單，金額被加了兩次）。

**根因**：報表用 `join` 同時彙總「訂單層級的金額」與「明細層級的件數」，
join 讓一張單出現 N 次，訂單金額就被加了 N 次。

**教訓**：
> **不同粒度的彙總不要混在同一個 join 裡。** 訂單層與明細層要各算各的，再合併。

**防線**：`verify_mvp.py` 檢查「毛利總額 = 明細逐筆加總」；`test_all_features.py` 檢查「毛利 = 應收 − 銷貨成本」。

---

## 2026-10-21 · 占用與出庫對不上

**現象**：銷售單送出後「占用」增加，但出貨時找不到對應庫存，數字愈對愈亂。

**根因**：`reserve()` 記在「商品 + 倉庫」層級，`issue_for_sale()` 扣在「商品 + 倉庫 + 儲位 + 批次」層級。
占用跟出貨不是同一筆庫存。

**教訓**：**同一個概念，寫入與釋放必須在同一個鍵值上。** 粒度不一致 = 對不上。

**防線**：spine AD-3 明確要求占用與出貨都落在 `item + warehouse + bin + batch`；`verify_mvp.py` 檢查「可用量 = 在手 − 占用」。

---

## 2026-10-21 · 調撥「來源倉可用庫存不足」

**現象**：調出時報 OUT_OF_STOCK，但明明那個商品有貨。

**根因**：調撥單沒有批次資訊，扣減時用 `batch_id IS NULL` 去比對，而庫存都在批次列上 → 扣不到。

**教訓**：批次是商品流轉的一部分，調撥也必須帶著它走（貨物換倉不等於換批次）。

**防線**：AD-11（`pick_level()` 由後端挑批次並回寫）；`transfers` 表新增 `batch_id` 欄位（走 Alembic 遷移）。

---

## 2026-10-21 · 調入時 500 Internal Server Error

**根因**：目標儲位可以留空，但 `stock_levels.bin_id` 是 NOT NULL → IntegrityError。

**教訓**：對外允許留空的欄位，寫進庫的時候要有「自動補值」或明確擋下來，不能讓它炸成 500。

**防線**：`transfer_service._default_bin()` 自動挑目標倉的可用儲位；沒有則回明確錯誤訊息。

---

## 2026-10-21 · 種子資料把 `viewer` 帳號弄丟了

**現象**：viewer 登入 401，README 明明有寫這個帳號。

**根因**：重寫 `seed_data.py` 時漏掉一個使用者，而當時的測試只檢查「有登入就好」沒檢查每個角色。

**教訓**：種子資料要跟文件、權限矩陣三邊對齊，改動後要驗「文件裡列的每一個帳號都存在」。

**防線**：`test_all_features.py` 開頭會登入全部 7 個角色，少一個就報錯。

---

## 2026-10-21 · PowerShell 把中文檔案弄成亂碼

**現象**：用 `Set-Content` 改 `seed_data.py` 後，檔案裡的中文全部變成亂碼且語法壞掉。

**根因**：PowerShell 5.1 的 `Get-Content` / `Set-Content` 預設用主機 ANSI 編碼（這台機器是 cp950），
讀寫 UTF-8 中文會掉字元。`Set-Content -Encoding utf8` 則會多寫一個 BOM，導致 dotenv 讀不到第一個變數。

**教訓**：改 UTF-8 中文檔案，**用編輯工具，不要用 PowerShell 的 Get/Set-Content**。
真的要用 PowerShell，就用 `[System.IO.File]::ReadAllText()` + `WriteAllText(..., UTF8Encoding($false))`。

---

## 2026-10-21 · 測試腳本自己寫錯

**現象**：全功能測試 3 項失敗：補貨建議查不到品項、在途數量比預期多、調入後數量不對。

**根因**：全是**測試寫法**的問題，不是系統問題：
- 測試商品的安全水位設得比入庫量低，所以本來就不該出現在補貨建議。
- 只看庫存的第一列（`b["items"][0]`）而不是加總，扣的是另一列。
- 假設目標倉是空的，其實裡面有貨。

**教訓**：
> 測試失敗時，先確認是「系統錯」還是「測試錯」。兩者都會顯示紅字，但處理方式完全不同。
> 測試也會過期——種子資料一改，寫死的假設就會壞掉。

**防線**：測試用「挑有足夠庫存的列」而不是「取第一列」；比較數量一律用加總與前後差值，不假設初始狀態。

---

## 2026-10-21 · antd v6 棄用 API 噴 console 錯誤

**現象**：`Space direction`、`Statistic valueStyle` 在 antd v6 已棄用，噴 console.error 污染畫面。

**教訓**：套件大版本升級時，舊 API 會變成 console 錯誤（功能可能還能用，但 demo 畫面會有紅字）。

**防線**：煙霧測試把 console 錯誤視為失敗 → 棄用 API 會被擋下來。

---

## 2026-10-22 · Cloudflare Tunnel 穿出去後 Vite 回 403

**現象**：Tunnel 本身健康（`Registered tunnel connection ... protocol=quic`），但從 `*.trycloudflare.com`
打進來首頁一律 403，錯誤訊息是：

```
Blocked request. This host ("xxx.trycloudflare.com") is not allowed.
To allow this host, add "xxx.trycloudflare.com" to `server.allowedHosts` in vite.config.js.
```

**根因**：**不是 Cloudflare 擋的，是 Vite 自己擋的。** Vite 預設開 DNS rebinding 保護，只接受已知 Host；
Tunnel 會原樣轉發瀏覽器的 `Host` header（`xxx.trycloudflare.com`），Vite 認不出來就回 403。
`localhost` 測試完全正常，所以本地端看不出問題。

**為什麼沒被發現**：
- 本機 `127.0.0.1:5173` 直接測是 200，只有繞出去才 403。
- 403 的 body 是 Vite 的 HTML 文字，看起來像「被 Cloudflare 拒絕」，容易誤判成 Cloudflare 的問題。

**教訓**：
> **看到 403 先看回應 body 是誰寫的**，不要從網域名猜。`trycloudflare.com` 是 Cloudflare 給的，
> 但 403 不一定是 Cloudflare 寫的。
> 反過來說：只要有東西會把外部請求轉發到本機服務，那個服務的 Host 白名單就是必經之路。

**防線**：`frontend/vite.config.ts` 加 `server.allowedHosts: ['.trycloudflare.com']`。
刻意**不**用 `allowedHosts: true`——那是全開，只放行網域尾綴比較安全；要用自有網域再把網域加進去。

---

## 2026-10-22 · 庫存現況表格 rowKey 撞車

**現象**：`/stock` 頁在 dev server 噴 `Encountered two children with the same key`（React console.error），
煙霧測試判失敗。但同一支程式用 production build 開完全正常，頁面內容也對。

**根因**：前端 `rowKey={(r) => \`${r.item_id}-${r.warehouse_id}-${r.bin_id}\`}` **不夠唯一**。
`stock_levels` 的真正唯一鍵是 `(item_id, warehouse_id, bin_id, batch_id)`（`uq_stock_level`）——
同一批商品可以在同一倉庫的同一儲位存在於**不同批次**，於是多列共用同一組 key。
種子資料裡 `I-00003` / `I-00004` 各有一組重複，就會炸。

**為什麼沒被發現**：
- React 的 key 警告只在 **development build** 輸出，production build 直接把警告砍掉 → 上線看起來完全正常。
- 但這不是只有「看起來正常」：production 會重用同 key 的 DOM，批次之間的列可能互相污染。
- 真正的破口是 **API 沒回傳任何唯一識別碼**，前端想用 `id` 也沒得用。

**教訓**：
> **rowKey 必須來自資料庫主鍵或完整唯一鍵，不能用「看起來夠」的欄位拼。**
> 資料粒度（item+warehouse+bin）≠ 唯一鍵（再加上 batch）。
> 遇到 `duplicate key` 警告不要只在 dev 修，production 沒有警告不代表沒問題。

**防線**：
- `GET /api/stock` 回傳 `id`（`stock_levels` 主鍵）與 `batch_id`，前端 `StockRow` 型別同步。
- `Stock.tsx` 改用 `rowKey="id"`。
- 其他頁面的 `rowKey` 一律檢查過（`Items`/`PurchaseOrders`/`Transfers`/`SalesOrders` 用 `id`，
  `Reports` 用 `salesperson_id`、`Replenishment` 用 `item_id`，都唯一）。

---

## 2026-10-22 · 煙霧測試綁死 localhost，測不了公開部署

**現象**：對 Cloudflare Tunnel 的公開網址跑煙霧測試，7 個頁面全部「缺少預期內容」；
但同一支程式對 `localhost:5173` 全過。

**根因**：`smoke.mjs` 把 cookie 的 `domain` 寫死成 `'localhost'`。頁面開在 `trycloudflare.com`，
cookie 不會送出 → 未登入 → 跳登入頁 → 自然找不到「庫存現況」「業績與毛利」這些關鍵字。
session 本身是好的（Flask session 不綁網域），純粹是 cookie 沒送到。

**教訓**：
> **測試腳本裡寫死的 host 會讓測試只能測一種部署形态。**
> 「本機測過」不等於「部署後測過」——尤其部署形態改變時（dev server → preview → tunnel）。

**防線**：
- `smoke.mjs` 的 `APP` / `API` 改用環境變數覆寫（`APP_URL` / `API_URL`），預設值不變，既有流程不受影響。
- cookie 改用 `url: APP` 讓 CDP 自動帶出 domain/path/secure，不再寫死 `localhost`。
- 交付前除了跑預設的 localhost 煙霧測試，也用 `APP_URL=<公開網址>` 再跑一次，測的是真正上線的那條路徑。

---

## 2026-10-22 · 公開網址「活著但沒人知道」：行程被砍 + 網址會變

**現象**：
- Cloudflare Quick Tunnel 網址偶爾「連不上」，使用者只看到 `Error 1033` / 530。
- 服務本身沒崩：`flask.err` 與 `tunnel.err` 都乾淨結束、沒有 traceback。
- 而且**每次重新啟動，網址就換一個**（`trycloudflare.com` 隨機配發），舊的書籤立刻失效。

**根因（兩個）**：
1. 服務是用 Agent shell / `Start-Process` 起的，屬於 OpenCode 的行程樹。
   **OpenCode server 一重啟，整棵樹被砍掉** → 網址 530，但 log 看起來「正常結束」。
2. Quick Tunnel 沒有固定網址。任何重啟都等於換網址。

**教訓**：
> **「程序還在跑」≠「服務撐得過重啟」。** 任何要長期對外提供的東西，
> 都不能掛在開發工具的行程樹底下 —— 必須交給 OS 層級的服務管理者。
> 公開服務的「網址會變」是使用者體驗的大敵，必須在第一次交付時就講清楚。

**現在的防線**：
- 用 **Windows 工作排程器** 管理四個工作，各自在登入時啟動：
  `InventoryFlask`（5000）、`InventoryPreview`（4173，正式建置產物）、
  `InventoryDev`（5173，本機煙霧測試用）、`InventoryTunnel`（Quick Tunnel）。
  排程器由 Windows 服務管理，完全脫離 Agent 行程樹。
- **每個工作的 PowerShell 腳本自己是 supervisor**（外層 `while ($true)`），
  子行程死了就重新拉起。
  > 為什麼不靠排程器的「失敗後重新啟動」？實測 `RestartOnFailure`（Count=999 / Interval=PT1M）
  > **不會觸發**：子行程被殺後工作狀態變 `Ready`、`LastTaskResult=1`，排程器就是不重跑。
  > 腳本自己監看才有可預測的行為，`tunnel-task.log` 也留得下重啟紀錄。
- 每個啟動腳本**開跑前先清掉佔用該埠的殘留行程**（`taskkill /PID ... /T /F`），
  否則 vite 會「Port 4173 is in use, trying another one...」自動改跑 4174，
  而 tunnel 還是指向 4173 —— 表面正常，實際上 tunnel 連到的是幽靈行程。
- vite preview 加 `--strictPort`：埠被佔就**大聲失敗**，不要靜默換埠。
- 公開網址寫入 `tunnel-url.txt`，使用者隨時可查；桌面放 `庫存系統網址.cmd` 一鍵開啟。

**延伸教訓（Windows / PowerShell 地雷）**：
> **Windows PowerShell 5.1 的 `Start-Process -RedirectStandardError` 會阻塞到子行程結束**，
> 指令碼會卡在啟動那一步、後面的程式碼永遠跑不到（本次就卡在「寫入網址檔」之前）。
> 正確做法：**用 cmd 包一層做輸出轉向**（`cmd.exe /c "... 1>>a.log 2>>b.log"`），
> `Start-Process` 不帶 `-Redirect*` 才會立即返回。
>
> 另外 PS 5.1 讀**無 BOM 的 UTF-8 `.ps1` 會當 ANSI**，腳本裡任何非 ASCII 字面值（例如中文資料夾名）
> 都會變亂碼。→ 啟動腳本一律 ASCII-only，專案路徑用「掃描 `backend\wsgi.py` 找根目錄」的方式取得。
