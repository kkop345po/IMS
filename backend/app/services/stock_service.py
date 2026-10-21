"""StockService —— 庫存數字的唯一寫入口（AD-1、AD-2、AD-3、AD-4）。

所有會改變 stock_levels / stock_ledger / item_costs 的動作都必須走這裡；
其他模組不得直接寫這三張表。

交易邊界：一個公開方法 = 一個交易（AD-2）。transaction() 支援巢狀，
只有最外層才 commit，因此外層服務可以包住多個庫存動作仍維持單一交易。
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select, update

from app.errors import NotFoundError, OutOfStock, ValidationError
from app.extensions import db
from app.models.item import Item, ItemBatch
from app.models.stock import ItemCost, StockLedger, StockLevel

_state = threading.local()


@contextmanager
def transaction():
    """最外層開啟／提交交易；失敗整筆回滾（AD-2）。"""
    depth = getattr(_state, "depth", 0)
    _state.depth = depth + 1
    try:
        yield
        if depth == 0:
            db.session.commit()
    except Exception:
        if depth == 0:
            db.session.rollback()
        raise
    finally:
        _state.depth = depth


def _dec(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


# ── 唯讀查詢（AD-3：可用量只有一個算法）──────────────────────────
def available(item_id: int, warehouse_id: int | None = None) -> Decimal:
    """可用量 = 在手 − 占用。倉庫為 None 時為全部倉庫合計。"""
    stmt = select(
        func.coalesce(func.sum(StockLevel.on_hand - StockLevel.reserved), 0)
    ).where(StockLevel.item_id == item_id)
    if warehouse_id is not None:
        stmt = stmt.where(StockLevel.warehouse_id == warehouse_id)
    return _dec(db.session.execute(stmt).scalar_one())


def on_hand(item_id: int, warehouse_id: int | None = None) -> Decimal:
    stmt = select(func.coalesce(func.sum(StockLevel.on_hand), 0)).where(
        StockLevel.item_id == item_id
    )
    if warehouse_id is not None:
        stmt = stmt.where(StockLevel.warehouse_id == warehouse_id)
    return _dec(db.session.execute(stmt).scalar_one())


def current_cost(item_id: int) -> Decimal:
    cost = db.session.get(ItemCost, item_id)
    return _dec(cost.moving_avg_cost) if cost else Decimal("0")


def pick_level(
    *,
    item_id: int,
    warehouse_id: int,
    qty: Decimal,
    bin_id: int | None = None,
    batch_id: int | None = None,
) -> StockLevel:
    """挑選要出貨的庫存列（AD-11）。

    - 指定 bin/batch → 就用那一筆。
    - 未指定 → 依進貨批次先後（FIFO）挑第一筆可用量足夠的庫存列。
      v1 不做 FEFO（依效期挑選），那是 P2（FR-9）。
    """
    qty = _dec(qty)
    stmt = select(StockLevel).where(
        StockLevel.item_id == item_id,
        StockLevel.warehouse_id == warehouse_id,
        (StockLevel.on_hand - StockLevel.reserved) >= qty,
    )
    if bin_id is not None:
        stmt = stmt.where(StockLevel.bin_id == bin_id)
    if batch_id is not None:
        stmt = stmt.where(StockLevel.batch_id == batch_id)
    level = db.session.execute(
        stmt.order_by(StockLevel.batch_id.asc().nullsfirst(), StockLevel.id.asc())
    ).scalars().first()
    if level is None:
        raise OutOfStock(
            "可用庫存不足，找不到可出貨的庫存",
            {"item_id": item_id, "warehouse_id": warehouse_id, "required": str(qty)},
        )
    return level


# ── 內部輔助 ────────────────────────────────────────────────────
def _get_or_create_level(item_id: int, warehouse_id: int, bin_id: int, batch_id: int | None) -> StockLevel:
    stmt = select(StockLevel).where(
        StockLevel.item_id == item_id,
        StockLevel.warehouse_id == warehouse_id,
        StockLevel.bin_id == bin_id,
        StockLevel.batch_id.is_(None) if batch_id is None else StockLevel.batch_id == batch_id,
    )
    level = db.session.execute(stmt).scalar_one_or_none()
    if level is None:
        level = StockLevel(
            item_id=item_id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
            batch_id=batch_id,
            on_hand=Decimal("0"),
            reserved=Decimal("0"),
        )
        db.session.add(level)
        db.session.flush()
    return level


def _recalc_moving_avg_cost(item_id: int, add_qty: Decimal, unit_cost: Decimal) -> None:
    """AD-4：移動平均成本只有一個來源；只在入庫時重算。"""
    cost = db.session.get(ItemCost, item_id)
    if cost is None:
        cost = ItemCost(item_id=item_id, moving_avg_cost=Decimal("0"))
        db.session.add(cost)
        db.session.flush()

    prev_qty = on_hand(item_id)  # 尚未寫入前的在手量
    prev_cost = _dec(cost.moving_avg_cost)
    new_qty = prev_qty + add_qty
    if new_qty <= 0:
        cost.moving_avg_cost = Decimal("0")
    else:
        cost.moving_avg_cost = ((prev_qty * prev_cost) + (add_qty * unit_cost)) / new_qty
    db.session.flush()


def _write_ledger(
    *,
    item_id: int,
    warehouse_id: int,
    bin_id: int | None,
    batch_id: int | None,
    qty_delta: Decimal,
    movement_type: str,
    source_doc_type: str,
    source_doc_id: str | None,
    operator_id: int | None,
    reason_code: str | None = None,
    occurred_at=None,
) -> None:
    db.session.add(
        StockLedger(
            item_id=item_id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
            batch_id=batch_id,
            qty_delta=qty_delta,
            movement_type=movement_type,
            source_doc_type=source_doc_type,
            source_doc_id=source_doc_id,
            operator_id=operator_id,
            reason_code=reason_code,
            created_at=occurred_at or datetime.now(timezone.utc),
        )
    )


def _atomic_issue(item_id: int, warehouse_id: int, bin_id: int | None, batch_id: int | None, qty: Decimal) -> bool:
    """原子扣減：只有可用量足夠才成功（AD-3）。回傳是否成功。"""
    stmt = (
        update(StockLevel)
        .where(
            StockLevel.item_id == item_id,
            StockLevel.warehouse_id == warehouse_id,
            StockLevel.bin_id == bin_id,
            (StockLevel.batch_id.is_(None) if batch_id is None else StockLevel.batch_id == batch_id),
        )
        .values(
            on_hand=StockLevel.on_hand - qty,
            reserved=func.greatest(StockLevel.reserved - qty, 0),
        )
    )
    result = db.session.execute(stmt)
    return result.rowcount > 0


# ── 公開寫入方法（唯一對外介面）──────────────────────────────────
def receive(
    *,
    item_id: int,
    warehouse_id: int,
    bin_id: int,
    qty: Decimal,
    unit_cost: Decimal,
    operator_id: int | None,
    source_doc_type: str = "PO",
    source_doc_id: str | None = None,
    lot_code: str | None = None,
    expiry_date: date | None = None,
    purchase_date: date | None = None,
    supplier_id: int | None = None,
    reason_code: str | None = None,
    occurred_at=None,
) -> int:
    """入庫：建立批次（若有）→ 增加在手 → 重算移動平均成本 → 寫交易流。"""
    qty = _dec(qty)
    unit_cost = _dec(unit_cost)
    if qty <= 0:
        raise ValidationError("入庫數量必須大於 0")

    with transaction():
        item = db.session.get(Item, item_id)
        if item is None:
            raise NotFoundError(f"商品 {item_id} 不存在")

        batch_id = None
        if lot_code:
            batch = db.session.execute(
                select(ItemBatch).where(
                    ItemBatch.item_id == item_id, ItemBatch.lot_code == lot_code
                )
            ).scalar_one_or_none()
            if batch is None:
                batch = ItemBatch(
                    item_id=item_id,
                    lot_code=lot_code,
                    expiry_date=expiry_date,
                    purchase_date=purchase_date or date.today(),
                    unit_cost=unit_cost,
                    qty_received=qty,
                    supplier_id=supplier_id,
                )
                db.session.add(batch)
                db.session.flush()
            else:
                batch.qty_received = _dec(batch.qty_received) + qty
            batch_id = batch.id

        level = _get_or_create_level(item_id, warehouse_id, bin_id, batch_id)
        prev_qty = _dec(level.on_hand)
        prev_cost = current_cost(item_id)

        level.on_hand = prev_qty + qty

        # AD-4：移動平均成本重算（順序：先算成本，再寫流水）
        new_qty = prev_qty + qty
        cost = db.session.get(ItemCost, item_id)
        if cost is None:
            cost = ItemCost(item_id=item_id, moving_avg_cost=Decimal("0"))
            db.session.add(cost)
            db.session.flush()
        if new_qty > 0:
            cost.moving_avg_cost = ((prev_qty * prev_cost) + (qty * unit_cost)) / new_qty
        db.session.flush()

        _write_ledger(
            item_id=item_id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
            batch_id=batch_id,
            qty_delta=qty,
            movement_type="IN",
            source_doc_type=source_doc_type,
            source_doc_id=source_doc_id,
            operator_id=operator_id,
            reason_code=reason_code,
            occurred_at=occurred_at,
        )
        db.session.flush()
        return level.id


def reserve(
    *,
    item_id: int,
    warehouse_id: int,
    bin_id: int | None,
    batch_id: int | None,
    qty: Decimal,
    source_doc_type: str,
    source_doc_id: str | None,
) -> None:
    """建立占用（FR-23）。出貨前先佔住，避免重複售出。

    占用必須落在「將來要出庫的那一筆庫存」上（item + warehouse + bin + batch），
    否則占用與出庫會對不上（AD-3）。
    """
    qty = _dec(qty)
    if qty <= 0:
        raise ValidationError("占用數量必須大於 0")
    with transaction():
        stmt = (
            update(StockLevel)
            .where(
                StockLevel.item_id == item_id,
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.bin_id == bin_id,
                (StockLevel.batch_id.is_(None) if batch_id is None else StockLevel.batch_id == batch_id),
                (StockLevel.on_hand - StockLevel.reserved) >= qty,
            )
            .values(reserved=StockLevel.reserved + qty)
        )
        if db.session.execute(stmt).rowcount == 0:
            raise OutOfStock(
                "可用庫存不足，無法占用",
                {"item_id": item_id, "warehouse_id": warehouse_id, "required": str(qty)},
            )


def release_reserved(*, item_id: int, warehouse_id: int, bin_id: int | None, batch_id: int | None, qty: Decimal) -> None:
    """釋放占用（取消未出貨訂單時）。"""
    qty = _dec(qty)
    with transaction():
        stmt = (
            update(StockLevel)
            .where(
                StockLevel.item_id == item_id,
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.bin_id == bin_id,
                (StockLevel.batch_id.is_(None) if batch_id is None else StockLevel.batch_id == batch_id),
            )
            .values(reserved=func.greatest(StockLevel.reserved - qty, 0))
        )
        db.session.execute(stmt)


def issue_for_sale(
    *,
    item_id: int,
    warehouse_id: int,
    bin_id: int | None,
    batch_id: int | None,
    qty: Decimal,
    operator_id: int | None,
    source_doc_id: str | None,
    occurred_at=None,
) -> Decimal:
    """銷貨出庫：釋放占用 + 扣減在手 + 寫交易流。回傳出庫當下的成本快照（AD-4）。"""
    qty = _dec(qty)
    if qty <= 0:
        raise ValidationError("出庫數量必須大於 0")

    with transaction():
        ok = _atomic_issue(item_id, warehouse_id, bin_id, batch_id, qty)
        if not ok:
            raise OutOfStock(
                "可用庫存不足，無法出貨",
                {"item_id": item_id, "warehouse_id": warehouse_id, "required": str(qty)},
            )
        _write_ledger(
            item_id=item_id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
            batch_id=batch_id,
            qty_delta=-qty,
            movement_type="OUT",
            source_doc_type="SO",
            source_doc_id=source_doc_id,
            operator_id=operator_id,
            occurred_at=occurred_at,
        )
        db.session.flush()
        return current_cost(item_id)


def issue_internal(
    *,
    item_id: int,
    warehouse_id: int,
    bin_id: int | None,
    batch_id: int | None,
    qty: Decimal,
    operator_id: int | None,
    source_doc_id: str | None,
    reason_code: str,
) -> None:
    """內部領用出庫（FR-10）。"""
    qty = _dec(qty)
    with transaction():
        if not _atomic_issue(item_id, warehouse_id, bin_id, batch_id, qty):
            raise OutOfStock("可用庫存不足", {"item_id": item_id, "required": str(qty)})
        _write_ledger(
            item_id=item_id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
            batch_id=batch_id,
            qty_delta=-qty,
            movement_type="OUT",
            source_doc_type="ISSUE",
            source_doc_id=source_doc_id,
            operator_id=operator_id,
            reason_code=reason_code,
        )


def transfer_out(
    *, item_id: int, from_warehouse_id: int, from_bin_id: int | None, batch_id: int | None,
    qty: Decimal, operator_id: int | None, source_doc_id: str | None,
) -> None:
    """調出：離開來源倉 → 在途，不計入任一倉可用量（FR-12）。"""
    qty = _dec(qty)
    with transaction():
        if not _atomic_issue(item_id, from_warehouse_id, from_bin_id, batch_id, qty):
            raise OutOfStock("來源倉可用庫存不足", {"item_id": item_id, "required": str(qty)})
        _write_ledger(
            item_id=item_id, warehouse_id=from_warehouse_id, bin_id=from_bin_id, batch_id=batch_id,
            qty_delta=-qty, movement_type="TRANSFER_OUT", source_doc_type="TO",
            source_doc_id=source_doc_id, operator_id=operator_id,
        )


def transfer_in(
    *, item_id: int, to_warehouse_id: int, to_bin_id: int | None, batch_id: int | None,
    qty: Decimal, operator_id: int | None, source_doc_id: str | None,
) -> None:
    """調入：才計入目標倉（FR-12）。"""
    qty = _dec(qty)
    with transaction():
        level = _get_or_create_level(item_id, to_warehouse_id, to_bin_id, batch_id)
        level.on_hand = _dec(level.on_hand) + qty
        _write_ledger(
            item_id=item_id, warehouse_id=to_warehouse_id, bin_id=to_bin_id, batch_id=batch_id,
            qty_delta=qty, movement_type="TRANSFER_IN", source_doc_type="TO",
            source_doc_id=source_doc_id, operator_id=operator_id,
        )
