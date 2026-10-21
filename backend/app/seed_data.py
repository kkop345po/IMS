"""種子資料（FR-31）：3 倉庫、12 商品、60+ 筆歷史異動、跨 3 個月的銷售、1 張調撥單、7 位使用者。

所有庫存變動都經由 StockService（AD-1），因此流水、成本、庫存三者的數字必然自洽。
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.extensions import db
from app.models.documents import Transfer
from app.models.item import Item, ItemBatch, ItemUom, Supplier
from app.models.location import Bin, Rack, Warehouse, Zone
from app.models.stock import StockLevel
from app.models.user import User
from app.services import sales_service, stock_service
from app.services.auth import hash_password
from app.services.stock_service import transaction

DEMO_PASSWORD = "Passw0rd!"

SUPPLIERS = [
    {"tax_id": "12345678", "company_name": "台灣飲料股份有限公司", "contact_name": "陳採購", "phone": "02-2222-3333"},
    {"tax_id": "23456789", "company_name": "中華文具用品行", "contact_name": "林經理", "phone": "02-2345-6789"},
    {"tax_id": "34567890", "company_name": "統一包材企業有限公司", "contact_name": "王專員", "phone": "03-345-6789"},
    {"tax_id": "45678901", "company_name": "佳美食品原料行", "contact_name": "張主任", "phone": "04-567-8901"},
]

ITEMS = [
    {"name": "碳酸飲料 500ml", "category": "飲料", "supplier": 0, "purchase": 18.0, "selling": 32.0, "min": 200, "max": 800, "uom": ("箱", 20)},
    {"name": "無糖茶 500ml", "category": "飲料", "supplier": 0, "purchase": 15.0, "selling": 28.0, "min": 150, "max": 600, "uom": ("箱", 24)},
    {"name": "原子筆 黑色", "category": "文具", "supplier": 1, "purchase": 6.0, "selling": 12.0, "min": 100, "max": 500, "uom": None},
    {"name": "A4 影印紙 500 張", "category": "文具", "supplier": 1, "purchase": 168.0, "selling": 220.0, "min": 30, "max": 150, "uom": None},
    {"name": "瓦楞紙箱 中型", "category": "包材", "supplier": 2, "purchase": 12.0, "selling": 0.0, "min": 80, "max": 400, "uom": None},
    {"name": "氣泡袋 30x40", "category": "包材", "supplier": 2, "purchase": 1.5, "selling": 0.0, "min": 500, "max": 2000, "uom": None},
    {"name": "冷凍雞胸肉 1kg", "category": "食材", "supplier": 3, "purchase": 95.0, "selling": 145.0, "min": 40, "max": 200, "uom": None},
    {"name": "橄欖油 500ml", "category": "食材", "supplier": 3, "purchase": 180.0, "selling": 250.0, "min": 20, "max": 80, "uom": None, "low": True},
    {"name": "砂糖 1kg", "category": "食材", "supplier": 3, "purchase": 32.0, "selling": 48.0, "min": 60, "max": 240, "uom": None},
    {"name": "咖啡豆 500g", "category": "食材", "supplier": 3, "purchase": 260.0, "selling": 380.0, "min": 25, "max": 100, "uom": None, "low": True},
    {"name": "辦公文稿袋", "category": "文具", "supplier": 1, "purchase": 22.0, "selling": 39.0, "min": 50, "max": 200, "uom": None},
    {"name": "白板筆 12 色", "category": "文具", "supplier": 1, "purchase": 78.0, "selling": 120.0, "min": 35, "max": 140, "uom": None},
]

WAREHOUSES = [
    {"code": "WH-A", "name": "總倉（中和）"},
    {"code": "WH-B", "name": "倉北分倉"},
    {"code": "WH-C", "name": "倉南分倉"},
]

USERS = [
    {"username": "admin", "role": "admin"},
    {"username": "warehouse", "role": "warehouse"},
    {"username": "purchasing", "role": "purchasing"},
    {"username": "sales", "role": "sales"},
    {"username": "sales2", "role": "sales"},
    {"username": "sales3", "role": "sales"},
    {"username": "accounting", "role": "accounting"},
    {"username": "manager", "role": "manager"},
    {"username": "viewer", "role": "viewer"},
]


def _clear_all() -> None:
    """只清除種子資料（不動使用者自行建立的資料）。"""
    from app.models.documents import (
        PurchaseOrder,
        PurchaseOrderLine,
        SalesOrder,
        SalesOrderLine,
    )
    from app.models.stock import ItemCost, StockLedger

    for model in (
        SalesOrderLine,
        SalesOrder,
        PurchaseOrderLine,
        PurchaseOrder,
        Transfer,
        StockLedger,
        StockLevel,
        ItemCost,
        ItemBatch,
        ItemUom,
        Item,
        Bin,
        Rack,
        Zone,
        Warehouse,
        Supplier,
    ):
        db.session.query(model).delete()
    db.session.commit()


def seed() -> dict:
    random.seed(20261021)
    now = datetime.now(timezone.utc)

    _clear_all()

    # ── 使用者（upsert：既有帳號只更新角色與密碼）──────────────
    users: dict[str, User] = {}
    for spec in USERS:
        user = db.session.execute(
            select(User).where(User.username == spec["username"])
        ).scalar_one_or_none()
        if user is None:
            user = User(username=spec["username"], password_hash=hash_password(DEMO_PASSWORD))
            db.session.add(user)
        user.role = spec["role"]
        user.password_hash = hash_password(DEMO_PASSWORD)
        user.is_active = True
        users[spec["username"]] = user
    db.session.flush()

    # ── 供應商 ────────────────────────────────────────────────
    suppliers: list[Supplier] = []
    for spec in SUPPLIERS:
        s = Supplier(**spec)
        db.session.add(s)
        suppliers.append(s)
    db.session.flush()

    # ── 倉庫 → 區 → 架 → 儲位 ────────────────────────────────
    bins: dict[str, list[Bin]] = {}
    for w_spec in WAREHOUSES:
        wh = Warehouse(code=w_spec["code"], name=w_spec["name"])
        db.session.add(wh)
        db.session.flush()
        wh_bins: list[Bin] = []
        for z_idx, zone_code in enumerate(["A", "B"], start=1):
            zone = Zone(warehouse_id=wh.id, code=f"{wh.code}-Z{z_idx}", name=f"{zone_code} 區")
            db.session.add(zone)
            db.session.flush()
            for r_idx in range(1, 3):
                rack = Rack(zone_id=zone.id, code=f"{zone_code}-R{r_idx}", name=f"{zone_code} 架 {r_idx}")
                db.session.add(rack)
                db.session.flush()
                for b_idx in range(1, 4):
                    b = Bin(rack_id=rack.id, code=f"{wh.code}-{zone_code}-{r_idx:02d}-{b_idx:02d}")
                    db.session.add(b)
                    wh_bins.append(b)
        db.session.flush()
        bins[w_spec["code"]] = wh_bins

    # ── 商品（含單位換算）────────────────────────────────────
    items: list[Item] = []
    for idx, spec in enumerate(ITEMS, start=1):
        item = Item(
            code=f"I-{idx:05d}",
            name=spec["name"],
            category=spec["category"],
            supplier_id=suppliers[spec["supplier"]].id,
            default_purchase_price=Decimal(str(spec["purchase"])),
            default_selling_price=Decimal(str(spec["selling"])),
            min_stock=Decimal(str(spec["min"])),
            max_stock=Decimal(str(spec["max"])),
            uom_base=spec["uom"][0] if spec["uom"] else "個",
        )
        db.session.add(item)
        items.append(item)
    db.session.flush()

    for item, spec in zip(items, ITEMS):
        if spec["uom"]:
            unit, factor = spec["uom"]
            db.session.add(
                ItemUom(item_id=item.id, unit_name=unit, conversion_factor=Decimal(str(factor)))
            )
    db.session.commit()

    # ── 歷史進貨（90 天內兩批，總量留出銷售消耗的餘裕）──────
    admin = users["admin"]
    wh_a_bins = bins["WH-A"]
    wh_a_id = wh_a_bins[0].rack.zone.warehouse_id
    for item, spec in zip(items, ITEMS):
        for batch_no, days_ago in enumerate((88, 42), start=1):
            if spec.get("low"):
                # 刻意進貨不足 → 低於安全水位 → 補貨建議有內容（FR-17）
                factor = Decimal("0.1") if batch_no == 1 else Decimal("0.05")
            else:
                factor = Decimal("1.2") if batch_no == 1 else Decimal("0.8")
            qty = (Decimal(str(spec["max"])) * factor).quantize(Decimal("1"))
            occurred = now - timedelta(days=days_ago, hours=random.randint(0, 8))
            lot = f"LOT-{item.code}-{batch_no:02d}"
            stock_service.receive(
                item_id=item.id,
                warehouse_id=wh_a_id,
                bin_id=wh_a_bins[(item.id + batch_no) % len(wh_a_bins)].id,
                qty=qty,
                unit_cost=Decimal(str(spec["purchase"])),
                operator_id=admin.id,
                source_doc_type="PO",
                source_doc_id=f"PO-SEED-{item.id:03d}-{batch_no}",
                lot_code=lot,
                purchase_date=(now - timedelta(days=days_ago)).date(),
                expiry_date=(now + timedelta(days=180)).date() if spec["category"] == "食材" else None,
                supplier_id=suppliers[spec["supplier"]].id,
                occurred_at=occurred,
            )

    # ── 歷史銷售（跨 3 個月、3 位銷貨員）────────────────────
    sales_users = [users["sales"], users["sales2"], users["sales3"]]
    customers = ["台北門市", "高雄門市", "台中客戶", "桃園客戶", "新竹客戶"]
    order_count = 0
    for months_ago in (2, 1, 0):
        for _ in range(7):
            salesperson = random.choice(sales_users)
            occurred = now - timedelta(
                days=random.randint(months_ago * 30 + 1, (months_ago + 1) * 30)
            )
            lines = []
            for item, spec in random.sample(list(zip(items, ITEMS)), k=random.randint(1, 3)):
                if not spec["selling"] or spec.get("low"):
                    continue
                # 從「實際有庫存」的儲位出貨
                level = db.session.execute(
                    select(StockLevel)
                    .where(StockLevel.item_id == item.id, StockLevel.warehouse_id == wh_a_id)
                    .order_by(StockLevel.on_hand.desc())
                ).scalars().first()
                if level is None:
                    continue
                lines.append(
                    {
                        "item_id": item.id,
                        "warehouse_id": wh_a_id,
                        "bin_id": level.bin_id,
                        "batch_id": level.batch_id,
                        "qty": Decimal(str(random.randint(3, 15))),
                        "unit_price": Decimal(str(spec["selling"])),
                    }
                )
            if not lines:
                continue
            order = sales_service.create_order(
                salesperson_id=salesperson.id,
                customer_name=random.choice(customers),
                lines=lines,
            )
            sales_service.send_order(order.id)
            sales_service.ship_order(order.id, admin.id, shipped_at=occurred)
            order_count += 1

    # ── 採購單（3 張不同狀態，讓「採購單」頁一開就有內容）──
    from app.services import purchasing_service
    from datetime import timedelta as _td

    po_specs = [
        ("draft", 0.0),      # 草稿：等待送出
        ("sent", 0.0),       # 已送出：等待收貨
        ("partially_received", 0.5),  # 部分收貨
    ]
    for idx, (status, ratio) in enumerate(po_specs):
        line_items = [items[idx], items[idx + 1]]
        po = purchasing_service.create_order(
            supplier_id=line_items[0].supplier_id or suppliers[0].id,
            created_by=admin.id,
            expected_date=(now + _td(days=7)).date(),
            lines=[
                {
                    "item_id": it.id,
                    "qty": (Decimal(str(it.max_stock)) * Decimal("0.4")).quantize(Decimal("1")),
                    "unit_price": it.default_purchase_price,
                }
                for it in line_items
            ],
        )
        if status != "draft":
            purchasing_service.send_order(po.id)
        if status == "partially_received":
            for line in po.lines:
                purchasing_service.receive_line(
                    purchase_order_id=po.id,
                    line_id=line.id,
                    received_qty=Decimal(str(int(float(line.qty) * ratio))),
                    warehouse_id=wh_a_id,
                    bin_id=wh_a_bins[(line.item_id + idx) % len(wh_a_bins)].id,
                    operator_id=admin.id,
                    lot_code=f"LOT-PO-{po.id:04d}-{line.item_id:04d}",
                )

    # ── 1 張在途調撥單（FR-12）───────────────────────────────
    item = items[0]
    target_wh = bins["WH-B"][0].rack.zone.warehouse_id
    # 從該商品「實際有庫存」的儲位調出
    src_level = db.session.execute(
        select(StockLevel)
        .where(StockLevel.item_id == item.id, StockLevel.warehouse_id == wh_a_id)
        .order_by(StockLevel.on_hand.desc())
    ).scalars().first()
    transfer = Transfer(
        transfer_no="TO-SEED-0001",
        from_warehouse_id=wh_a_id,
        to_warehouse_id=target_wh,
        from_bin_id=src_level.bin_id,
        to_bin_id=bins["WH-B"][0].id,
        item_id=item.id,
        qty=Decimal("50"),
        status="in_transit",
        created_by=admin.id,
    )
    db.session.add(transfer)
    db.session.flush()
    stock_service.transfer_out(
        item_id=item.id,
        from_warehouse_id=wh_a_id,
        from_bin_id=src_level.bin_id,
        batch_id=src_level.batch_id,
        qty=Decimal("50"),
        operator_id=admin.id,
        source_doc_id=transfer.transfer_no,
    )
    db.session.commit()

    ledger_count = db.session.execute(select(StockLevel.id)).scalars().all()
    return {
        "users": len(users),
        "suppliers": len(suppliers),
        "items": len(items),
        "warehouses": len(WAREHOUSES),
        "bins": sum(len(v) for v in bins.values()),
        "sales_orders": order_count,
        "stock_rows": len(ledger_count),
        "password": DEMO_PASSWORD,
    }
