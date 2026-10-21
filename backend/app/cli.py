"""CLI 指令：flask seed --reset。"""
from __future__ import annotations

import click
from flask.cli import with_appcontext

from app.extensions import db


def register_cli(app) -> None:
    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="先清除既有示範資料再重新載入")
    @with_appcontext
    def seed_command(reset: bool):
        """載入示範種子資料（FR-31）。"""
        from app.seed_data import seed

        if not reset:
            click.echo("提示：種子資料會重建示範資料，建議使用 --reset")
        result = seed()
        click.echo("種子資料載入完成：")
        for key, value in result.items():
            click.echo(f"  {key}: {value}")

    @app.cli.command("db-reset")
    @with_appcontext
    def db_reset():
        """清空所有資料表（僅限開發環境）。"""
        from app.seed_data import _clear_all

        _clear_all()
        click.echo("資料已清空。")
