# AGENTS.md — 庫存管理系統專案規則

> 這份文件會被 OpenCode 自動載入。**改任何程式碼前先讀，改完必須跑完「交付前檢查清單」。**
> 背景事故見 `docs/lessons-learned.md`（每次出包或踩坑都應該回來補一筆）。

## 專案是什麼

庫存／倉儲管理系統（課程作業，一人開發）。需求在
`_bmad-output/planning-artifacts/prds/prd-庫存管理系統-2026-10-21/prd.md`，
架構規則在 `_bmad-output/planning-artifacts/architecture/architecture-庫存管理系統-2026-10-21/ARCHITECTURE-SPINE.md`。

技術棧：**React 19 + antd 6 + Vite 8 + React Router 8 + TanStack Query 5**（前端）／
**Flask 3.1 + SQLAlchemy 2.0 + Flask-Migrate + psycopg 3 + PostgreSQL 18.6**（後端）。

## 交付前檢查清單（缺一不可）

```powershell
# 後端
.venv\Scripts\python.exe backend\scripts\verify_mvp.py        # 9 項：資料庫不變量
.venv\Scripts\python.exe backend\scripts\verify_api.py        # 17 項：HTTP 端到端
.venv\Scripts\python.exe backend\scripts\test_all_features.py # 64 項：全功能

# 前端（兩道都要，缺一不可）
cd frontend
npm run build            # 內含 tsc --noEmit：漏 import / 未定義變數會擋下來
node scripts\smoke.mjs   # headless Edge 實際渲染 7 個頁面，檢查 console 錯誤與空白頁
```

> **只測 API 不等於測過頁面。** 純後端測試抓不到「元件漏 import 造成整頁空白」這類問題；
> 反之只跑前端也不知道數字對不對。兩邊都要跑。

## 硬性規則

1. **庫存數字只有一個寫入口**：任何改到 `stock_levels` / `stock_ledger` / `item_costs` 的動作，
   只能呼叫 `StockService` 的公開方法（spine AD-1）。路由、其他 service、ORM event 都不得直接寫這三張表。
2. **一個 use case = 一個交易**：交易在 service 層開啟（`stock_service.transaction()`），失敗整筆回滾（AD-2）。
3. **可用量只有一個算法**：`available = on_hand - reserved`，出庫用原子條件更新，庫存不足直接擋（AD-3）。
4. **出庫當下寫入成本快照** `unit_cost_snapshot`，之後成本變動不回溯改寫歷史毛利（AD-4）。
5. **授權只認 FR-28 的權限矩陣**：`ROLE_PERMISSIONS` 是唯一來源，每個端點都要掛 `require_capability`（AD-6）。
6. **數量與金額用 `NUMERIC` / `Decimal`**，禁止 float；時間用 `timestamptz` 存 UTC；金額一律 NT$（AD-7）。
7. **只走 ORM 參數化查詢**，禁止字串拼 SQL；機密只走環境變數（AD-8）。
8. **毛利與可用量一律後端算**，前端不推算（AD-9）。
9. **中文搜尋用 `ILIKE` + `pg_trgm`**，不用 FTS（本機 `default_text_search_config=simple` 對中文會靜默零結果）（AD-10）。
10. **批次由後端挑選並回寫**（AD-11）：未指定儲位／批次時用 `pick_level()` 依 FIFO 挑，結果寫回單據行。

## 前端注意事項

- **antd v6 API**：`Space` 用 `orientation="vertical"`（不是 `direction`）、`Statistic` 用 `styles={{ content: {...} }}`（不是 `valueStyle`）。
  棄用 API 會噴 console 錯誤，煙霧測試會判失敗。
- **新增元件後一定要跑 `npm run build`**：build 腳本已改為 `tsc --noEmit && vite build`，漏 import 會直接擋下來。
- **新增頁面後一定要把路由加進 `frontend/scripts/smoke.mjs` 的 `ROUTES`**，否則等於沒測。
- 中文檔案一律 **UTF-8 無 BOM**。

## Windows / PowerShell 地雷（踩過）

- **不要用 `Get-Content` / `Set-Content` 改中文檔**：它們用主機 ANSI 編碼讀寫，會把 UTF-8 中文弄成亂碼。
  改檔用 `edit` / `write` 工具；必須用 PowerShell 時用
  `[System.IO.File]::ReadAllText()` + `[System.IO.File]::WriteAllText(..., (New-Object System.Text.UTF8Encoding($false)))`。
- **不要用 `Set-Content -Encoding utf8`**：PowerShell 5.1 會寫出 BOM，導致 dotenv 讀不到第一個變數。
- **資料庫連線字串的路徑段不可加引號**：`postgresql+psycopg://user:pw@host:5432/AILearn` 才是對的，
  加引號會得到 `database ""AILearn"" does not exist`。
- **本機 5432 已被既有 PostgreSQL 服務佔用**，容器模式要映射 5433。
- 跑 Python 腳本時設 `$env:PYTHONUTF8="1"`，否則 Windows cp950 會讓中文輸出亂碼或拋 UnicodeEncodeError。

## 種子資料

`flask seed --reset` 會重建示範資料（3 倉庫、12 商品、15 銷售單、3 採購單、1 在途調撥、26 筆庫存、7 個角色帳號，
密碼統一 `Passw0rd!`）。**測試跑完要重置**，否則 demo 畫面會混入測試建立的垃圾資料。

## 新增功能的順序

1. 先看 PRD 有沒有對應 FR，沒有就先回頭補 PRD（不要在程式碼裡偷偷擴張範圍）。
2. 後端：service → api → 測試。
3. 前端：api client → 頁面 → 路由 → **smoke.mjs 的 ROUTES**。
4. 跑完整檢查清單。
5. 踩到坑 → 補 `docs/lessons-learned.md`。
