"""Structured logging.

Log events, not sentences: every line is a set of key=value fields,
rendered pretty for dev consoles and as JSON for production. Configured
exactly once at startup via configure_logging(settings). Context such as
request_id binds via contextvars and appears on every subsequent line
automatically.

"""

import logging
import sys

import structlog

from ragx.config import Environment, Settings

get_logger = structlog.get_logger

def configure_logging(settings : Settings) -> None:
    shared_processors :list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso",utc=True)
    ]

    renderer: structlog.typing.Processor
    if settings.environment is Environment.PRODUCTION:
      shared_processors.append(structlog.processors.dict_tracebacks)
      renderer = structlog.processors.JSONRenderer()
    else:
      renderer = structlog.dev.ConsoleRenderer()

    """here are the global rules for what happens when our code calls log.info(...)."""
    structlog.configure(
       processors=[
          *shared_processors,
          structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
       ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
       foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level)
