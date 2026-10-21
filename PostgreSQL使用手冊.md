# PostgreSQL 資料庫使用手冊

> 適用專案：庫存管理系統
> 建立日期：2026-10-21
> 環境：Windows + PostgreSQL 18.6

---

## 一、環境資訊總覽

| 項目 | 內容 |
|------|------|
| PostgreSQL 版本 | 18.6（64-bit, Windows x86_64） |
| 安裝路徑 | `C:\Program Files\PostgreSQL\18\` |
| 資料目錄 | `C:\Program Files\PostgreSQL\18\data\` |
| Windows 服務名稱 | `postgresql-x64-18` |
| 主機位址 | `localhost`（= 127.0.0.1 / ::1） |
| 通訊埠 | `5432` |
| 登入帳號 | `postgres` |
| 認證方式 | `scram-sha-256`（需密碼） |
| 資料庫編碼 | UTF8 |
| 排序規則 | Chinese (Traditional)_Taiwan.950 |

### 專案資料庫
| 項目 | 內容 |
|------|------|
| 資料庫名稱 | **AILearn**（注意大小寫，`A`、`L` 為大寫） |
| 擁有者 | postgres |
| 編碼 | UTF8 |

---

## 二、確認 PostgreSQL 是否正常運作

### 1. 檢查服務狀態
在 PowerShell 執行：
```powershell
Get-Service postgresql-x64-18
```
`Status` 應顯示 **Running**。

### 2. 檢查伺服器是否接受連線
```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_isready.exe" -h localhost -p 5432
```
出現 `localhost:5432 - accepting connections` 即正常。

### 3. 檢查 psql 指令是否可用
```powershell
psql --version
```
應顯示 `psql (PostgreSQL) 18.6`。

> 補充：`C:\Program Files\PostgreSQL\18\bin` 已加入系統 PATH，
> 若新開的終端機仍找不到 `psql`，請關掉終端機重新開啟。

---

## 三、密碼管理

本專案採用 **密碼檔** 方式，避免每次手動輸入。

| 檔案 | 位置 |
|------|------|
| 密碼檔 | `C:\Users\GIGABYTE\Desktop\AI學習第一課\pg_password.txt` |
| 連線腳本 | `C:\Users\GIGABYTE\Desktop\AI學習第一課\connect_db.bat` |

> ⚠️ **安全提醒**
> - 密碼檔為「明碼」儲存，任何能讀取此電腦的人都看得到。
> - **請勿**將含密碼檔的資料夾上傳至 GitHub、雲端硬碟或分享給他人。
> - 若要分享專案，請先刪除 `pg_password.txt`。

### 修改密碼
```powershell
psql -U postgres -h localhost -c "ALTER USER postgres WITH PASSWORD '你的新密碼';"
```
改完後記得同步更新 `pg_password.txt` 的內容。

---

## 四、連線資料庫

### 方法 1：雙擊批次檔（最簡單）
雙擊 `connect_db.bat`，會自動讀取密碼檔並連上 `AILearn`。

### 方法 2：PowerShell 手動連線
```powershell
# 從密碼檔讀取密碼（不顯示於畫面）
$env:PGPASSWORD = (Get-Content "C:\Users\GIGABYTE\Desktop\AI學習第一課\pg_password.txt" -Raw).Trim()

# 連線到 AILearn 資料庫
psql -U postgres -h localhost -d AILearn
```

### 方法 3：手動輸入密碼
```powershell
psql -U postgres -h localhost -d AILearn
```
出現 `Password for user postgres:` 時輸入密碼。
（輸入時畫面不會顯示任何字元，這是正常現象，打完直接按 Enter）

---

## 五、常用 psql 指令

進入 `psql` 後（提示符為 `AILearn=#`）：

| 指令 | 說明 |
|------|------|
| `\l` | 列出所有資料庫 |
| `\c AILearn` | 切換到 AILearn 資料庫 |
| `\dt` | 列出目前資料庫的所有資料表 |
| `\d 資料表名` | 查看某資料表的結構 |
| `\du` | 列出所有使用者角色 |
| `\dn` | 列出所有 schema |
| `\x` | 切換「展開顯示」模式（適合寬表格） |
| `\q` | 離開 psql |
| `\?` | 查看所有 psql 指令說明 |
| `\h` | 查看 SQL 語法說明 |

---

## 六、建立資料庫 / 資料表

### 建立資料庫
```powershell
psql -U postgres -h localhost -c "CREATE DATABASE 資料庫名稱 ENCODING 'UTF8';"
```

