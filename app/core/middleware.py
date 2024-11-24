# app/core/middleware.py
from fastapi import Request
import time
from .logging_config import logger


async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"Request started: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "duration_ms": round(duration * 1000, 2),
                "status_code": response.status_code,
            },
        )

        return response

    except Exception as exc:
        # Log exception
        duration = time.time() - start_time
        logger.exception(
            f"Request failed: {request.method} {request.url.path}",
            extra={"duration_ms": round(duration * 1000, 2), "error": str(exc)},
        )
        raise
