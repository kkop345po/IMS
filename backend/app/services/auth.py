"""認證與授權（AD-6）。

角色權限只有這一份定義，對應 PRD FR-28 的權限矩陣。
所有端點一律以 require_capability 檢查；前端隱藏按鈕不算授權。
"""
from functools import wraps

from flask import g, session
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import AuthError, ForbiddenError
from app.extensions import db
from app.models.user import User

# ── 權限矩陣（唯一來源）────────────────────────────────────────────
# 能力名對應 PRD FR-28 矩陣的每一列；admin 為超級管理者。
CAPABILITIES = {
    "item.manage",        # 商品主檔增修
    "item.view",          # 商品查詢
    "supplier.manage",    # 供應商主檔維護
    "supplier.view",      # 供應商查詢
    "warehouse.manage",   # 倉庫／儲位維護
    "stock.view",         # 庫存現況與庫存交易流查詢
    "stock.receive",      # 入庫
    "stock.issue",        # 內部領用出庫／移位
    "stocktake.fill",     # 盤點建立與填報
    "stocktake.approve",  # 盤盈盤虧核准
    "transfer.create",    # 調撥單建立
    "transfer.execute",   # 調撥執行（調出／調入）
    "purchase.manage",    # 採購單
    "replenishment.view", # 補貨建議檢視
    "sales.manage",       # 銷售單與出貨
    "report.view",        # 業績與毛利報表
    "audit.view",         # 稽核軌跡查詢
    "seed.manage",        # 種子資料載入／重置
    "user.manage",        # 使用者與角色管理
}

ROLE_PERMISSIONS = {
    "admin": set(CAPABILITIES),
    "warehouse": {
        "item.view", "supplier.view", "stock.view", "stock.receive", "stock.issue",
        "transfer.execute", "stocktake.fill", "replenishment.view",
    },
    "purchasing": {
        "item.view", "supplier.view", "stock.view", "purchase.manage",
        "transfer.create", "replenishment.view",
    },
    "sales": {
        "item.view", "stock.view", "sales.manage", "replenishment.view",
    },
    "accounting": {
        "item.view", "supplier.view", "stock.view", "report.view",
    },
    "manager": {
        "item.view", "supplier.view", "stock.view", "replenishment.view",
        "report.view", "stocktake.fill", "stocktake.approve",
    },
    "viewer": {
        "item.view", "supplier.view", "stock.view", "report.view",
    },
}


def hash_password(raw: str) -> str:
    return generate_password_hash(raw)


def verify_password(password_hash: str, raw: str) -> bool:
    return check_password_hash(password_hash, raw)


def login(username: str, password: str) -> User:
    user = db.session.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthError("帳號不存在或已停用")
    if not verify_password(user.password_hash, password):
        raise AuthError("密碼錯誤")
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return user


def logout() -> None:
    session.clear()


def current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def has_capability(user: User, capability: str) -> bool:
    granted = ROLE_PERMISSIONS.get(user.role, set())
    return capability in granted


def require_capability(*capabilities: str):
    """端點守衛：每個端點都要掛（NFR-7）。"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                raise AuthError("請先登入")
            if not user.is_active:
                raise AuthError("帳號已停用")
            missing = [c for c in capabilities if not has_capability(user, c)]
            if missing:
                raise ForbiddenError(f"權限不足，缺少：{'、'.join(missing)}")
            g.current_user = user
            return func(*args, **kwargs)

        return wrapper

    return decorator
