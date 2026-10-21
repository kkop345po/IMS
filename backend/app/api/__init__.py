"""API 藍圖。"""
from flask import Blueprint, jsonify

from app.api.catalog import catalog_bp
from app.api.documents import documents_bp
from app.api.reports import reports_bp
from app.api.stock import stock_bp


def register_blueprints(app) -> None:
    app.register_blueprint(catalog_bp, url_prefix="/api")
    app.register_blueprint(stock_bp, url_prefix="/api")
    app.register_blueprint(documents_bp, url_prefix="/api")
    app.register_blueprint(reports_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "inventory-backend"})
