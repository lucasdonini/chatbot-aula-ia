import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional, cast

from .paths import SRC

_INTERACTION_COUNTER: int = 0
_current_session_id: str = ""
_current_trace_id: str = ""


def set_session_context(session_id: str) -> None:
    global _current_session_id
    _current_session_id = session_id


def set_trace_context(trace_id: str) -> None:
    global _current_trace_id
    _current_trace_id = trace_id


def increment_interaction() -> None:
    global _INTERACTION_COUNTER
    _INTERACTION_COUNTER += 1


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
        record.interaction = _INTERACTION_COUNTER
        record.session_id = _current_session_id
        record.trace_id = _current_trace_id
        record.agent = _short_module_name(record.name)
        return True


class HideConsoleTracebackFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            record.exc_info = None
            record.exc_text = None
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


def setup_logger(log_file: str = "logs/app.log", level: int = logging.DEBUG) -> None:
    logging.setLogRecordFactory(StructuredLogRecord)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    file_fmt = StructuredFormatter(
        fmt=(
            "%(asctime)s | %(levelname)-5s | %(agent)s |"
            " session=%(session_id)s int=%(interaction)d trace=%(trace_id)s"
            " | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_fmt)
    file_handler.addFilter(ContextFilter())
    root.addHandler(file_handler)

    console_fmt = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.CRITICAL)
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(ContextFilter())
    console_handler.addFilter(HideConsoleTracebackFilter())
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
