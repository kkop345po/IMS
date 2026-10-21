# -*- coding: utf-8 -*-
"""檢查各角色能否看到「業績與毛利」，以及報表資料內容。"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5000/api"
ROLES = ["admin", "accounting", "manager", "viewer", "sales", "warehouse", "purchasing"]


def login(name):
    req = urllib.request.Request(
        BASE + "/auth/login",
        data=json.dumps({"username": name, "password": "Passw0rd!"}).encode(),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.headers.get("Set-Cookie").split("session=")[1].split(";")[0]


def get(path, token):
    req = urllib.request.Request(BASE + path)
    req.add_header("Cookie", "session=" + token)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


for role in ROLES:
    t = login(role)
    _, me = get("/auth/me", t)
    caps = me.get("capabilities", [])
    s, data = get("/reports/sales-performance?period=all", t)
    n = len(data.get("items", [])) if isinstance(data, dict) else 0
    mark = "可看到" if "report.view" in caps else "看不到"
    print(f"{role:11s} report.view={'Y' if 'report.view' in caps else 'N'}  選單={mark:5s}  報表 HTTP {s}  列數={n}")

print("\n=== 業績報表內容（admin，累計）===")
t = login("admin")
_, data = get("/reports/sales-performance?period=all", t)
for row in data.get("items", []):
    print(
        f"  {row['username']:8s} 訂單 {row['order_count']:>3} | 件數 {row['qty']:>8} | "
        f"金額 {row['sales_amount']:>10} | 成本 {row['total_cost']:>10} | "
        f"毛利 {row['gross_margin']:>9} | 毛利率 {row['gross_margin_rate']}%"
    )
_, turn = get("/reports/inventory-turnover?period=all", t)
print(f"\n  庫存週轉率 {turn.get('turnover')}（銷貨成本 {turn.get('sold_cost')} / 庫存價值 {turn.get('stock_value')}）")

for period in ("week", "month", "quarter"):
    _, d = get(f"/reports/sales-performance?period={period}", t)
    print(f"  期間 {period:8s} → {len(d.get('items', []))} 位銷貨員")
