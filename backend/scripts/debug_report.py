import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("FLASK_APP", "wsgi:app")

from sqlalchemy import func, select, text
from app import create_app
from app.extensions import db
from app.models.documents import SalesOrder
from app.models.user import User

app = create_app()
with app.app_context():
    print("狀態分布:", db.session.execute(text("select status, count(*) from sales_orders group by status")).all())
    print("銷貨員分布:", db.session.execute(text("select salesperson_id, count(*) from sales_orders group by salesperson_id")).all())
    print("shipped_at 範圍:", db.session.execute(text("select min(shipped_at), max(shipped_at) from sales_orders")).all())
    rows = db.session.execute(select(SalesOrder.id, SalesOrder.salesperson_id, SalesOrder.status, SalesOrder.shipped_at).limit(3)).all()
    print("範例列:", rows)
    print("使用者:", db.session.execute(select(User.id, User.username, User.role)).all())
    agg = (
        select(
            SalesOrder.salesperson_id.label("sid"),
            func.count(func.distinct(SalesOrder.id)).label("order_count"),
            func.coalesce(func.sum(SalesOrder.total), 0).label("total"),
        )
        .where(SalesOrder.status == "shipped")
        .group_by(SalesOrder.salesperson_id)
        .subquery()
    )
    print("子查詢結果:", db.session.execute(select(agg)).all())
    q = (
        select(User.id, User.username, agg.c.order_count, agg.c.total)
        .join(agg, agg.c.sid == User.id)
        .order_by(User.username)
    )
    print("最終結果:", db.session.execute(q).all())
