"""調撥單（FR-12、FR-18）。

流程：draft → in_transit → received
調出後貨物在途，不計入任一倉庫的可用數量（AD-3）。
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.errors import InvalidStateTransition, NotFoundError, ValidationError
from app.extensions import db
from app.models.documents import Transfer
from app.models.item import Item
from app.services import stock_service
from app.services.stock_service import transaction


def _dec(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _next_no() -> str:
    count = db.session.execute(select(func.count(Transfer.id))).scalar_one()
    return f"TO-{count + 1:06d}"


def create_transfer(
    *,
    item_id: int,
    from_warehouse_id: int,
    from_bin_id: int | None,
    to_warehouse_id: int,
    to_bin_id: int | None,
    qty,
    created_by: int | None,
) -> Transfer:
    qty = _dec(qty)
    if qty <= 0:
        raise ValidationError("調撥數量必須大於 0")
    if from_warehouse_id == to_warehouse_id:
        raise ValidationError("來源與目標倉庫不可相同")

    with transaction():
        item = db.session.get(Item, item_id)
        if item is None:
            raise NotFoundError("商品不存在")
        # 確認來源倉有足夠可用量（AD-3）
        available = stock_service.available(item_id, from_warehouse_id)
        if available < qty:
            from app.errors import OutOfStock

            raise OutOfStock(
                "來源倉可用庫存不足",
                {"item_id": item_id, "available": str(available), "required": str(qty)},
            )
        transfer = Transfer(
            transfer_no=_next_no(),
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            from_bin_id=from_bin_id,
            to_bin_id=to_bin_id,
            item_id=item_id,
            qty=qty,
            status="draft",
            created_by=created_by,
        )
        db.session.add(transfer)
        db.session.flush()
        return transfer


def _default_bin(warehouse_id: int) -> int | None:
    """目標倉未指定儲位時，挑第一個可用儲位（庫存必須落在儲位上）。"""
    from app.models.location import Bin, Rack, Zone

    row = db.session.execute(
        select(Bin.id)
        .join(Rack, Rack.id == Bin.rack_id)
        .join(Zone, Zone.id == Rack.zone_id)
        .where(Zone.warehouse_id == warehouse_id, Bin.is_active.is_(True))
        .order_by(Bin.id)
    ).scalars().first()
    return row


def execute_out(transfer_id: int, operator_id: int | None) -> Transfer:
    """調出：貨物離開來源倉，進入在途。"""
    with transaction():
        transfer = db.session.get(Transfer, transfer_id)
        if transfer is None:
            raise NotFoundError("調撥單不存在")
        if transfer.status != "draft":
            raise InvalidStateTransition(f"只有草稿可調出，目前狀態：{transfer.status}")
        # AD-11：批次由後端挑選並記錄，調入時才知道要放回哪個批次
        level = stock_service.pick_level(
            item_id=transfer.item_id,
            warehouse_id=transfer.from_warehouse_id,
            qty=_dec(transfer.qty),
            bin_id=transfer.from_bin_id,
        )
        transfer.batch_id = level.batch_id
        stock_service.transfer_out(
            item_id=transfer.item_id,
            from_warehouse_id=transfer.from_warehouse_id,
            from_bin_id=level.bin_id,
            batch_id=level.batch_id,
            qty=_dec(transfer.qty),
            operator_id=operator_id,
            source_doc_id=transfer.transfer_no,
        )
        transfer.status = "in_transit"
        db.session.flush()
        return transfer


def execute_in(transfer_id: int, operator_id: int | None) -> Transfer:
    """調入：才計入目標倉。"""
    with transaction():
        transfer = db.session.get(Transfer, transfer_id)
        if transfer is None:
            raise NotFoundError("調撥單不存在")
        if transfer.status != "in_transit":
            raise InvalidStateTransition(f"只有在庫中的單可調入，目前狀態：{transfer.status}")
        to_bin = transfer.to_bin_id or _default_bin(transfer.to_warehouse_id)
        if to_bin is None:
            raise ValidationError("目標倉庫沒有可用儲位，請先建立儲位")
        stock_service.transfer_in(
            item_id=transfer.item_id,
            to_warehouse_id=transfer.to_warehouse_id,
            to_bin_id=to_bin,
            batch_id=transfer.batch_id,
            qty=_dec(transfer.qty),
            operator_id=operator_id,
            source_doc_id=transfer.transfer_no,
        )
        transfer.to_bin_id = to_bin
        transfer.status = "received"
        transfer.received_at = datetime.now(timezone.utc)
        db.session.flush()
        return transfer
