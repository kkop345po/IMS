"""庫存 API：庫存現況、交易流、調撥（FR-7、FR-12）。"""
from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func, select

from app.extensions import db
from app.models.documents import Transfer
from app.models.item import Item
from app.models.location import Bin, Warehouse
from app.models.stock import StockLedger, StockLevel
from app.services import stock_service, transfer_service
from app.services.auth import require_capability

stock_bp = Blueprint("stock", __name__)


@stock_bp.get("/stock")
@require_capability("stock.view")
def list_stock():
    """庫存現況：在手／占用／可用（AD-3，只由後端算）。"""
    page = max(int(request.args.get("page", 1)), 1)
    size = min(max(int(request.args.get("size", 50)), 1), 100)
    item_id = request.args.get("item_id", type=int)
    warehouse_id = request.args.get("warehouse_id", type=int)
    low_only = request.args.get("low_only") in ("1", "true", "True")

    stmt = (
        select(
            StockLevel,
            Item.code,
            Item.name,
            Item.min_stock,
            Item.max_stock,
            Warehouse.code,
        )
        .join(Item, Item.id == StockLevel.item_id)
        .join(Warehouse, Warehouse.id == StockLevel.warehouse_id)
    )
    if item_id:
        stmt = stmt.where(StockLevel.item_id == item_id)
    if warehouse_id:
        stmt = stmt.where(StockLevel.warehouse_id == warehouse_id)

    rows = db.session.execute(stmt).all()
    payload = []
    for level, item_code, item_name, min_stock, max_stock, wh_code in rows:
        available = Decimal(level.on_hand) - Decimal(level.reserved)
        is_low = Decimal(min_stock) > 0 and available < Decimal(min_stock)
        if low_only and not is_low:
            continue
        payload.append(
            {
                "item_id": level.item_id,
                "item_code": item_code,
                "item_name": item_name,
                "warehouse_id": level.warehouse_id,
                "warehouse_code": wh_code,
                "bin_id": level.bin_id,
                "on_hand": level.on_hand,
                "reserved": level.reserved,
                "available": available,
                "min_stock": min_stock,
                "max_stock": max_stock,
                "is_low": is_low,
            }
        )
    total = len(payload)
    start = (page - 1) * size
    return jsonify(
        {"total": total, "page": page, "size": size, "items": payload[start : start + size]}
    )


@stock_bp.get("/stock/ledger")
@require_capability("stock.view")
def list_ledger():
    """庫存交易流（AD-5：append-only，只能查）。"""
    page = max(int(request.args.get("page", 1)), 1)
    size = min(max(int(request.args.get("size", 50)), 1), 100)
    item_id = request.args.get("item_id", type=int)

    stmt = select(StockLedger).order_by(StockLedger.id.desc())
    if item_id:
        stmt = stmt.where(StockLedger.item_id == item_id)
    total = db.session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()
    rows = db.session.execute(stmt.offset((page - 1) * size).limit(size)).scalars().all()

    return jsonify(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [
                {
                    "id": r.id,
                    "item_id": r.item_id,
                    "warehouse_id": r.warehouse_id,
                    "qty_delta": r.qty_delta,
                    "movement_type": r.movement_type,
                    "source_doc_type": r.source_doc_type,
                    "source_doc_id": r.source_doc_id,
                    "reason_code": r.reason_code,
                    "operator_id": r.operator_id,
                    "created_at": r.created_at,
                }
                for r in rows
            ],
        }
    )


@stock_bp.get("/transfers")
@require_capability("stock.view")
def list_transfers():
    rows = db.session.execute(select(Transfer).order_by(Transfer.id.desc())).scalars().all()
    item_rows = db.session.execute(select(Item.id, Item.code, Item.name)).all()
    item_codes = {r[0]: r[1] for r in item_rows}
    item_names = {r[0]: r[2] for r in item_rows}
    return jsonify(
        {
            "items": [
                {
                    "id": t.id,
                    "transfer_no": t.transfer_no,
                    "item_id": t.item_id,
                    "item_code": item_codes.get(t.item_id),
                    "item_name": item_names.get(t.item_id),
                    "from_warehouse_id": t.from_warehouse_id,
                    "to_warehouse_id": t.to_warehouse_id,
                    "qty": t.qty,
                    "status": t.status,
                    "created_at": t.created_at,
                }
                for t in rows
            ]
        }
    )


@stock_bp.post("/transfers")
@require_capability("transfer.create")
def create_transfer():
    """建立調撥單（草稿）。"""
    payload = request.get_json(silent=True) or {}
    transfer = transfer_service.create_transfer(
        item_id=payload.get("item_id"),
        from_warehouse_id=payload.get("from_warehouse_id"),
        from_bin_id=payload.get("from_bin_id"),
        to_warehouse_id=payload.get("to_warehouse_id"),
        to_bin_id=payload.get("to_bin_id"),
        qty=payload.get("qty"),
        created_by=g.current_user.id,
    )
    return jsonify({"id": transfer.id, "transfer_no": transfer.transfer_no, "status": transfer.status}), 201


@stock_bp.post("/transfers/<int:transfer_id>/out")
@require_capability("transfer.execute")
def execute_transfer_out(transfer_id: int):
    """調出：貨物進入在途，不計入任一倉可用量。"""
    transfer = transfer_service.execute_out(transfer_id, g.current_user.id)
    return jsonify({"id": transfer.id, "transfer_no": transfer.transfer_no, "status": transfer.status})


@stock_bp.post("/transfers/<int:transfer_id>/receive")
@require_capability("transfer.execute")
def execute_transfer_in(transfer_id: int):
    """調入：計入目標倉。"""
    transfer = transfer_service.execute_in(transfer_id, g.current_user.id)
    return jsonify({"id": transfer.id, "transfer_no": transfer.transfer_no, "status": transfer.status})
