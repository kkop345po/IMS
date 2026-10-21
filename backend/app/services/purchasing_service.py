"""採購與補貨建議（FR-16、FR-17、FR-18、FR-19）。"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models.documents import PurchaseOrder, PurchaseOrderLine
from app.models.item import Item
from app.models.stock import StockLevel
from app.services import stock_service
from app.services.stock_service import transaction


def _dec(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _next_po_no() -> str:
    count = db.session.execute(select(PurchaseOrder.id)).scalars().all()
    return f"PO-{len(count) + 1:06d}"


def create_order(
    *, supplier_id: int, created_by: int, expected_date: date | None, lines: list[dict]
) -> PurchaseOrder:
    """lines: [{item_id, qty, unit_price}]"""
    if not lines:
        raise ValidationError("採購單至少要有一個品項")
    with transaction():
        order = PurchaseOrder(
            po_no=_next_po_no(),
            supplier_id=supplier_id,
            status="draft",
            expected_date=expected_date,
            created_by=created_by,
        )
        db.session.add(order)
        db.session.flush()
        for line in lines:
            item = db.session.get(Item, line["item_id"])
            if item is None:
                raise NotFoundError(f"商品 {line['item_id']} 不存在")
            qty = _dec(line["qty"])
            unit_price = _dec(line.get("unit_price", item.default_purchase_price))
            db.session.add(
                PurchaseOrderLine(
                    purchase_order_id=order.id,
                    item_id=item.id,
                    qty=qty,
                    unit_price=unit_price,
                )
            )
        db.session.flush()
        order.total = sum(
            (_dec(l.qty) * _dec(l.unit_price) for l in order.lines), Decimal("0")
        )
        db.session.flush()
        return order


def send_order(order_id: int) -> PurchaseOrder:
    with transaction():
        order = db.session.get(PurchaseOrder, order_id)
        if order is None:
            raise NotFoundError("採購單不存在")
        if order.status != "draft":
            raise ValidationError(f"只有草稿可送出，目前狀態：{order.status}")
        order.status = "sent"
        db.session.flush()
        return order


def receive_line(
    *,
    purchase_order_id: int,
    line_id: int,
    received_qty,
    warehouse_id: int,
    bin_id: int,
    operator_id: int,
    lot_code: str | None = None,
    expiry_date: date | None = None,
) -> PurchaseOrder:
    """收貨入庫（FR-8）。差異保留為未收貨數量，差異原因由呼叫端驗證。"""
    received_qty = _dec(received_qty)
    with transaction():
        order = db.session.get(PurchaseOrder, purchase_order_id)
        if order is None:
            raise NotFoundError("採購單不存在")
        line = db.session.get(PurchaseOrderLine, line_id)
        if line is None or line.purchase_order_id != order.id:
            raise NotFoundError("採購單明細不存在")
        if order.status not in ("sent", "partially_received"):
            raise ValidationError(f"目前狀態不可收貨：{order.status}")

        stock_service.receive(
            item_id=line.item_id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
            qty=received_qty,
            unit_cost=_dec(line.unit_price),
            operator_id=operator_id,
            source_doc_type="PO",
            source_doc_id=order.po_no,
            lot_code=lot_code,
            expiry_date=expiry_date,
            supplier_id=order.supplier_id,
        )

        line.received_qty = _dec(line.received_qty) + received_qty
        line.received_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        if line.lot_code is None and lot_code:
            line.lot_code = lot_code
        if line.expiry_date is None and expiry_date:
            line.expiry_date = expiry_date

        all_received = all(_dec(l.received_qty) >= _dec(l.qty) for l in order.lines)
        order.status = "received" if all_received else "partially_received"
        db.session.flush()
        return order


def replenishment_suggestions() -> list[dict]:
    """補貨建議（FR-17）：可用量 < 安全水位最低值 → 建議補至最高水位。"""
    rows = db.session.execute(
        select(
            Item.id,
            Item.code,
            Item.name,
            Item.min_stock,
            Item.max_stock,
            Item.default_purchase_price,
            Item.supplier_id,
            func.coalesce(func.sum(StockLevel.on_hand - StockLevel.reserved), 0).label("available"),
        )
        .outerjoin(StockLevel, StockLevel.item_id == Item.id)
        .where(Item.is_active.is_(True))
        .group_by(Item.id)
    ).all()

    suggestions = []
    for row in rows:
        available = _dec(row.available)
        min_stock = _dec(row.min_stock)
        max_stock = _dec(row.max_stock)
        if min_stock <= 0 or available >= min_stock:
            continue
        suggest_qty = max(max_stock - available, Decimal("0"))
        suggestions.append(
            {
                "item_id": row.id,
                "code": row.code,
                "name": row.name,
                "available": str(available),
                "min_stock": str(min_stock),
                "max_stock": str(max_stock),
                "suggest_qty": str(suggest_qty),
                "supplier_id": row.supplier_id,
                "unit_price": str(_dec(row.default_purchase_price)),
                "estimated_total": str((suggest_qty * _dec(row.default_purchase_price)).quantize(Decimal("0.01"))),
            }
        )
    return suggestions


def transfer_suggestions() -> list[dict]:
    """跨倉調撥建議（FR-18）：本倉不足但他倉有貨。"""
    suggestions = []
    for s in replenishment_suggestions():
        other = db.session.execute(
            select(
                StockLevel.warehouse_id,
                func.coalesce(func.sum(StockLevel.on_hand - StockLevel.reserved), 0),
            )
            .where(StockLevel.item_id == s["item_id"])
            .group_by(StockLevel.warehouse_id)
        ).all()
        for warehouse_id, qty in other:
            qty = _dec(qty)
            if qty <= 0:
                continue
            suggestions.append(
                {
                    "item_id": s["item_id"],
                    "code": s["code"],
                    "name": s["name"],
                    "from_warehouse_id": warehouse_id,
                    "transferable_qty": str(qty),
                    "suggest_qty": s["suggest_qty"],
                }
            )
    return suggestions
