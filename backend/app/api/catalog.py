"""主檔 API：登入、商品、供應商、倉庫（FR-1、FR-2、FR-5、FR-6、FR-27）。"""
from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func, select

from app.errors import AuthError, NotFoundError, ValidationError
from app.extensions import db
from app.models.item import Item, ItemUom, Supplier
from app.models.location import Bin, Rack, Warehouse, Zone
from app.models.user import User
from app.services.auth import (
    ROLE_PERMISSIONS,
    current_user,
    hash_password,
    login,
    logout,
    require_capability,
)

catalog_bp = Blueprint("catalog", __name__)


# ── 認證 ────────────────────────────────────────────────────────
@catalog_bp.post("/auth/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        raise ValidationError("請輸入帳號與密碼")
    user = login(username, password)
    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "capabilities": sorted(ROLE_PERMISSIONS.get(user.role, set())),
        }
    )


@catalog_bp.post("/auth/logout")
def api_logout():
    logout()
    return jsonify({"ok": True})


@catalog_bp.get("/auth/me")
def api_me():
    # 注意：此端點不掛 require_capability（它本身就是「我是誰」的查詢），
    # 必須自行讀取 session，否則 g.current_user 永遠是 None。
    user = current_user()
    if user is None:
        raise AuthError("請先登入")
    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "capabilities": sorted(ROLE_PERMISSIONS.get(user.role, set())),
        }
    )


# ── 商品（FR-1、FR-2）───────────────────────────────────────────
@catalog_bp.get("/items")
@require_capability("item.view")
def list_items():
    keyword = (request.args.get("q") or "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    size = min(max(int(request.args.get("size", 50)), 1), 100)

    stmt = select(Item).where(Item.is_active.is_(True))
    if keyword:
        # AD-10：中文關鍵字用 ILIKE + pg_trgm，不用 FTS
        like = f"%{keyword}%"
        stmt = stmt.where((Item.name.ilike(like)) | (Item.code.ilike(like)))
    total = db.session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()
    rows = db.session.execute(
        stmt.order_by(Item.id).offset((page - 1) * size).limit(size)
    ).scalars().all()

    return jsonify(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [
                {
                    "id": r.id,
                    "code": r.code,
                    "name": r.name,
                    "category": r.category,
                    "supplier_id": r.supplier_id,
                    "default_purchase_price": r.default_purchase_price,
                    "default_selling_price": r.default_selling_price,
                    "min_stock": r.min_stock,
                    "max_stock": r.max_stock,
                    "uom_base": r.uom_base,
                }
                for r in rows
            ],
        }
    )


def _next_item_code() -> str:
    count = db.session.execute(select(func.count(Item.id))).scalar_one()
    return f"I-{count + 1:05d}"


@catalog_bp.post("/items")
@require_capability("item.manage")
def create_item():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        raise ValidationError("商品名稱必填")

    item = Item(
        code=_next_item_code(),  # FR-1：流水號由系統產生
        name=name,
        category=payload.get("category"),
        supplier_id=payload.get("supplier_id"),
        default_purchase_price=payload.get("default_purchase_price", 0),
        default_selling_price=payload.get("default_selling_price", 0),
        min_stock=payload.get("min_stock", 0),
        max_stock=payload.get("max_stock", 0),
        uom_base=payload.get("uom_base", "個"),
    )
    db.session.add(item)
    db.session.flush()

    for uom in payload.get("uoms", []):
        db.session.add(
            ItemUom(
                item_id=item.id,
                unit_name=uom.get("unit_name", "個"),
                conversion_factor=uom.get("conversion_factor", 1),
            )
        )
    db.session.commit()
    return jsonify({"id": item.id, "code": item.code, "name": item.name}), 201


# ── 供應商（FR-5）───────────────────────────────────────────────
@catalog_bp.get("/suppliers")
@require_capability("supplier.view")
def list_suppliers():
    rows = db.session.execute(select(Supplier).order_by(Supplier.id)).scalars().all()
    return jsonify(
        {
            "items": [
                {
                    "id": s.id,
                    "tax_id": s.tax_id,
                    "company_name": s.company_name,
                    "contact_name": s.contact_name,
                    "phone": s.phone,
                    "is_active": s.is_active,
                }
                for s in rows
            ]
        }
    )


@catalog_bp.post("/suppliers")
@require_capability("supplier.manage")
def create_supplier():
    payload = request.get_json(silent=True) or {}
    tax_id = (payload.get("tax_id") or "").strip()
    company_name = (payload.get("company_name") or "").strip()
    if not tax_id or not company_name:
        raise ValidationError("統編與公司名稱必填")
    exists = db.session.execute(
        select(Supplier).where(Supplier.tax_id == tax_id)
    ).scalar_one_or_none()
    if exists:
        raise ValidationError(f"統編已存在：{exists.company_name}")

    supplier = Supplier(
        tax_id=tax_id,
        company_name=company_name,
        contact_name=payload.get("contact_name"),
        phone=payload.get("phone"),
        address=payload.get("address"),
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify({"id": supplier.id, "tax_id": supplier.tax_id}), 201


# ── 倉庫與儲位（FR-6）──────────────────────────────────────────
@catalog_bp.get("/warehouses")
@require_capability("stock.view")
def list_warehouses():
    rows = db.session.execute(select(Warehouse).order_by(Warehouse.id)).scalars().all()
    bins = db.session.execute(select(Bin)).scalars().all()
    return jsonify(
        {
            "items": [
                {
                    "id": w.id,
                    "code": w.code,
                    "name": w.name,
                    "bin_count": sum(1 for b in bins if b.rack.zone.warehouse_id == w.id),
                }
                for w in rows
            ]
        }
    )


@catalog_bp.get("/bins")
@require_capability("stock.view")
def list_bins():
    rows = db.session.execute(select(Bin).order_by(Bin.id)).scalars().all()
    return jsonify(
        {
            "items": [
                {
                    "id": b.id,
                    "code": b.code,
                    "warehouse_id": b.rack.zone.warehouse_id,
                    "zone": b.rack.zone.code,
                    "rack": b.rack.code,
                }
                for b in rows
            ]
        }
    )


# ── 使用者（FR-27）─────────────────────────────────────────────
@catalog_bp.get("/users")
@require_capability("user.manage")
def list_users():
    rows = db.session.execute(select(User).order_by(User.id)).scalars().all()
    return jsonify(
        {
            "items": [
                {"id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active}
                for u in rows
            ]
        }
    )


@catalog_bp.post("/users")
@require_capability("user.manage")
def create_user():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    role = payload.get("role") or "viewer"
    if not username or not password:
        raise ValidationError("帳號與密碼必填")
    if role not in ROLE_PERMISSIONS:
        raise ValidationError(f"角色不合法：{role}")
    if db.session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none():
        raise ValidationError("帳號已存在")

    user = User(username=username, password_hash=hash_password(password), role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "username": username, "role": role}), 201
