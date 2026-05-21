import logging
from pathlib import Path


class InlineMessageFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_line = super().format(record)
        return log_line.replace("\n", "\\n")


def setup_logger(log_file: str = "logs/app.log", level: int = logging.DEBUG) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    fmt = InlineMessageFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(fmt)

    root.addHandler(file_handler)

    root.info("=" * 60)
    root.info(" New Session Initialized ".center(60, "-"))
    root.info("=" * 60)

    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("groq").propagate = False
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("markdown_it").setLevel(logging.WARNING)
    logging.getLogger("faiss").setLevel(logging.WARNING)
