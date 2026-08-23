import ast
from pathlib import Path

APP_ROOT = Path(__file__).parents[2] / "app"
ABSTRACTED_LOGGING_LAYERS = ("api", "application", "services")
FORBIDDEN_AGENT_LOGGER_MODULES = {
    "logging",
    "app.infrastructure.execution_time_logger",
    "app.infrastructure.logger",
}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def test_abstracted_layers_do_not_import_standard_logging() -> None:
    violations: list[str] = []

    for layer in ABSTRACTED_LOGGING_LAYERS:
        for path in (APP_ROOT / layer).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if any(
                isinstance(node, ast.ImportFrom)
                and node.module == "logging"
                or isinstance(node, ast.Import)
                and any(alias.name == "logging" for alias in node.names)
                for node in ast.walk(tree)
            ):
                violations.append(str(path.relative_to(APP_ROOT)))

    assert violations == []


def test_agents_only_depend_on_logger_abstractions() -> None:
    violations: list[str] = []

    for path in (APP_ROOT / "infrastructure" / "agents").rglob("*.py"):
        forbidden_imports = _imported_modules(path) & FORBIDDEN_AGENT_LOGGER_MODULES
        if forbidden_imports:
            modules = ", ".join(sorted(forbidden_imports))
            violations.append(f"{path.relative_to(APP_ROOT)}: {modules}")

    assert violations == []
