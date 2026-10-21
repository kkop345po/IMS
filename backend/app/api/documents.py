"""單據 API：採購單、銷售單、補貨建議（FR-17～FR-22）。"""
from __future__ import annotations

from datetime import date

from flask import Blueprint, g, jsonify, request
from decimal import Decimal
from sqlalchemy import select

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models.documents import PurchaseOrder, SalesOrder
from app.models.item import Item
from app.services import purchasing_service, sales_service, stock_service
from app.services.auth import require_capability

documents_bp = Blueprint("documents", __name__)


# ── 補貨建議（FR-17、FR-18）────────────────────────────────────
@documents_bp.get("/replenishment")
@require_capability("replenishment.view")
def replenishment():
    mode = request.args.get("mode", "purchase")
    if mode == "transfer":
        return jsonify({"items": purchasing_service.transfer_suggestions()})
    return jsonify({"items": purchasing_service.replenishment_suggestions()})


@documents_bp.post("/replenishment/to-purchase")
@require_capability("purchase.manage")
def replenishment_to_purchase():
    payload = request.get_json(silent=True) or {}
    lines = payload.get("lines") or []
    if not lines:
        raise ValidationError("請至少選擇一個品項")
    order = purchasing_service.create_order(
        supplier_id=payload.get("supplier_id"),
        created_by=g.current_user.id,
        expected_date=date.fromisoformat(payload["expected_date"]) if payload.get("expected_date") else None,
        lines=lines,
    )
    return jsonify({"id": order.id, "po_no": order.po_no, "status": order.status}), 201


# ── 採購單（FR-19、FR-8）───────────────────────────────────────
@documents_bp.get("/purchase-orders")
@require_capability("purchase.manage")
def list_purchase_orders():
    rows = db.session.execute(
        select(PurchaseOrder).order_by(PurchaseOrder.id.desc())
    ).scalars().all()
    return jsonify(
        {
            "items": [
                {
                    "id": o.id,
                    "po_no": o.po_no,
                    "supplier_id": o.supplier_id,
                    "status": o.status,
                    "total": o.total,
                    "expected_date": o.expected_date,
                    "lines": [
                        {
                            "id": l.id,
                            "item_id": l.item_id,
                            "qty": l.qty,
                            "unit_price": l.unit_price,
                            "received_qty": l.received_qty,
                        }
                        for l in o.lines
                    ],
                }
                for o in rows
            ]
        }
    )


@documents_bp.post("/purchase-orders")
@require_capability("purchase.manage")
def create_purchase_order():
    payload = request.get_json(silent=True) or {}
    order = purchasing_service.create_order(
        supplier_id=payload.get("supplier_id"),
        created_by=g.current_user.id,
        expected_date=date.fromisoformat(payload["expected_date"]) if payload.get("expected_date") else None,
        lines=payload.get("lines") or [],
    )
    return jsonify({"id": order.id, "po_no": order.po_no, "status": order.status}), 201


@documents_bp.post("/purchase-orders/<int:order_id>/send")
@require_capability("purchase.manage")
def send_purchase_order(order_id: int):
    order = purchasing_service.send_order(order_id)
    return jsonify({"id": order.id, "po_no": order.po_no, "status": order.status})


@documents_bp.post("/purchase-orders/<int:order_id>/receive")
@require_capability("stock.receive")
def receive_purchase_order(order_id: int):
    payload = request.get_json(silent=True) or {}
    line_id = payload.get("line_id")
    received_qty = payload.get("received_qty")
    if not line_id or received_qty is None:
        raise ValidationError("請提供 line_id 與 received_qty")

    order = db.session.get(PurchaseOrder, order_id)
    if order is None:
        raise NotFoundError("採購單不存在")
    line = next((l for l in order.lines if l.id == line_id), None)
    if line is None:
        raise NotFoundError("採購單明細不存在")

    # 差異原因必填（FR-8）
    diff = float(line.qty) - float(received_qty)
    if diff > 0 and not (payload.get("diff_reason") or "").strip():
        raise ValidationError("實收數量少於單據數量時，必須填寫差異原因")

    order = purchasing_service.receive_line(
        purchase_order_id=order_id,
        line_id=line_id,
        received_qty=received_qty,
        warehouse_id=payload.get("warehouse_id"),
        bin_id=payload.get("bin_id"),
        operator_id=g.current_user.id,
        lot_code=payload.get("lot_code"),
        expiry_date=date.fromisoformat(payload["expiry_date"]) if payload.get("expiry_date") else None,
    )
    return jsonify({"id": order.id, "po_no": order.po_no, "status": order.status})


