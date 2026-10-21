# 庫存管理系統

一人開發的庫存／倉儲管理系統（課程作業）。目標：**數字對得起來** —— 所有庫存異動可追溯、毛利算得準、庫存不會變負。

- 需求文件：`_bmad-output/planning-artifacts/prds/prd-庫存管理系統-2026-10-21/prd.md`
- 架構脊椎：`_bmad-output/planning-artifacts/architecture/architecture-庫存管理系統-2026-10-21/ARCHITECTURE-SPINE.md`
- 施工清單：`_bmad-output/planning-artifacts/prds/prd-庫存管理系統-2026-10-21/mvp-scope.md`

---

## 1. 環境需求

| 項目 | 版本 | 說明 |
|---|---|---|
| Python | 3.14（本機）或 3.12（容器） | 已驗證 3.14.7 可用 |
| Node.js | 24.x | 已驗證 24.21.0 |
| PostgreSQL | 18.6 | 本機既有服務，資料庫 `AILearn` |
| Docker Desktop | 選用 | 未安裝則走「模式 A」本機直連 |

## 2. 環境變數

```powershell
cd backend
copy .env.example .env      # Windows（Mac/Linux 用 cp）
# 編輯 .env：
#   DATABASE_URL=postgresql+psycopg://postgres:<密碼>@localhost:5432/AILearn
#   SECRET_KEY=<隨機字串>
```

> ⚠️ **連線字串的 URI 路徑段不可加引號**：`.../AILearn` 才是對的；寫成 `.../"AILearn"` 會得到 `database ""AILearn"" does not exist`。
> 密碼含 `@ : / # ?` 等字元時需 URL 編碼。

## 3. 安裝與初始化

```powershell
# 後端
uv venv .venv --python 3.14          # 或 python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r backend\requirements.txt
cd backend
..\.venv\Scripts\python.exe -m flask db upgrade      # 套用遷移（建立 18 張表）
..\.venv\Scripts\python.exe -m flask seed --reset     # 載入示範資料

# 前端
cd ..\frontend
npm install
npm run dev                            # http://localhost:5173
```

## 4. 啟動

```powershell
# 終端機 1：後端
cd backend
..\.venv\Scripts\python.exe -m flask run --port 5000

# 終端機 2：前端
cd frontend
npm run dev
```

開 http://localhost:5173 ，Vite 會把 `/api` 代理到 `http://127.0.0.1:5000`。

**容器模式（選用）**

```powershell
$env:POSTGRES_PASSWORD = "yourpassword"
docker compose up
```
容器 postgres 對外映射 **5433**（本機 5432 已被既有服務佔用）。

## 5. 測試帳號

| 帳號 | 角色 | 能做什麼 |
|---|---|---|
| `admin` | 管理員 | 全部 |
| `warehouse` | 倉管 | 入庫、出庫、盤點填報 |
| `purchasing` | 採購 | 採購單、補貨建議 |
| `sales` / `sales2` / `sales3` | 銷售 | 銷售單、出貨 |
| `accounting` | 會計 | 業績與毛利報表、庫存現況 |
| `manager` | 主管 | 報表、盤點核准、補貨建議 |
| `viewer` | 唯讀 | 唯讀檢視 |

密碼統一：`Passw0rd!`（示範用，正式環境請更換）

> **角色切換**：畫面右上角的下拉選單可一鍵切換 7 個示範帳號（密碼相同），用來示範「不同角色看到不同選單」——例如切到 `sales` 就看不到「業績與毛利」，切到 `manager` 就看得到。

## 6. 自我檢查腳本

```powershell
# 1) 資料庫層不變量（9 項）：三數字、交易流=庫存總量、毛利可加總、成本快照
.venv\Scripts\python.exe backend\scripts\verify_mvp.py

# 2) HTTP 端到端（17 項）：需後端已啟動
.venv\Scripts\python.exe backend\scripts\verify_api.py

# 3) 全功能測試（64 項）：所有讀取端點 + 角色權限矩陣 + 完整寫入流程
.venv\Scripts\python.exe backend\scripts\test_all_features.py

# 4) 端點巡檢（快速看所有 GET 的狀態與筆數）
.venv\Scripts\python.exe backend\scripts\sweep_endpoints.py

# 5) 前端煙霧測試（7 個頁面實際渲染，檢查 console 錯誤與空白頁）
node frontend\scripts\smoke.mjs

# 6) 前端型別檢查（build 腳本已包含，漏 import 的元件會擋下來）
cd frontend && npx tsc --noEmit
```

> **為什麼需要前端煙霧測試**：`vite build` 只做轉譯不做型別檢查，所以「漏 import 一個元件」這種錯誤會直接送到使用者面前（曾造成「業績與毛利」整頁空白）。`npm run build` 現在會先跑 `tsc --noEmit`，而煙霧測試會用 headless Edge 實際開啟每個頁面，兩道防線一起擋掉這類問題。

**全功能測試涵蓋的流程**

| 區塊 | 內容 |
|---|---|
| 讀取端點 | 19 個 GET 端點逐一驗證 |
| 角色權限矩陣 | 15 組「角色 × 端點」期望狀態（200／403） |
| 商品與供應商 | 建立、重複統編被拒、中文搜尋 |
| 採購與入庫 | 建立 → 送出 → 差異原因必填 → 入庫 → 在手數量正確 |
| 補貨建議 | 低於水位出現、建議量算法、一鍵轉採購單、跨倉建議 |
| 調撥 | 建立 → 調出（在途不計可用）→ 調入（目標倉 +5） |
| 銷售 | 試算（可用量/毛利）→ 建立 → 送出（占用+2）→ 出貨（毛利正確） |
| 防呆 | 超量出貨被擋、空品項被拒、未登入 401、錯密 401、未知端點 404 |

## 7. 架構

```
瀏覽器 (React 19 + antd 6)
   │  REST /api（session cookie）
   ▼
Flask 3.1 (routes → services → models)
   │
   ▼
PostgreSQL 18.6 (18 張表，schema 變更走 Alembic 遷移)
```

**四條不能破的規則**（詳見 ARCHITECTURE-SPINE.md）

1. **庫存數字只有一個寫入口**：所有 `stock_levels` / `stock_ledger` / `item_costs` 的寫入只能經 `StockService`。
2. **一個 use case = 一個交易**：交易在服務層開啟，失敗整筆回滾。
3. **可用量 = 在手 − 占用**，只有一個算法；出庫用原子條件更新，庫存不足直接擋。
4. **出庫當下寫入成本快照**，之後成本變動不回溯改寫歷史毛利。

## 8. 已知限制

- 移動平均成本一旦有交易不可切換為 FIFO。
- 不允許負庫存；庫存不足一律阻擋並提供調撥／補貨路徑。
- 不含退貨（RMA）流程、條碼掃碼、IoT 硬體對接、通知推播。
- 盤點（範圍鎖定與差異核准）列為 P1，尚未實作。
- 出貨批次目前以 FIFO 挑選；FEFO（依效期）為 P2。
- 本機 PostgreSQL 為 Windows 專屬 collation，容器以 ICU `zh-TW`，兩者排序結果可能不同（排序鍵在應用層指定）。
