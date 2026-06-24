import logging
import sys
from pathlib import Path


class InlineMessageFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.exc_info:
            return super().format(record)

        log_line = super().format(record)
        return log_line.replace("\n", "\\n")


class HideConsoleTracebackFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            record.exc_info = None
            record.exc_text = None
        return True


def setup_logger(log_file: str = "logs/app.log", level: int = logging.DEBUG) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    file_fmt = InlineMessageFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_fmt)
    root.addHandler(file_handler)

    console_fmt = logging.Formatter(fmt="%(levelname)s: %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.CRITICAL)
    console_handler.setFormatter(console_fmt)
    console_handler.addFilter(HideConsoleTracebackFilter())
    root.addHandler(console_handler)

    root.info("=" * 60)
    root.info(" New Session Initialized ".center(60, "-"))
    root.info("=" * 60)

    loggers_para_silenciar = [
        "groq",
        "httpx",
        "langchain",
        "langgraph",
        "httpcore",
        "markdown_it",
        "faiss",
        "asyncio",
    ]
    for logger_name in loggers_para_silenciar:
        lg = logging.getLogger(logger_name)
        lg.setLevel(logging.WARNING)
        lg.propagate = False
