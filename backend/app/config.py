"""應用程式設定：全部來自環境變數（AD-8）。

缺 DATABASE_URL 時必須明確失敗，不可帶著空值嘗試連線。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# .env 自動載入（專案內的 .env 優先於外部環境變數之外，缺值時明確失敗）
load_dotenv(BASE_DIR / ".env")


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"缺少必要的環境變數 {name}。\n"
            f"請在 {BASE_DIR} 複製 .env.example 為 .env 並填入後再啟動。"
        )
    return value


class Config:
    # AD-8：連線字串只走環境變數
    SQLALCHEMY_DATABASE_URI = _required("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-insecure-secret"

    # 中文不跳脫
    JSON_AS_ASCII = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 1800  # 閒置 30 分鐘登出（FR-27）
