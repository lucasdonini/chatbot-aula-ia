from rich.console import Console
from rich.markdown import Markdown

console = Console()


def print(s: str) -> None:
    md = Markdown(s)
    console.print(md)
