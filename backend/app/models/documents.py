from datetime import date, datetime, timezone

from app.extensions import db

PURCHASE_STATUS = ("draft", "sent", "partially_received", "received")
SALES_STATUS = ("draft", "sent", "shipped", "cancelled")
TRANSFER_STATUS = ("draft", "in_transit", "received")


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    po_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False, index=True)
    status = db.Column(db.String(24), nullable=False, default="draft", index=True)
    expected_date = db.Column(db.Date)
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    lines = db.relationship(
        "PurchaseOrderLine", back_populates="purchase_order", lazy="selectin", cascade="all, delete-orphan"
    )


class PurchaseOrderLine(db.Model):
    __tablename__ = "purchase_order_lines"

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    qty = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    received_qty = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    lot_code = db.Column(db.String(40))
    expiry_date = db.Column(db.Date)
    received_at = db.Column(db.DateTime(timezone=True))  # 實際進貨日期於入庫時帶入（FR-19）

    purchase_order = db.relationship("PurchaseOrder", back_populates="lines")


class SalesOrder(db.Model):
    __tablename__ = "sales_orders"

    id = db.Column(db.Integer, primary_key=True)
    so_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120))
    salesperson_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(24), nullable=False, default="draft", index=True)
    discount_type = db.Column(db.String(16))  # percent / fixed
    discount_value = db.Column(db.Numeric(12, 2))
    total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    total_cost = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    shipped_at = db.Column(db.DateTime(timezone=True))

    lines = db.relationship(
        "SalesOrderLine", back_populates="sales_order", lazy="selectin", cascade="all, delete-orphan"
    )


class SalesOrderLine(db.Model):
    __tablename__ = "sales_order_lines"

    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey("sales_orders.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False, index=True)
    bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"))
    batch_id = db.Column(db.Integer, db.ForeignKey("item_batches.id"))
    qty = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_type = db.Column(db.String(16))
    discount_value = db.Column(db.Numeric(12, 2))
    line_total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    line_cost = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    # AD-4：出庫當下的成本快照，之後成本變動不回溯改寫歷史毛利
    unit_cost_snapshot = db.Column(db.Numeric(12, 2))

    sales_order = db.relationship("SalesOrder", back_populates="lines")


class Transfer(db.Model):
    __tablename__ = "transfers"

    id = db.Column(db.Integer, primary_key=True)
    transfer_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False, index=True)
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False, index=True)
    from_bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"))
    to_bin_id = db.Column(db.Integer, db.ForeignKey("bins.id"))
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("item_batches.id"), index=True)  # 調撥後仍認得原批次
    qty = db.Column(db.Numeric(12, 3), nullable=False, default=0)
    status = db.Column(db.String(24), nullable=False, default="draft", index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    received_at = db.Column(db.DateTime(timezone=True))
