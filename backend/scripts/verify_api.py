"""HTTP 端到端測試：登入 → 庫存現況 → 補貨建議 → 業績報表 → 權限拒絕。"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5000/api"
PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((PASS if ok else FAIL, name, detail))


def call(method: str, path: str, body=None, token: str | None = None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Cookie", f"session={token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), resp.headers.get("Set-Cookie")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw), None
        except json.JSONDecodeError:
            return e.code, {"raw": raw}, None


def main() -> int:
    # 1. 登入
    status, body, cookie = call("POST", "/auth/login", {"username": "sales", "password": "Passw0rd!"})
    check("登入成功（sales）", status == 200 and body.get("role") == "sales", f"status={status}")
    token = ""
    if cookie:
        token = cookie.split("session=")[1].split(";")[0]

    # 2. 錯密
    status, body, _ = call("POST", "/auth/login", {"username": "sales", "password": "wrong"})
    check("錯誤密碼被拒（401）", status == 401 and body.get("code") == "UNAUTHORIZED", f"status={status}")

    # 3. 未登入存取
    status, body, _ = call("GET", "/stock")
    check("未登入被拒（401）", status == 401, f"status={status}")

    # 3b. 登入後 /auth/me 必須回傳使用者（前端靠它判斷登入狀態）
    status, body, _ = call("GET", "/auth/me", token=token)
    check(
        "登入後 /auth/me 回傳使用者與權限",
        status == 200 and body.get("username") == "sales" and body.get("capabilities"),
        f"status={status} {json.dumps(body, ensure_ascii=False)[:120]}",
    )

    # 4. 庫存現況
    status, body, _ = call("GET", "/stock?size=5", token=token)
    check(
        "庫存現況可查且含三數字",
        status == 200 and body.get("items") and "on_hand" in body["items"][0] and "available" in body["items"][0],
        f"total={body.get('total')}",
    )

    # 5. 權限：sales 不該能看業績報表
    status, body, _ = call("GET", "/reports/sales-performance", token=token)
    check("sales 角色看不到業績報表（403）", status == 403, f"status={status}")

    # 6. 切 manager 看業績
    status, body, cookie2 = call("POST", "/auth/login", {"username": "manager", "password": "Passw0rd!"})
    mtoken = cookie2.split("session=")[1].split(";")[0] if cookie2 else ""
    status, body, _ = call("GET", "/reports/sales-performance?period=all", token=mtoken)
    check(
        "業績報表可查且有毛利欄位",
        status == 200 and body.get("items") and "gross_margin" in body["items"][0],
        f"status={status} 人數={len(body.get('items', []))} {json.dumps(body, ensure_ascii=False)[:200]}",
    )

    # 7. 補貨建議
    status, body, _ = call("GET", "/replenishment?mode=purchase", token=mtoken)
    check("補貨建議有內容", status == 200 and len(body.get("items", [])) > 0, f"{len(body.get('items', []))} 筆")

    # 8. 庫存週轉率
    status, body, _ = call("GET", "/reports/inventory-turnover?period=all", token=mtoken)
    check("庫存週轉率可算", status == 200 and "turnover" in body, json.dumps(body, ensure_ascii=False))

    # 9. 商品清單（中文關鍵字需 URL 編碼）
    keyword = urllib.parse.quote("飲料")
    status, body, _ = call("GET", f"/items?q={keyword}", token=mtoken)
    check("商品搜尋（含中文）", status == 200 and body.get("total", 0) >= 1, f"total={body.get('total')}")

    # 10. 銷售試算（毛利由後端算，AD-9）
    status, body, _ = call("GET", "/stock?size=1", token=token)
    level = body["items"][0] if body.get("items") else None
    if level:
        status, body, _ = call(
            "POST",
            "/sales-orders/preview",
            {"lines": [{"item_id": level["item_id"], "warehouse_id": level["warehouse_id"], "qty": 1}]},
            token=token,
        )
        preview_ok = (
            status == 200
            and body.get("lines")
            and "gross_margin" in body["lines"][0]
            and "available" in body["lines"][0]
        )
        check("銷售試算回傳可用量與毛利（AD-9）", preview_ok, json.dumps(body, ensure_ascii=False)[:160])

    # 11. 銷售端建立訂單 → 出庫 → 毛利
    status, body, _ = call("GET", "/stock?size=1", token=mtoken)
    level = body["items"][0] if body.get("items") else None
    if level:
        status, body, _ = call(
            "POST",
            "/sales-orders",
            {
                "customer_name": "E2E 測試客戶",
                "lines": [
                    {
                        "item_id": level["item_id"],
                        "warehouse_id": level["warehouse_id"],
                        "bin_id": level["bin_id"],
                        "qty": 1,
                        "unit_price": 100,
                    }
                ],
            },
            token=token,
        )
        check("建立銷售單（sales 角色）", status == 201, f"status={status} {body.get('code','')}")
        if status == 201:
            so_id = body["id"]
            status, body, _ = call("POST", f"/sales-orders/{so_id}/send", {}, token=token)
            check("送出銷售單（建立占用）", status == 200, f"status={status} {body.get('code','')}")
            status, body, _ = call("POST", f"/sales-orders/{so_id}/ship", {}, token=token)
            check(
                "出貨並產生毛利",
                status == 200 and "gross_margin" in body,
                json.dumps(body, ensure_ascii=False),
            )
    else:
        check("取得庫存以進行銷售測試", False, "無庫存資料")

    # 12. 調撥：建立 → 調出（在途）→ 調入
    status, body, cookie3 = call("POST", "/auth/login", {"username": "purchasing", "password": "Passw0rd!"})
    ptoken = cookie3.split("session=")[1].split(";")[0] if cookie3 else ""
    status, body, _ = call("GET", "/stock?size=1", token=ptoken)
    src = body["items"][0] if body.get("items") else None
    status, whbody, _ = call("GET", "/warehouses", token=ptoken)
    whs = whbody.get("items", []) if status == 200 else []
    target = next((w for w in whs if src and w["id"] != src["warehouse_id"]), None)
    if src and target:
        status, body, _ = call(
            "POST",
            "/transfers",
            {
                "item_id": src["item_id"],
                "from_warehouse_id": src["warehouse_id"],
                "from_bin_id": src["bin_id"],
                "to_warehouse_id": target["id"],
                "to_bin_id": None,
                "qty": 5,
            },
            token=ptoken,
        )
        check("建立調撥單（purchasing）", status == 201, f"status={status} {body}")
        if status == 201:
            tid = body["id"]
            # 調出／調入由倉管執行（transfer.execute）
            status, body, cookie4 = call("POST", "/auth/login", {"username": "warehouse", "password": "Passw0rd!"})
            wtoken = cookie4.split("session=")[1].split(";")[0] if cookie4 else ""
            status, body, _ = call("POST", f"/transfers/{tid}/out", {}, token=wtoken)
            check("調出 → 在途", status == 200 and body.get("status") == "in_transit", f"status={status} {body}")
            status, body, _ = call("POST", f"/transfers/{tid}/receive", {}, token=wtoken)
            check("調入 → 計入目標倉", status == 200 and body.get("status") == "received", f"status={status} {body}")
    else:
        check("取得來源庫存以進行調撥測試", False, f"src={bool(src)} target={bool(target)}")

    print("\n=== HTTP API 端到端測試 ===")
    for status, name, detail in results:
        print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    failed = [r for r in results if r[0] == FAIL]
    print(f"\n{len(results) - len(failed)}/{len(results)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
