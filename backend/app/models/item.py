from datetime import datetime, timezone

from app.extensions import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    tax_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # 統編（FR-5）
    company_name = db.Column(db.String(120), nullable=False)
    contact_name = db.Column(db.String(60))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(240))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)  # 系統產生流水號（FR-1）
    name = db.Column(db.String(120), nullable=False, index=True)
    category = db.Column(db.String(60))
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), index=True)
    default_purchase_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    default_selling_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    target_margin_rate = db.Column(db.Numeric(5, 2))  # P2 預留（FR-4）
    min_stock = db.Column(db.Numeric(12, 3), nullable=False, default=0)  # 安全水位最低值
    max_stock = db.Column(db.Numeric(12, 3), nullable=False, default=0)  # 安全水位最高值
    uom_base = db.Column(db.String(16), nullable=False, default="個")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ItemUom(db.Model):
    """單位換算（FR-1）：1 箱 = 20 個。"""

    __tablename__ = "item_uoms"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    unit_name = db.Column(db.String(16), nullable=False)
    conversion_factor = db.Column(db.Numeric(12, 4), nullable=False, default=1)


class ItemBatch(db.Model):
    """進貨批次：批次流水號、進貨日期、效期、批次單價、批次數量（FR-8、FR-19）。"""

    __tablename__ = "item_batches"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    lot_code = db.Column(db.String(40), nullable=False, index=True)
    expiry_date = db.Column(db.Date)  # P2（FR-9）
    purchase_date = db.Column(db.Date)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)  # v1 不參與成本評價（AD-4）
    qty_received = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
