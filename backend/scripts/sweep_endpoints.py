# -*- coding: utf-8 -*-
"""巡檢所有 GET 端點，列出狀態與筆數。"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5000/api"


def call(method, path, body=None, token=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Cookie", "session=" + token)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8")), r.headers.get("Set-Cookie")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw), None
        except json.JSONDecodeError:
            return e.code, {"raw": raw[:300]}, None


def main():
    tokens = {}
    for u in ("admin", "warehouse", "purchasing", "sales", "accounting", "manager", "viewer"):
        s, b, c = call("POST", "/auth/login", {"username": u, "password": "Passw0rd!"})
        tokens[u] = c.split("session=")[1].split(";")[0] if c else None

    t = tokens["admin"]
    paths = [
        "/items",
        "/items?q=%E9%A3%B2%E6%96%99",
        "/suppliers",
        "/warehouses",
        "/bins",
        "/stock",
        "/stock?low_only=1",
        "/stock/ledger",
        "/purchase-orders",
        "/sales-orders",
        "/transfers",
        "/replenishment?mode=purchase",
        "/replenishment?mode=transfer",
        "/reports/sales-performance?period=all",
        "/reports/inventory-turnover?period=all",
        "/users",
    ]
    print("=== GET 端點巡檢（admin）===")
    for p in paths:
        s, b, _ = call("GET", p, token=t)
        if isinstance(b, dict):
            n = len(b.get("items", b.get("users", [])))
        else:
            n = 0
        flag = "OK " if s == 200 else "ERR"
        detail = "" if s == 200 else json.dumps(b, ensure_ascii=False)[:200]
        print(f"[{flag}] {s} {p:45s} items={n} {detail}")

    print("\n=== 角色權限矩陣抽查（應該被擋的會是 403）===")
    checks = [
        ("viewer", "/reports/sales-performance?period=all", 200),
        ("sales", "/reports/sales-performance?period=all", 403),
        ("sales", "/purchase-orders", 403),
        ("warehouse", "/purchase-orders", 403),
        ("warehouse", "/stock", 200),
        ("purchasing", "/replenishment?mode=purchase", 200),
        ("purchasing", "/sales-orders", 403),
        ("accounting", "/stock", 200),
    ]
    for user, path, expect in checks:
        s, b, _ = call("GET", path, token=tokens[user])
        mark = "OK " if s == expect else "!! "
        print(f"[{mark}] {user:11s} {path:40s} got={s} expect={expect}")


if __name__ == "__main__":
    main()
