from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# A JSON API surface should never accept megabytes of structured data; the
# larger ceiling leaves room for the 10 MB document upload plus multipart
# framing overhead.
JSON_BODY_LIMIT_BYTES = 1024 * 1024
OTHER_BODY_LIMIT_BYTES = 11 * 1024 * 1024


class BodyLimitMiddleware:
    """Reject oversized request bodies before the app sees them.

    Pure ASGI rather than BaseHTTPMiddleware: buffering ``receive`` counts
    every chunk of a chunked transfer, which BaseHTTPMiddleware cannot see.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        content_type = Headers(scope=scope).get("content-type", "")
        limit = (
            JSON_BODY_LIMIT_BYTES
            if "application/json" in content_type
            else OTHER_BODY_LIMIT_BYTES
        )
        buffered: list[Message] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > limit:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                    headers={"Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
            buffered.append(message)
            if not message.get("more_body", False):
                break

        iterator = iter(buffered)

        async def replayed_receive() -> Message:
            try:
                return next(iterator)
            except StopIteration:
                return await receive()

        await self.app(scope, replayed_receive, send)
