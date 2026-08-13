import json
import logging
import re
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Optional, cast

from .paths import SRC
from .settings import settings

_interaction_counter: ContextVar[int] = ContextVar("interaction_counter", default=0)
_session_id: ContextVar[str] = ContextVar("session_id", default="")
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


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


class ConsoleFormatter(logging.Formatter):
    _COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    _RESET = "\033[0m"

    def __init__(self, debug: bool) -> None:
        super().__init__()
        self._debug = debug

    def format(self, record: logging.LogRecord) -> str:
        record = cast(StructuredLogRecord, record)
        prefix = f"{record.levelname}:"
        color = self._COLORS.get(record.levelno, "")
        message = record.getMessage()

        if self._debug:
            agent = record.agent or _short_module_name(record.name)
            details = ""
            if record.details:
                details = " | " + json.dumps(
                    record.details, default=str, ensure_ascii=False
                )
            line = f"[{agent}] {prefix} {message}{details}"
        else:
            line = f"{prefix} {message}"

        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return f"{color}{line}{self._RESET}" if color else line


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
