"""領域例外 → 統一 JSON 錯誤格式（spine 一致性慣例）。"""
from typing import Any, Optional


class DomainError(Exception):
    code = "DOMAIN_ERROR"
    status = 400

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"
    status = 400


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    status = 404


class AuthError(DomainError):
    code = "UNAUTHORIZED"
    status = 401


class ForbiddenError(DomainError):
    code = "FORBIDDEN"
    status = 403


class OutOfStock(DomainError):
    code = "OUT_OF_STOCK"
    status = 409


class InvalidStateTransition(DomainError):
    code = "INVALID_STATE_TRANSITION"
    status = 409


class StocktakeLocked(DomainError):
    code = "STOCKTAKE_LOCKED"
    status = 409
