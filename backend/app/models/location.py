from datetime import datetime, timezone

from app.extensions import db


class Warehouse(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(240))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    zones = db.relationship("Zone", back_populates="warehouse", lazy="selectin")


class Zone(db.Model):
    __tablename__ = "zones"

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False, index=True)
    code = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(80))

    warehouse = db.relationship("Warehouse", back_populates="zones")
    racks = db.relationship("Rack", back_populates="zone", lazy="selectin")


class Rack(db.Model):
    __tablename__ = "racks"

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("zones.id"), nullable=False, index=True)
    code = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(80))

    zone = db.relationship("Zone", back_populates="racks")
    bins = db.relationship("Bin", back_populates="rack", lazy="selectin")


class Bin(db.Model):
    """儲位：庫存操作的最小單位（FR-6）。"""

    __tablename__ = "bins"

    id = db.Column(db.Integer, primary_key=True)
    rack_id = db.Column(db.Integer, db.ForeignKey("racks.id"), nullable=False, index=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    capacity = db.Column(db.Numeric(12, 3))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    rack = db.relationship("Rack", back_populates="bins")
