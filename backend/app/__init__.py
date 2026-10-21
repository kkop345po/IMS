"""應用程式工廠。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider

from app.config import Config
from app.errors import DomainError
from app.extensions import db, migrate


class AppJSONProvider(DefaultJSONProvider):
    """Decimal / date 的 JSON 序列化（AD-7：不可轉成 float 丟精度）。"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.json = AppJSONProvider(app)
    app.json.ensure_ascii = False  # 中文不跳脫

    db.init_app(app)
    migrate.init_app(app, db)

    from app.api import register_blueprints

    register_blueprints(app)

    @app.errorhandler(DomainError)
    def handle_domain_error(error: DomainError):
        return jsonify(error.to_dict()), error.status

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"code": "NOT_FOUND", "message": "找不到資源", "details": {}}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        app.logger.exception("未預期錯誤")
        return (
            jsonify({"code": "INTERNAL_ERROR", "message": "伺服器內部錯誤", "details": {}}),
            500,
        )

    from app.cli import register_cli

    register_cli(app)

    return app
