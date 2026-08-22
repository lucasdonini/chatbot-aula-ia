import json
import logging
import re
import sys
from collections.abc import Mapping
from contextvars import ContextVar
from copy import copy
from pathlib import Path
from typing import Any, Optional, cast

from uvicorn.logging import DefaultFormatter

from app.application.ports.logger import Logger

from .paths import SRC
from .settings import settings

_interaction_counter: ContextVar[int] = ContextVar("interaction_counter", default=0)
_session_id: ContextVar[str] = ContextVar("session_id", default="")
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


class PythonLoggerAdapter:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    @staticmethod
    def _extra(details: Mapping[str, object] | None) -> dict[str, object] | None:
        if details is None:
            return None
        return {"details": dict(details)}

    def debug(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.debug(message, extra=self._extra(details))

    def info(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.info(message, extra=self._extra(details))

    def warning(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.warning(message, extra=self._extra(details))

    def error(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.error(message, extra=self._extra(details))

    def exception(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        self._logger.exception(message, extra=self._extra(details))


def create_logger(name: str) -> Logger:
    return PythonLoggerAdapter(logging.getLogger(name))


def set_session_context(session_id: str) -> None:
    _session_id.set(session_id)


def set_trace_context(trace_id: str) -> None:
    _trace_id.set(trace_id)


def increment_interaction() -> None:
    _interaction_counter.set(_interaction_counter.get() + 1)


_TOP_LEVEL_MODULES = "|".join(d.name for d in SRC.iterdir() if d.is_dir())
_TOP_LEVEL_MODULE_REGEX = re.compile(r"^({})\.".format(_TOP_LEVEL_MODULES))
_TOOLS_REGEX = re.compile(r"\.tools\.")
_SUFFIX_REGEX = re.compile(r"(_agent|_service|_repository)$")


def _short_module_name(name: str) -> str:
    name = name.removeprefix(f"{SRC.name}.")
    name = _TOP_LEVEL_MODULE_REGEX.sub("", name)
    name = _TOOLS_REGEX.sub(".", name)
    name = _SUFFIX_REGEX.sub("", name)

    parts = name.split(".")
    if len(parts) >= 2 and parts[-1] == parts[-2]:
        parts.pop()

    return ".".join(parts)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        structured_record = cast(StructuredLogRecord, record)
        structured_record.interaction = _interaction_counter.get()
        structured_record.session_id = _session_id.get()
        structured_record.trace_id = _trace_id.get()
        structured_record.agent = _short_module_name(record.name)
        return True


class StructuredLogRecord(logging.LogRecord):
    agent: Optional[str] = None
    session_id: str = "-"
    trace_id: str = "-"
    interaction: int = 0
    details: Optional[dict[str, Any]] = None


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record = cast(StructuredLogRecord, record)
        record.asctime = self.formatTime(record, self.datefmt)

        level = f"{record.levelname:<5}"
        agent = record.agent
        session = record.session_id[:8] if record.session_id else "-"
        trace = record.trace_id[:8] if record.trace_id else "-"
        interaction = record.interaction
        ctx = f"session={session} int={interaction} trace={trace}"

        message = record.getMessage().replace("\n", "\n\t")

        details = record.details
        json_str = ""
        if details is not None and details != {}:
            json_str = " | " + json.dumps(details, default=str, ensure_ascii=False)

        line = f"{record.asctime} | {level} | {agent} | {ctx} | {message}{json_str}"

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            line = line + "\n" + record.exc_text

        return line

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        if datefmt:
            return super().formatTime(record, datefmt)
        return (
            f"{super().formatTime(record, '%Y-%m-%d %H:%M:%S')}.{int(record.msecs):03d}"
        )


class ConsoleFormatter(DefaultFormatter):
    def __init__(self, debug: bool) -> None:
        super().__init__(
            fmt="%(levelprefix)s %(message)s",
            use_colors=sys.stdout.isatty(),
        )
        self._debug = debug

    def format(self, record: logging.LogRecord) -> str:
        record = cast(StructuredLogRecord, record)
        message = record.getMessage()
        details = getattr(record, "details", None)

        if self._debug:
            agent = record.agent or _short_module_name(record.name)
            context = f"[{agent}] "
            if details:
                message += " | " + json.dumps(details, default=str, ensure_ascii=False)
        else:
            context = ""
            if details:
                for key in ("name", "from", "chain"):
                    value = details.get(key)
                    if isinstance(value, str) and value:
                        context = f"[{value}] "
                        break

        record_copy = copy(record)
        record_copy.msg = f"{context}{message}"
        record_copy.args = ()
        return super().format(record_copy)


def _get_log_level() -> int:
    return logging.DEBUG if settings.log_level == "DEBUG" else logging.INFO


def setup_logger() -> None:
    logging.setLogRecordFactory(StructuredLogRecord)
    root = logging.getLogger()
    root.setLevel(_get_log_level())
    for handler in root.handlers:
        handler.close()
    root.handlers.clear()

    file_fmt = StructuredFormatter(
        fmt=(
            "%(asctime)s | %(levelname)-5s | %(agent)s |"
            " session=%(session_id)s int=%(interaction)d trace=%(trace_id)s"
            " | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if settings.log_to_file:
        Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            settings.log_file, mode="a", encoding="utf-8"
        )
        file_handler.setFormatter(file_fmt)
        file_handler.addFilter(ContextFilter())
        root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_get_log_level())
    console_handler.setFormatter(ConsoleFormatter(debug=settings.log_level == "DEBUG"))
    console_handler.addFilter(ContextFilter())
    root.addHandler(console_handler)

    root.info("Session initialized")

    silenced_loggers = [
        "groq",
        "httpx",
        "langchain",
        "langgraph",
        "httpcore",
        "markdown_it",
        "faiss",
        "asyncio",
        "pymongo",
        "google_genai",
    ]
    for logger_name in silenced_loggers:
        lg = logging.getLogger(logger_name)
        lg.setLevel(logging.WARNING)
        lg.propagate = False
