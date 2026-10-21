from datetime import datetime, timezone

from app.extensions import db


class StockLevel(db.Model):
    """在手／占用（AD-3）。可用量 = on_hand - reserved，只由 StockService 計算。"""

    __tablename__ = "stock_levels"
    __table_args__ = (
        db.UniqueConstraint("item_id", "warehouse_id", "bin_id", "batch_id", name="uq_stock_level"),
    )

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False, index=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("item_batches.id"), index=True)
    on_hand = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    reserved = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class StockLedger(db.Model):
    """庫存交易流（AD-5：append-only）。"""

    __tablename__ = "stock_ledger"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False, index=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"))
    batch_id = db.Column(db.Integer, db.ForeignKey("item_batches.id"))
    qty_delta = db.Column(db.Numeric(12, 3), nullable=False)
    movement_type = db.Column(db.String(24), nullable=False, index=True)  # IN / OUT / TRANSFER_OUT / TRANSFER_IN / ADJUST
    source_doc_type = db.Column(db.String(24), nullable=False, index=True)  # PO / SO / TO / ST
    source_doc_id = db.Column(db.String(64), index=True)
    reason_code = db.Column(db.String(24))
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class ItemCost(db.Model):
    """移動平均成本（AD-4：成本只有這一個來源）。"""

    __tablename__ = "item_costs"

    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), primary_key=True)
    moving_avg_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
