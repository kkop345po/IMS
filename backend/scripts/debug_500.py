# -*- coding: utf-8 -*-
"""用 test client 取得 500 的真實 traceback。"""
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("FLASK_APP", "wsgi:app")

from app import create_app

app = create_app()
app.config["TESTING"] = False  # 讓錯誤 handler 生效，但 logger 會印 traceback

with app.test_client() as c:
    c.post("/api/auth/login", json={"username": "admin", "password": "Passw0rd!"})
    for path in ("/api/purchase-orders", "/api/sales-orders"):
        print("=" * 60)
        print("GET", path)
        r = c.get(path)
        print("status:", r.status_code)
        if r.status_code != 200:
            print(r.get_data(as_text=True)[:300])
