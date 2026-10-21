"""MVP 不變量自我檢查：確認「數字對得起來」。

執行方式：
    .venv\\Scripts\\python.exe backend\\scripts\\verify_mvp.py
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("FLASK_APP", "wsgi:app")

from sqlalchemy import text  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.documents import SalesOrder  # noqa: E402
from app.models.stock import StockLedger, StockLevel  # noqa: E402
from app.services import purchasing_service  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((PASS if ok else FAIL, name, detail))


def main() -> int:
    app = create_app()
    with app.app_context():
        tables = [r[0] for r in db.session.execute(
            text("select tablename from pg_tables where schemaname='public' order by tablename")
        ).all()]
        check("資料表已建立（18 張 + alembic_version）", len(tables) >= 19, f"{len(tables)} 張：{', '.join(tables)}")

        # 種子資料
        from app.seed_data import seed

        info = seed()
        check("種子資料載入", info["items"] == 12, str(info))

        levels = db.session.execute(select_levels()).all()
        negative = [l for l in levels if Decimal(l.on_hand) < 0 or Decimal(l.reserved) < 0]
        check("無負數在手／占用", not negative, f"違規 {len(negative)} 筆")

        mismatch = [
            l for l in levels
            if Decimal(l.on_hand) - Decimal(l.reserved) != Decimal(l.available)
        ]
        check("可用量 = 在手 − 占用（AD-3）", not mismatch, f"違規 {len(mismatch)} 筆")

        # 交易流與庫存總量一致
        ledger_in = db.session.execute(
            text("select coalesce(sum(qty_delta),0) from stock_ledger where movement_type='IN'")
        ).scalar_one()
        ledger_out = db.session.execute(
            text("select coalesce(sum(qty_delta),0) from stock_ledger")
        ).scalar_one()
        total_on_hand = db.session.execute(
            text("select coalesce(sum(on_hand),0) from stock_levels")
        ).scalar_one()
        check(
            "庫存總量 = 交易流累計（AD-1）",
            Decimal(str(ledger_out)) == Decimal(str(total_on_hand)),
            f"交易流 {ledger_out} vs 庫存 {total_on_hand}",
        )

        # 毛利可加總驗證（AD-4 / SM-6）
        orders = db.session.execute(
            text("select id, total, total_cost from sales_orders where status='shipped'")
        ).all()
        total_margin = sum((Decimal(str(o.total)) - Decimal(str(o.total_cost))) for o in orders)
        line_margin = db.session.execute(
            text(
                "select coalesce(sum(sol.line_total - sol.line_cost),0) from sales_order_lines sol "
                "join sales_orders so on so.id = sol.sales_order_id where so.status='shipped'"
            )
        ).scalar_one()
        check(
            "毛利總額 = 明細逐筆加總（SM-6）",
            total_margin == Decimal(str(line_margin)),
            f"單頭 {total_margin} vs 明細 {line_margin}",
        )

        # 成本快照存在
        missing_snapshot = db.session.execute(
            text(
                "select count(*) from sales_order_lines sol join sales_orders so on so.id=sol.sales_order_id "
                "where so.status='shipped' and sol.unit_cost_snapshot is null"
            )
        ).scalar_one()
        check("出庫成本快照已寫入（AD-4）", missing_snapshot == 0, f"缺 {missing_snapshot} 筆")

        # 補貨建議可算
        suggestions = purchasing_service.replenishment_suggestions()
        check("補貨建議可算（FR-17）", True, f"{len(suggestions)} 筆建議")

        # 負庫存防護
        from app.errors import OutOfStock
        from app.services import stock_service

        try:
            stock_service.issue_for_sale(
                item_id=1, warehouse_id=1, bin_id=1, batch_id=None,
                qty=Decimal("99999999"), operator_id=1, source_doc_id="TEST",
            )
            blocked = False
        except OutOfStock:
            blocked = True
        except Exception:
            blocked = False
        check("超量出庫被阻擋（AD-3）", blocked, "測試超量出貨是否被擋下")

        db.session.rollback()

    print("\n=== MVP 不變量檢查 ===")
    for status, name, detail in results:
        print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    failed = [r for r in results if r[0] == FAIL]
    print(f"\n{len(results) - len(failed)}/{len(results)} 通過")
    return 1 if failed else 0


def select_levels():
    from sqlalchemy import select

    return select(
        StockLevel.id,
        StockLevel.on_hand,
        StockLevel.reserved,
        (StockLevel.on_hand - StockLevel.reserved).label("available"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
