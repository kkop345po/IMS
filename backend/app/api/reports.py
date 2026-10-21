"""報表 API：銷貨員業績、庫存週轉率（FR-24）。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from app.extensions import db
from app.models.documents import SalesOrder, SalesOrderLine
from app.models.item import Item
from app.models.stock import ItemCost, StockLevel
from app.models.user import User
from app.services.auth import require_capability

reports_bp = Blueprint("reports", __name__)

PERIODS = {
    "week": 7,
    "month": 30,
    "quarter": 90,
    "all": None,
}


def _period_start(period: str):
    days = PERIODS.get(period, 30)
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


@reports_bp.get("/reports/sales-performance")
@require_capability("report.view")
def sales_performance():
    """銷貨員業績：銷售金額／成交件數／訂單數／毛利金額／毛利率（FR-24）。"""
    period = request.args.get("period", "month")
    start = _period_start(period)
    period_filter = [SalesOrder.shipped_at >= start] if start else []

    # 訂單層級彙總與明細層級彙總分開算，
    # 否則 join 明細會讓「銷售金額」被重複累加（每個品項列一次）
    order_agg = (
        select(
            SalesOrder.salesperson_id.label("sid"),
            func.count(func.distinct(SalesOrder.id)).label("order_count"),
            func.coalesce(func.sum(SalesOrder.total), 0).label("total"),
            func.coalesce(func.sum(SalesOrder.total_cost), 0).label("total_cost"),
        )
        .where(SalesOrder.status == "shipped", *period_filter)
        .group_by(SalesOrder.salesperson_id)
        .subquery()
    )
    qty_agg = (
        select(
            SalesOrder.salesperson_id.label("sid"),
            func.coalesce(func.sum(SalesOrderLine.qty), 0).label("qty"),
        )
        .join(SalesOrderLine, SalesOrderLine.sales_order_id == SalesOrder.id)
        .where(SalesOrder.status == "shipped", *period_filter)
        .group_by(SalesOrder.salesperson_id)
        .subquery()
    )

    rows = db.session.execute(
        select(
            User.id,
            User.username,
            order_agg.c.order_count,
            order_agg.c.total,
            order_agg.c.total_cost,
            qty_agg.c.qty,
        )
        .join(order_agg, order_agg.c.sid == User.id)
        .outerjoin(qty_agg, qty_agg.c.sid == User.id)
        .order_by(User.username)
    ).all()

    items = []
    for uid, username, order_count, total, total_cost, qty in rows:
        total = Decimal(total)
        total_cost = Decimal(total_cost)
        margin = total - total_cost
        rate = (margin / total * 100) if total > 0 else Decimal("0")
        items.append(
            {
                "salesperson_id": uid,
                "username": username,
                "order_count": order_count,
                "qty": qty,
                "sales_amount": total,
                "total_cost": total_cost,
                "gross_margin": margin,
                "gross_margin_rate": rate.quantize(Decimal("0.01")),
            }
        )
    return jsonify({"period": period, "items": items})


@reports_bp.get("/reports/inventory-turnover")
@require_capability("report.view")
def inventory_turnover():
    """庫存週轉率 = 期間銷貨成本 ÷ 期間平均庫存價值。"""
    period = request.args.get("period", "month")
    start = _period_start(period)

    sold_cost = Decimal(
        db.session.execute(
            select(func.coalesce(func.sum(SalesOrder.total_cost), 0)).where(
                SalesOrder.status == "shipped",
                *([SalesOrder.shipped_at >= start] if start else []),
            )
        ).scalar_one()
    )
    stock_value = Decimal(
        db.session.execute(
            select(
                func.coalesce(
                    func.sum(StockLevel.on_hand * ItemCost.moving_avg_cost), 0
                )
            )
            .select_from(StockLevel)
            .join(ItemCost, ItemCost.item_id == StockLevel.item_id)
        ).scalar_one()
    )
    turnover = (sold_cost / stock_value) if stock_value > 0 else Decimal("0")
    return jsonify(
        {
            "period": period,
            "sold_cost": sold_cost,
            "stock_value": stock_value,
            "turnover": turnover.quantize(Decimal("0.01")),
        }
    )
