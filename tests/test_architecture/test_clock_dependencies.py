import ast
from pathlib import Path

APP_ROOT = Path(__file__).parents[2] / "app"
INNER_LAYERS = ("application", "domain", "services")


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def test_inner_layers_do_not_import_infrastructure_clock() -> None:
    violations: list[str] = []

    for layer in INNER_LAYERS:
        for path in (APP_ROOT / layer).rglob("*.py"):
            if "app.infrastructure.clock" in _imported_modules(path):
                violations.append(str(path.relative_to(APP_ROOT)))

    assert violations == []


def test_agents_do_not_use_global_clock_provider() -> None:
    violations: list[str] = []

    for path in (APP_ROOT / "infrastructure" / "agents").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        if names & {"get_clock", "set_clock", "SystemClock"}:
            violations.append(str(path.relative_to(APP_ROOT)))

    assert violations == []
