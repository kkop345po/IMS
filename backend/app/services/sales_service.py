"""銷售流程（FR-20～FR-23、FR-24）。

規則：
- 送出訂單 → 建立占用（FR-23）
- 出貨 → 釋放占用 + 扣在手 + 寫成本快照（AD-3、AD-4）
- 一個 use case = 一個交易（AD-2）：包住庫存動作的是這裡，不是 route
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.errors import InvalidStateTransition, NotFoundError, ValidationError
from app.extensions import db
from app.models.documents import SalesOrder, SalesOrderLine
from app.models.item import Item
from app.services import stock_service
from app.services.stock_service import transaction


def _dec(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _next_so_no() -> str:
    count = db.session.execute(select(SalesOrder.id)).scalars().all()
    return f"SO-{len(count) + 1:06d}"


def _line_total(qty: Decimal, unit_price: Decimal, discount_type, discount_value) -> Decimal:
    gross = qty * unit_price
    if discount_type == "percent" and discount_value:
        gross = gross * (Decimal("1") - _dec(discount_value) / Decimal("100"))
    elif discount_type == "fixed" and discount_value:
        gross = gross - _dec(discount_value)
    return max(gross, Decimal("0"))


def create_order(
    *,
    salesperson_id: int,
    customer_name: str | None,
    lines: list[dict],
    discount_type: str | None = None,
    discount_value=None,
) -> SalesOrder:
    """建立銷售單（草稿）。lines: [{item_id, warehouse_id, bin_id?, qty, unit_price, discount_type?, discount_value?}]"""
    if not lines:
        raise ValidationError("銷售單至少要有一個品項")
    with transaction():
        order = SalesOrder(
            so_no=_next_so_no(),
            customer_name=customer_name,
            salesperson_id=salesperson_id,
            status="draft",
            discount_type=discount_type,
            discount_value=_dec(discount_value) if discount_value else None,
        )
        db.session.add(order)
        db.session.flush()
        for line in lines:
            item = db.session.get(Item, line["item_id"])
            if item is None:
                raise NotFoundError(f"商品 {line['item_id']} 不存在")
            qty = _dec(line["qty"])
            unit_price = _dec(line.get("unit_price", item.default_selling_price))
            d_type = line.get("discount_type", discount_type)
            d_value = line.get("discount_value", discount_value)
            total = _line_total(qty, unit_price, d_type, d_value)
            # AD-11：未指定儲位／批次時，由後端挑出實際要出貨的庫存列並回寫
            level = stock_service.pick_level(
                item_id=item.id,
                warehouse_id=line["warehouse_id"],
                qty=qty,
                bin_id=line.get("bin_id"),
                batch_id=line.get("batch_id"),
            )
            db.session.add(
                SalesOrderLine(
                    sales_order_id=order.id,
                    item_id=item.id,
                    warehouse_id=line["warehouse_id"],
                    bin_id=level.bin_id,
                    batch_id=level.batch_id,
                    qty=qty,
                    unit_price=unit_price,
                    discount_type=d_type,
                    discount_value=_dec(d_value) if d_value else None,
                    line_total=total,
                )
            )
        db.session.flush()
        _recalc_total(order)
        return order


def send_order(order_id: int) -> SalesOrder:
    """送出：建立占用（FR-23）。草稿不算業績。"""
    with transaction():
        order = db.session.get(SalesOrder, order_id)
        if order is None:
            raise NotFoundError("銷售單不存在")
        if order.status != "draft":
            raise InvalidStateTransition(f"只有草稿可送出，目前狀態：{order.status}")
        for line in order.lines:
            stock_service.reserve(
                item_id=line.item_id,
                warehouse_id=line.warehouse_id,
                bin_id=line.bin_id,
                batch_id=line.batch_id,
                qty=_dec(line.qty),
                source_doc_type="SO",
                source_doc_id=order.so_no,
            )
        order.status = "sent"
        db.session.flush()
        return order


def ship_order(order_id: int, operator_id: int, shipped_at=None) -> SalesOrder:
    """出貨：扣庫存 + 寫成本快照 + 累計毛利（FR-22）。"""
    with transaction():
        order = db.session.get(SalesOrder, order_id)
        if order is None:
            raise NotFoundError("銷售單不存在")
        if order.status != "sent":
            raise InvalidStateTransition(f"只有已送出的單可出貨，目前狀態：{order.status}")

        total_cost = Decimal("0")
        for line in order.lines:
            snapshot = stock_service.issue_for_sale(
                item_id=line.item_id,
                warehouse_id=line.warehouse_id,
                bin_id=line.bin_id,
                batch_id=line.batch_id,
                qty=_dec(line.qty),
                operator_id=operator_id,
                source_doc_id=order.so_no,
                occurred_at=shipped_at,
            )
            line.unit_cost_snapshot = snapshot  # AD-4
            line.line_cost = snapshot * _dec(line.qty)
            total_cost += line.line_cost

        order.total_cost = total_cost
        order.total = sum((_dec(l.line_total) for l in order.lines), Decimal("0"))
        order.status = "shipped"
        order.shipped_at = shipped_at or datetime.now(timezone.utc)
        db.session.flush()
        return order


def cancel_order(order_id: int) -> SalesOrder:
    """取消未出貨的單：釋放占用（FR-23）。"""
    with transaction():
        order = db.session.get(SalesOrder, order_id)
        if order is None:
            raise NotFoundError("銷售單不存在")
        if order.status != "sent":
            raise InvalidStateTransition(f"只有已送出且未出貨的單可取消，目前狀態：{order.status}")
        for line in order.lines:
            stock_service.release_reserved(
                item_id=line.item_id,
                warehouse_id=line.warehouse_id,
                bin_id=line.bin_id,
                batch_id=line.batch_id,
                qty=_dec(line.qty),
            )
        order.status = "cancelled"
        db.session.flush()
        return order


def _recalc_total(order: SalesOrder) -> None:
    order.total = sum((_dec(l.line_total) for l in order.lines), Decimal("0"))
    db.session.flush()
