import ast
import io
import tokenize
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
FEATURES = ("accounts", "catalog", "households", "inventory", "promotions", "recipes", "shopping")
FRAMEWORKS = ("django", "rest_framework", "httpx", "bs4", "PIL", "MySQLdb")
FORBIDDEN_TYPING = {"Any", "TypeVar", "Protocol", "cast", "TYPE_CHECKING"}
FORBIDDEN_BUILTINS = {"getattr", "setattr"}
VAGUE_MODULE_NAMES = {"utils", "helpers", "helper", "common", "misc", "manager", "handlers"}
ALLOWED_INNER_CALLS = {
    "str",
    "int",
    "float",
    "bool",
    "len",
    "tuple",
    "list",
    "set",
    "dict",
    "sorted",
    "min",
    "max",
    "any",
    "all",
    "Q",
    "F",
    "When",
    "Case",
    "enum_choices",
    "enum_values",
    "super",
    "isinstance",
    "frozenset",
    "range",
    "Count",
    "Decimal",
    "path",
    "include",
    "get",
    "split",
    "strip",
    "values",
    "keys",
    "items",
    "casefold",
    "lower",
    "replace",
    "group",
    "groups",
    "get_username",
    "now",
}


def _python_files() -> list[Path]:
    return sorted(
        path
        for path in BACKEND.rglob("*.py")
        if "migrations" not in path.parts and ".venv" not in path.parts
    )


def _application_files() -> list[Path]:
    return [
        path
        for path in _python_files()
        if "tests" not in path.parts and path.name not in {"settings.py", "urls.py", "conftest.py"}
    ]


def _module(path: Path) -> str:
    return ".".join(path.relative_to(BACKEND).with_suffix("").parts)


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return imported


def _is_orm_module(module: str) -> bool:
    parts = module.split(".")
    return len(parts) == 2 and parts[1] == "models"


def _layer(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) > 1 and parts[1] in {"domain", "application", "infrastructure", "presentation"}:
        return parts[1]
    return None


def _violations_of(rule: str, found: list[str]) -> None:
    assert found == [], f"{rule}:\n" + "\n".join(found)


def test_domain_and_application_are_free_of_frameworks_and_outer_layers() -> None:
    found = []
    for path in _application_files():
        module = _module(path)
        if _layer(module) not in {"domain", "application"}:
            continue
        for imported in _imports(path):
            root = imported.split(".")[0]
            outer = _layer(imported) in {"infrastructure", "presentation"}
            if root in FRAMEWORKS or root == "config" or outer or _is_orm_module(imported):
                found.append(f"{module} imports {imported}")
    _violations_of("the core depends on a framework or an outer layer", found)


def test_domain_does_not_depend_on_application() -> None:
    found = [
        f"{_module(path)} imports {imported}"
        for path in _application_files()
        if _layer(_module(path)) == "domain"
        for imported in _imports(path)
        if _layer(imported) == "application"
    ]
    _violations_of("domain imports application", found)


def test_application_uses_no_other_feature() -> None:
    found = []
    for path in _application_files():
        module = _module(path)
        feature = module.split(".")[0]
        if _layer(module) != "application":
            continue
        for imported in _imports(path):
            root = imported.split(".")[0]
            if root in FEATURES and root != feature:
                found.append(f"{module} imports {imported}")
    _violations_of("application code crosses a feature boundary", found)


def test_presentation_reaches_only_the_application_and_the_composition_root() -> None:
    found = []
    for path in _application_files():
        module = _module(path)
        if _layer(module) != "presentation":
            continue
        for imported in _imports(path):
            if _layer(imported) == "infrastructure" or _is_orm_module(imported):
                found.append(f"{module} imports {imported}")
    _violations_of("presentation bypasses the application", found)


def test_features_meet_only_through_public_use_cases_errors_and_domain() -> None:
    allowed_layers = {"domain", "application"}
    found = []
    for path in _application_files():
        module = _module(path)
        feature = module.split(".")[0]
        if feature not in FEATURES or _layer(module) != "infrastructure":
            continue
        for imported in _imports(path):
            root = imported.split(".")[0]
            if root not in FEATURES or root == feature:
                continue
            parts = imported.split(".")
            public = _layer(imported) in allowed_layers and (
                parts[1] == "domain" or parts[2] in {"use_cases", "errors"}
            )
            if not public:
                found.append(f"{module} imports {imported}")
    _violations_of("an adapter reaches into another feature's internals", found)


def test_shared_depends_on_no_feature() -> None:
    found = [
        f"{_module(path)} imports {imported}"
        for path in _application_files()
        if _module(path).startswith("shared.")
        for imported in _imports(path)
        if imported.split(".")[0] in (*FEATURES, "config")
    ]
    _violations_of("shared depends on a feature", found)


def test_errors_are_caught_narrowly() -> None:
    found = []
    for path in _python_files():
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.ExceptHandler):
                continue
            caught = node.type
            broad = caught is None or (
                isinstance(caught, ast.Name) and caught.id in {"Exception", "BaseException"}
            )
            if broad:
                found.append(f"{_module(path)}:{node.lineno}")
    _violations_of("a broad except", found)


def test_no_dynamic_access_or_escape_hatch_typing() -> None:
    found = []
    for path in _python_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in FORBIDDEN_BUILTINS
            ):
                found.append(f"{_module(path)}:{node.lineno} calls {node.func.id}")
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                names = {alias.name for alias in node.names} & FORBIDDEN_TYPING
                if names:
                    found.append(f"{_module(path)}:{node.lineno} imports {sorted(names)}")
    _violations_of("dynamic access or escape-hatch typing", found)


def test_code_carries_no_comments() -> None:
    found = []
    for path in [*_python_files(), *BACKEND.glob("*/migrations/*.py")]:
        source = path.read_text()
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        if any(token.type == tokenize.COMMENT for token in tokens):
            found.append(f"{_module(path)} has a comment")
        for node in ast.walk(ast.parse(source)):
            documentable = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            if isinstance(node, documentable) and ast.get_docstring(node) is not None:
                found.append(f"{_module(path)}:{_line_of(node)} has a docstring")
    _violations_of("comments or docstrings", found)


def _line_of(node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    if isinstance(node, ast.Module):
        return 1
    return node.lineno


def test_calls_are_not_nested_inside_calls() -> None:
    found = []
    for path in _application_files():
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
                if not isinstance(argument, ast.Call):
                    continue
                callee = argument.func
                name = callee.id if isinstance(callee, ast.Name) else ""
                if isinstance(callee, ast.Attribute):
                    name = callee.attr
                if name not in ALLOWED_INNER_CALLS and not name[:1].isupper():
                    found.append(f"{_module(path)}:{node.lineno} {ast.unparse(node)[:80]}")
    _violations_of("a call nested inside another call", found)


def test_module_names_describe_a_responsibility() -> None:
    found = [_module(path) for path in _python_files() if path.stem in VAGUE_MODULE_NAMES]
    _violations_of("a vague module name", found)


def test_every_app_has_one_generated_migration() -> None:
    found = []
    for feature in FEATURES:
        migrations = sorted(path.name for path in (BACKEND / feature / "migrations").glob("0*.py"))
        if migrations not in ([], ["0001_initial.py"]):
            found.append(f"{feature}: {migrations}")
    _violations_of("a migration chain instead of one clean baseline", found)
