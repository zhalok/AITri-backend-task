from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, **extra):
        super().__init__(message)
        self.message = message
        self.extra = extra  # more fields for the response body, e.g. the value that is current now


class UnauthorizedError(AppError):
    status_code, code = 401, "unauthorized"


class ForbiddenError(AppError):
    status_code, code = 403, "forbidden"


class NotFoundError(AppError):
    status_code, code = 404, "not_found"


class ConflictError(AppError):
    status_code, code = 409, "conflict"


class StaleDataError(ConflictError):
    """The caller acted on a value that is no longer current. Nothing was written; `current` is what is stored."""

    code = "stale_data"


class DomainValidationError(AppError):
    status_code, code = 422, "validation_error"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, **exc.extra})
