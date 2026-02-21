from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

import structlog
from pythonjsonlogger import jsonlogger

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value: str | None) -> None:
    _request_id.set(value)


def get_request_id() -> str | None:
    return _request_id.get()

def _add_request_id(logger, method_name, event_dict):
    rid = get_request_id()
    if rid:
        event_dict["request_id"] = rid
    return event_dict

def configure_logging(service_name: str, env: str) -> None:
    # stdlib logging -> JSON
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO if env != "dev" else logging.DEBUG)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            _add_request_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG if env == "dev" else logging.INFO),
        cache_logger_on_first_use=True,
    )


def new_request_id() -> str:
    return str(uuid.uuid4())