> 注意：未加雙引號的名稱會被自動轉成**小寫**。
> 若要保留大小寫（如 `AILearn`），必須加上雙引號：
> ```sql
> CREATE DATABASE "AILearn" ENCODING 'UTF8';
> ```

### 刪除資料庫
```sql
DROP DATABASE "資料庫名稱";
```

### 建立資料表示例（庫存管理）
```sql
-- 商品資料表
CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(50),
    unit_price  NUMERIC(10,2) NOT NULL DEFAULT 0,
    stock_qty   INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 進出貨紀錄表
CREATE TABLE stock_movements (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    move_type   VARCHAR(10) NOT NULL,   -- 'IN' 進貨 / 'OUT' 出貨
    quantity    INTEGER NOT NULL,
    note        TEXT,
    moved_at    TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 基本資料操作（CRUD）
```sql
-- 新增
INSERT INTO products (name, category, unit_price, stock_qty)
VALUES ('A4 影印紙', '文具', 120.00, 50);

-- 查詢
SELECT * FROM products;
SELECT name, stock_qty FROM products WHERE stock_qty < 10;

-- 修改
UPDATE products SET unit_price = 130.00 WHERE name = 'A4 影印紙';

-- 刪除
DELETE FROM products WHERE id = 1;
```

---

## 七、備份與還原

### 備份（匯出）
```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -h localhost -d AILearn -f "備份檔案.sql"
```

### 還原（匯入）
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d AILearn -f "備份檔案.sql"
```

> 執行前記得先設定 `$env:PGPASSWORD` 或使用密碼檔。

---

## 八、常見問題排除

### Q1：`psql: 無法辨識 'psql'`（找不到指令）
**原因**：PATH 尚未在目前的終端機生效。
**解法**：關掉終端機重新開啟，或使用完整路徑：
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

### Q2：`password authentication failed for user "postgres"`
**原因**：密碼錯誤。
**解法**：確認 `pg_password.txt` 內容是否為最新密碼。

### Q3：`database "xxx" does not exist`
**原因**：資料庫名稱大小寫不符（PostgreSQL 會自動轉小寫）。
**解法**：名稱含大寫時，SQL 中要用雙引號：`"AILearn"`。

### Q4：服務沒啟動 / 無法連線
**解法**：以**系統管理員**身分開啟 PowerShell 後執行：
```powershell
Restart-Service postgresql-x64-18
```
或按 `Win + R` → `services.msc` → 找到 `postgresql-x64-18` → 右鍵「重新啟動」。

### Q5：忘記密碼
1. 備份並編輯 `C:\Program Files\PostgreSQL\18\data\pg_hba.conf`
2. 將 `scram-sha-256` 暫時改為 `trust`（需管理員權限）
3. 重新載入設定：
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" reload -D "C:\Program Files\PostgreSQL\18\data"
   ```
4. 免密碼登入並改密碼：
   ```powershell
   psql -U postgres -h localhost
   ```
   ```sql
   ALTER USER postgres WITH PASSWORD '新密碼';
   ```
5. **務必**將 `pg_hba.conf` 改回 `scram-sha-256`，再 reload 一次。

> ⚠️ `trust` 期間任何本機程式都能無密碼連線，改完一定要恢復設定。

---

## 九、檔案位置速查表

| 用途 | 路徑 |
|------|------|
| psql 執行檔 | `C:\Program Files\PostgreSQL\18\bin\psql.exe` |
| 伺服器設定 | `C:\Program Files\PostgreSQL\18\data\postgresql.conf` |
| 認證設定 | `C:\Program Files\PostgreSQL\18\data\pg_hba.conf` |
| 資料目錄 | `C:\Program Files\PostgreSQL\18\data\` |
| 密碼檔 | `C:\Users\GIGABYTE\Desktop\AI學習第一課\pg_password.txt` |
| 連線腳本 | `C:\Users\GIGABYTE\Desktop\AI學習第一課\connect_db.bat` |

---

## 十、快速開始（三步驟）

```powershell
# 1. 讀取密碼
$env:PGPASSWORD = (Get-Content "C:\Users\GIGABYTE\Desktop\AI學習第一課\pg_password.txt" -Raw).Trim()

# 2. 連線到 AILearn
psql -U postgres -h localhost -d AILearn

# 3. 查看資料庫內容
\dt
```

---

*本手冊由 AI 協助整理，實際設定請以你的環境為準。*
