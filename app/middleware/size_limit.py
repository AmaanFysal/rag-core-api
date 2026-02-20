from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

UPLOAD_MAX_BYTES = 10 * 1024 * 1024   # 10 MB for /documents/upload
DEFAULT_MAX_BYTES = 1 * 1024 * 1024   # 1 MB for all other routes


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        max_bytes = UPLOAD_MAX_BYTES if request.url.path == "/documents/upload" else DEFAULT_MAX_BYTES

        # Fast path: trust Content-Length header when present
        content_length = request.headers.get("content-length")
        if content_length is not None:
            if int(content_length) > max_bytes:
                return Response(
                    content="Request body too large",
                    status_code=413,
                )

        # Slow path: buffer entire body (BaseHTTPMiddleware caches it so
        # the route handler can still read it via request.body())
        body = await request.body()
        if len(body) > max_bytes:
            return Response(
                content="Request body too large",
                status_code=413,
            )

        return await call_next(request)
