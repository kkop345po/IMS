# -*- coding: utf-8 -*-
"""全功能測試：把 PRD 的 P0 功能與每個 API 端點都跑一遍。

執行方式：
    .venv\\Scripts\\python.exe backend\\scripts\\test_all_features.py

需要後端已啟動（http://127.0.0.1:5000）。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "http://127.0.0.1:5000/api"
PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((PASS if ok else FAIL, name, detail))
    print(f"[{PASS if ok else FAIL}] {name}" + (f" — {detail}" if detail else ""))


def call(method: str, path: str, body=None, token: str | None = None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Cookie", f"session={token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8")), r.headers.get("Set-Cookie")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw), None
        except json.JSONDecodeError:
            return e.code, {"raw": raw[:200]}, None
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}, None


def login(username: str) -> str | None:
    s, b, c = call("POST", "/auth/login", {"username": username, "password": "Passw0rd!"})
    if s != 200 or not c:
        return None
    return c.split("session=")[1].split(";")[0]


def pick_stock_row(token: str, min_available: float = 10.0, exclude: set[int] | None = None):
    """挑一筆真的有庫存的列（測試可重複執行）。"""
    exclude = exclude or set()
    s, b, _ = call("GET", "/stock?size=200", token=token)
    if s != 200:
        return None
    best = None
    for row in b.get("items", []):
        if row["item_id"] in exclude:
            continue
        if float(row["available"]) >= min_available:
            if best is None or float(row["available"]) > float(best["available"]):
                best = row
    return best


def main() -> int:
    print("=" * 70)
    print("庫存管理系統 — 全功能測試")
    print("=" * 70)

    # ── 0. 七個角色登入 ────────────────────────────────────
    roles = ["admin", "warehouse", "purchasing", "sales", "accounting", "manager", "viewer"]
    T: dict[str, str] = {}
    for r in roles:
        T[r] = login(r)
    missing = [r for r in roles if not T[r]]
    check("7 個角色皆可登入", not missing, f"失敗：{missing}" if missing else "admin/warehouse/purchasing/sales/accounting/manager/viewer")
    if missing:
        return 1
    admin = T["admin"]

    # ── 1. 端點巡檢（全部 GET）────────────────────────────
    print("\n--- 1. 讀取端點巡檢 ---")
    get_paths = [
        "/items", "/items?q=%E9%A3%B2%E6%96%99", "/suppliers", "/warehouses", "/bins",
        "/stock", "/stock?low_only=1", "/stock/ledger",
        "/purchase-orders", "/sales-orders", "/transfers",
        "/replenishment?mode=purchase", "/replenishment?mode=transfer",
        "/reports/sales-performance?period=all",
        "/reports/sales-performance?period=month",
        "/reports/inventory-turnover?period=all",
        "/users", "/auth/me", "/health",
    ]
    for p in get_paths:
        s, b, _ = call("GET", p, token=admin)
        check(f"GET {p}", s == 200, f"status={s} {json.dumps(b, ensure_ascii=False)[:120]}" if s != 200 else "")

    # ── 2. 角色權限矩陣 ────────────────────────────────────
    print("\n--- 2. 角色權限矩陣（FR-28）---")
    matrix = [
        ("viewer", "/reports/sales-performance?period=all", 200),
        ("viewer", "/purchase-orders", 403),
        ("sales", "/reports/sales-performance?period=all", 403),
        ("sales", "/sales-orders", 200),
        ("sales", "/purchase-orders", 403),
        ("warehouse", "/stock", 200),
        ("warehouse", "/purchase-orders", 403),
        ("warehouse", "/sales-orders", 403),
        ("purchasing", "/purchase-orders", 200),
        ("purchasing", "/sales-orders", 403),
        ("purchasing", "/replenishment?mode=purchase", 200),
        ("accounting", "/reports/sales-performance?period=all", 200),
        ("accounting", "/sales-orders", 403),
        ("manager", "/reports/sales-performance?period=all", 200),
        ("manager", "/users", 403),
    ]
    for user, path, expect in matrix:
        s, b, _ = call("GET", path, token=T[user])
        check(f"{user:11s} GET {path}", s == expect, f"got={s} expect={expect}")

    # ── 3. 商品與供應商（FR-1、FR-2、FR-5）──────────────
    print("\n--- 3. 商品與供應商 ---")
    suffix = datetime.now(timezone.utc).strftime("%H%M%S")
    s, b, _ = call("POST", "/suppliers", {
        "tax_id": f"9{suffix}", "company_name": "測試供應商股份有限公司",
        "contact_name": "測試聯絡人", "phone": "02-0000-0000",
    }, token=admin)
    check("建立供應商", s == 201, f"status={s} {b}")
    supplier_id = b.get("id") if s == 201 else None
    if supplier_id:
        s, b, _ = call("POST", "/suppliers", {
            "tax_id": f"9{suffix}", "company_name": "重複統編測試",
        }, token=admin)
        check("重複統編被拒（FR-5）", s == 400 and b.get("code") == "VALIDATION_ERROR", f"status={s} {b}")

    s, b, _ = call("POST", "/items", {
        "name": f"測試商品-{suffix}", "category": "測試", "supplier_id": supplier_id,
        "default_purchase_price": 10, "default_selling_price": 20,
        # 水位設高於稍後的入庫量（280），才會出現在補貨建議裡
        "min_stock": 500, "max_stock": 800, "uom_base": "箱",
        "uoms": [{"unit_name": "個", "conversion_factor": 20}],
    }, token=admin)
    check("建立商品", s == 201 and b.get("code", "").startswith("I-"), f"status={s} {b}")
    item_id = b.get("id") if s == 201 else None
    item_code = b.get("code") if s == 201 else None
    if item_id:
        s, b, _ = call("GET", f"/items?q={urllib.parse.quote('測試商品')}", token=admin)
        check("中文搜尋找得到新商品", s == 200 and any(i["id"] == item_id for i in b.get("items", [])),
              f"total={b.get('total')}")

    # ── 4. 採購單 → 入庫（FR-19、FR-8）────────────────────
    print("\n--- 4. 採購單與入庫 ---")
    s, b, _ = call("GET", "/warehouses", token=admin)
    wh = b["items"][0]["id"] if s == 200 and b.get("items") else None
    s, b, _ = call("GET", "/bins", token=admin)
    bins = [x for x in (b.get("items", []) if s == 200 else []) if wh and x["warehouse_id"] == wh]
    bin_id = bins[0]["id"] if bins else None
    s, b, _ = call("POST", "/purchase-orders", {
        "supplier_id": supplier_id,
        "lines": [{"item_id": item_id, "qty": 300, "unit_price": 10}],
    }, token=admin)
    check("建立採購單", s == 201, f"status={s} {b}")
    po_id = b.get("id") if s == 201 else None
    po_no = b.get("po_no") if s == 201 else None
    if po_id:
        s, b, _ = call("POST", f"/purchase-orders/{po_id}/send", {}, token=T["purchasing"])
        check("送出採購單", s == 200 and b.get("status") == "sent", f"status={s} {b}")
        s, b, _ = call("GET", f"/purchase-orders", token=admin)
        po = next((p for p in b.get("items", []) if p["id"] == po_id), None)
        line_id = po["lines"][0]["id"] if po else None
        if line_id:
            # 差異原因必填（FR-8）
            s, b, _ = call("POST", f"/purchase-orders/{po_id}/receive", {
                "line_id": line_id, "received_qty": 280,
                "warehouse_id": wh, "bin_id": bin_id,
            }, token=T["warehouse"])
            check("實收不足且未填差異原因 → 被拒（FR-8）", s == 400, f"status={s} {b}")
            s, b, _ = call("POST", f"/purchase-orders/{po_id}/receive", {
                "line_id": line_id, "received_qty": 280, "diff_reason": "測試：破損 2 箱",
                "warehouse_id": wh, "bin_id": bin_id, "lot_code": f"LOT-{suffix}",
            }, token=T["warehouse"])
            check("收貨入庫（有填差異原因）", s == 200, f"status={s} {b}")
            s, b, _ = call("GET", f"/stock?item_id={item_id}", token=admin)
            row = b["items"][0] if b.get("items") else None
            on_hand = float(row["on_hand"]) if row else 0
            check("入庫後在手數量 = 280", row is not None and abs(on_hand - 280) < 0.001,
                  f"on_hand={row.get('on_hand') if row else 'n/a'}")

    # ── 5. 補貨建議（FR-17、FR-18）────────────────────────
    print("\n--- 5. 補貨建議 ---")
    s, b, _ = call("GET", "/replenishment?mode=purchase", token=T["purchasing"])
    items = b.get("items", [])
    hit = next((i for i in items if i["item_id"] == item_id), None)
    check("低於水位的品項出現在補貨建議", hit is not None,
          f"建議 {len(items)} 筆" + (f"，測試品項建議 {hit['suggest_qty']}" if hit else ""))
    if hit:
        check("建議補貨量 = 最高水位 − 可用量",
              abs(float(hit["suggest_qty"]) - (float(hit["max_stock"]) - float(hit["available"]))) < 0.001,
              f"suggest={hit['suggest_qty']} available={hit['available']} max={hit['max_stock']}")
        s, b, _ = call("POST", "/replenishment/to-purchase", {
            "supplier_id": supplier_id,
            "lines": [{"item_id": hit["item_id"], "qty": float(hit["suggest_qty"]), "unit_price": float(hit["unit_price"])}],
        }, token=T["purchasing"])
        check("一鍵轉採購單（FR-17 → FR-19）", s == 201, f"status={s} {b}")
    s, b, _ = call("GET", "/replenishment?mode=transfer", token=T["purchasing"])
    check("跨倉調撥建議可產生", s == 200, f"status={s} items={len(b.get('items', []))}")

    # ── 6. 調撥（FR-12、FR-18）───────────────────────────
    print("\n--- 6. 調撥單 ---")
    s, b, _ = call("GET", "/stock?size=200", token=admin)
    src = pick_stock_row(admin, min_available=10, exclude={item_id} if item_id else set())
    s, b, _ = call("GET", "/warehouses", token=admin)
    whs = b.get("items", [])
    target = next((w for w in whs if src and w["id"] != src["warehouse_id"]), None)
    if src and target:
        s, b, _ = call("POST", "/transfers", {
            "item_id": src["item_id"], "from_warehouse_id": src["warehouse_id"],
            "from_bin_id": src["bin_id"], "to_warehouse_id": target["id"], "qty": 5,
        }, token=T["purchasing"])
        check("建立調撥單", s == 201, f"status={s} {b}")
        tid = b.get("id") if s == 201 else None
        if tid:
            def wh_total(wid: int) -> float:
                """該商品在指定倉庫的在庫總量（所有儲位/批次加總）。"""
                s2, b2, _ = call("GET", f"/stock?item_id={src['item_id']}&warehouse_id={wid}", token=admin)
                return sum(float(x["on_hand"]) for x in b2.get("items", [])) if b2.get("items") else 0.0

            before = wh_total(src["warehouse_id"])
            target_before = wh_total(target["id"])
            s, b, _ = call("POST", f"/transfers/{tid}/out", {}, token=T["warehouse"])
            check("調出 → 在途", s == 200 and b.get("status") == "in_transit", f"status={s} {b}")
            during = wh_total(src["warehouse_id"])
            check("在途期間來源倉總量減少 5（不計入可用）", abs((before - during) - 5) < 0.001,
                  f"{before} → {during}")
            s, b, _ = call("POST", f"/transfers/{tid}/receive", {}, token=T["warehouse"])
            check("調入 → 計入目標倉", s == 200 and b.get("status") == "received", f"status={s} {b}")
            after = wh_total(target["id"])
            check("目標倉庫存增加 5 單位", abs((after - target_before) - 5) < 0.001,
                  f"{target_before} → {after}")

    # ── 7. 銷售（FR-20～FR-23、FR-26）───────────────────
    print("\n--- 7. 銷售與毛利 ---")
    s, b, _ = call("GET", "/stock?size=200", token=T["sales"])
    stock_row = pick_stock_row(T["sales"], min_available=5, exclude={item_id} if item_id else set())
    if stock_row:
        s, b, _ = call("POST", "/sales-orders/preview", {
            "lines": [{"item_id": stock_row["item_id"], "warehouse_id": stock_row["warehouse_id"], "qty": 2}],
        }, token=T["sales"])
        p = b.get("lines", [{}])[0] if s == 200 else {}
        check("銷售試算回傳可用量與毛利（FR-20）",
              s == 200 and "available" in p and "gross_margin" in p, json.dumps(p, ensure_ascii=False)[:140])
        s, b, _ = call("POST", "/sales-orders", {
            "customer_name": "全功能測試客戶",
            "lines": [{"item_id": stock_row["item_id"], "warehouse_id": stock_row["warehouse_id"], "qty": 2,
                       "unit_price": 50}],
        }, token=T["sales"])
        check("建立銷售單", s == 201, f"status={s} {b}")
        so_id = b.get("id") if s == 201 else None
        if so_id:
            s, b, _ = call("POST", f"/sales-orders/{so_id}/send", {}, token=T["sales"])
            check("送出銷售單（建立占用）", s == 200 and b.get("status") == "sent", f"status={s} {b}")
            s, b, _ = call("GET", f"/stock?item_id={stock_row['item_id']}&warehouse_id={stock_row['warehouse_id']}", token=admin)
            reserved = sum(float(x["reserved"]) for x in b.get("items", [])) if b.get("items") else 0
            check("送出後占用增加 2", reserved >= 2, f"reserved={reserved}")
            s, b, _ = call("POST", f"/sales-orders/{so_id}/ship", {}, token=T["sales"])
            gm = float(b.get("gross_margin", 0)) if s == 200 else 0
            total_amt = float(b.get("total", 0)) if s == 200 else 0
            cost_amt = float(b.get("total_cost", 0)) if s == 200 else 0
            check("出貨並回傳毛利", s == 200 and b.get("status") == "shipped" and gm != 0, f"status={s} {b}")
            check("毛利 = 應收 − 銷貨成本（FR-26）", abs(gm - (total_amt - cost_amt)) < 0.01,
                  f"total={total_amt} cost={cost_amt} margin={gm}")
            s, b, _ = call("GET", "/reports/sales-performance?period=all", token=T["accounting"])
            total = sum(float(x["gross_margin"]) for x in b.get("items", []))
            check("業績報表毛利合計 > 0", total > 0, f"合計={total}")

    # 超量出貨阻擋
    s, b, _ = call("POST", "/sales-orders", {
        "customer_name": "超量測試",
        "lines": [{"item_id": stock_row["item_id"] if stock_row else 1,
                   "warehouse_id": stock_row["warehouse_id"] if stock_row else 1, "qty": 99999999}],
    }, token=T["sales"])
    over_id = b.get("id") if s == 201 else None
    if over_id:
        s, b, _ = call("POST", f"/sales-orders/{over_id}/send", {}, token=T["sales"])
        check("超量出貨被阻擋（AD-3）", s == 409 and b.get("code") == "OUT_OF_STOCK", f"status={s} {b}")

    # ── 8. 錯誤處理 ───────────────────────────────────────
    print("\n--- 8. 錯誤處理 ---")
    s, b, _ = call("POST", "/sales-orders", {"lines": []}, token=T["sales"])
    check("空品項被拒", s == 400, f"status={s} {b}")
    s, b, _ = call("GET", "/stock", token=None)
    check("未登入被拒（401）", s == 401, f"status={s}")
    s, b, _ = call("POST", "/auth/login", {"username": "admin", "password": "wrong"})
    check("錯誤密碼被拒（401）", s == 401, f"status={s}")
    s, b, _ = call("GET", "/nonexistent-endpoint", token=admin)
    check("不存在的端點回 404", s == 404, f"status={s}")

    # ── 總結 ─────────────────────────────────────────────
    failed = [r for r in results if r[0] == FAIL]
    print("\n" + "=" * 70)
    print(f"總計：{len(results) - len(failed)}/{len(results)} 通過")
    if failed:
        print("失敗項目：")
        for _, name, detail in failed:
            print(f"  ✗ {name} — {detail}")
    print("=" * 70)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