# ── 銷售單（FR-20～FR-23）──────────────────────────────────────
@documents_bp.post("/sales-orders/preview")
@require_capability("sales.manage")
def preview_sales_order():
    """試算：可用量、應收金額、毛利（FR-20）。

    毛利與可用量一律由後端計算（AD-9），前端不自行推算。
    """
    payload = request.get_json(silent=True) or {}
    lines = payload.get("lines") or []

    preview_lines = []
    total = Decimal("0")
    total_cost = Decimal("0")
    for line in lines:
        item = db.session.get(Item, line.get("item_id"))
        if item is None:
            continue
        qty = Decimal(str(line.get("qty") or 0))
        unit_price = Decimal(str(line.get("unit_price") or item.default_selling_price))
        d_type = line.get("discount_type")
        d_value = line.get("discount_value")
        gross = qty * unit_price
        if d_type == "percent" and d_value:
            gross = gross * (Decimal("1") - Decimal(str(d_value)) / Decimal("100"))
        elif d_type == "fixed" and d_value:
            gross = gross - Decimal(str(d_value))
        gross = max(gross, Decimal("0"))

        cost = stock_service.current_cost(item.id)
        available = stock_service.available(item.id, line.get("warehouse_id"))
        line_cost = qty * cost
        margin = gross - line_cost

        total += gross
        total_cost += line_cost
        preview_lines.append(
            {
                "item_id": item.id,
                "item_code": item.code,
                "item_name": item.name,
                "available": str(available),
                "unit_price": str(unit_price),
                "unit_cost": str(cost),
                "qty": str(qty),
                "amount": str(gross),
                "line_cost": str(line_cost),
                "gross_margin": str(margin),
                "insufficient": available < qty,
            }
        )

    rate = (total - total_cost) / total * 100 if total > 0 else Decimal("0")
    return jsonify(
        {
            "lines": preview_lines,
            "total": str(total),
            "total_cost": str(total_cost),
            "gross_margin": str(total - total_cost),
            "gross_margin_rate": str(rate.quantize(Decimal("0.01"))),
        }
    )


@documents_bp.get("/sales-orders")
@require_capability("sales.manage")
def list_sales_orders():
    rows = db.session.execute(
        select(SalesOrder).order_by(SalesOrder.id.desc())
    ).scalars().all()
    return jsonify(
        {
            "items": [
                {
                    "id": o.id,
                    "so_no": o.so_no,
                    "customer_name": o.customer_name,
                    "salesperson_id": o.salesperson_id,
                    "status": o.status,
                    "total": o.total,
                    "total_cost": o.total_cost,
                    "gross_margin": (o.total or 0) - (o.total_cost or 0),
                    "created_at": o.created_at,
                    "shipped_at": o.shipped_at,
                    "lines": [
                        {
                            "id": l.id,
                            "item_id": l.item_id,
                            "qty": l.qty,
                            "unit_price": l.unit_price,
                            "line_total": l.line_total,
                            "unit_cost_snapshot": l.unit_cost_snapshot,
                        }
                        for l in o.lines
                    ],
                }
                for o in rows
            ]
        }
    )


@documents_bp.post("/sales-orders")
@require_capability("sales.manage")
def create_sales_order():
    payload = request.get_json(silent=True) or {}
    order = sales_service.create_order(
        salesperson_id=g.current_user.id,
        customer_name=payload.get("customer_name"),
        lines=payload.get("lines") or [],
        discount_type=payload.get("discount_type"),
        discount_value=payload.get("discount_value"),
    )
    return jsonify({"id": order.id, "so_no": order.so_no, "status": order.status}), 201


@documents_bp.post("/sales-orders/<int:order_id>/send")
@require_capability("sales.manage")
def send_sales_order(order_id: int):
    order = sales_service.send_order(order_id)
    return jsonify({"id": order.id, "so_no": order.so_no, "status": order.status})


@documents_bp.post("/sales-orders/<int:order_id>/ship")
@require_capability("sales.manage")
def ship_sales_order(order_id: int):
    order = sales_service.ship_order(order_id, g.current_user.id)
    return jsonify(
        {
            "id": order.id,
            "so_no": order.so_no,
            "status": order.status,
            "total": order.total,
            "total_cost": order.total_cost,
            "gross_margin": (order.total or 0) - (order.total_cost or 0),
        }
    )


@documents_bp.post("/sales-orders/<int:order_id>/cancel")
@require_capability("sales.manage")
def cancel_sales_order(order_id: int):
    order = sales_service.cancel_order(order_id)
    return jsonify({"id": order.id, "so_no": order.so_no, "status": order.status})
