import logging
import sys
import traceback

from app.core.redaction import redact_text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = ()
        if record.exc_info:
            record.exc_text = redact_text(
                "".join(traceback.format_exception(*record.exc_info))
            )
            record.exc_info = None
        if record.stack_info:
            record.stack_info = redact_text(record.stack_info)
        return True


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    handler.addFilter(RedactingFilter())
    root.handlers = [handler]

    # Uvicorn logs unhandled-exception tracebacks through its own loggers with
    # propagation disabled, so those records never reach the root handler
    # above. Its logging is configured before the app is imported, so the
    # handlers already exist here.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        for uvicorn_handler in logging.getLogger(name).handlers:
            if not any(
                isinstance(existing, RedactingFilter)
                for existing in uvicorn_handler.filters
            ):
                uvicorn_handler.addFilter(RedactingFilter())
