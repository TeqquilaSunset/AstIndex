from dataclasses import dataclass, field
from pathlib import Path

import yaml  # type: ignore[import-untyped]

DEFAULT_EXCLUDES = [
    "node_modules",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    # C# specific
    "bin",
    "obj",
    ".vs",
    ".vscode",
    "publish",
]

DEFAULT_INCLUDES = ["*.py", "*.cs", "*.js", "*.ts", "*.tsx"]


@dataclass
class Config:
    root: Path
    includes: list[str] = field(default_factory=lambda: DEFAULT_INCLUDES.copy())
    excludes: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDES.copy())
    database_path: str | None = None
    languages: list[str] = field(
        default_factory=lambda: ["python", "csharp", "javascript", "typescript"]
    )

    def __post_init__(self) -> None:
        if isinstance(self.root, str):
            self.root = Path(self.root)
        self.root = self.root.resolve()
        if self.database_path is None:
            self.database_path = str(self.root / ".ast-index.db")

    @property
    def db_path(self) -> str:
        return self.database_path or str(self.root / ".ast-index.db")


def find_config_file(start_path: Path | None = None) -> Path | None:
    """Find .ast-index.yaml by traversing up from start_path."""
    if start_path is None:
        start_path = Path.cwd()
    elif isinstance(start_path, str):
        start_path = Path(start_path)

    current = start_path.resolve()
    while current != current.parent:
        config_file = current / ".ast-index.yaml"
        if config_file.exists():
            return config_file
        current = current.parent

    config_file = current / ".ast-index.yaml"
    if config_file.exists():
        return config_file

    return None


def load_config(root: Path | None = None) -> Config:
    """Load configuration from .ast-index.yaml or return defaults."""
    if root is None:
        root = Path.cwd()
    elif isinstance(root, str):
        root = Path(root)

    resolved_root = root.resolve()
    config_file = find_config_file(resolved_root)

    if config_file:
        with open(config_file) as f:
            data = yaml.safe_load(f) or {}

        return Config(
            root=resolved_root,
            includes=data.get("includes", DEFAULT_INCLUDES.copy()),
            excludes=data.get("excludes", DEFAULT_EXCLUDES.copy()),
            database_path=data.get("database_path"),
            languages=data.get("languages", ["python", "csharp", "javascript", "typescript"]),
        )

    return Config(root=resolved_root)


def save_config(config: Config, path: Path | None = None) -> None:
    """Save configuration to .ast-index.yaml."""
    if path is None:
        path = config.root / ".ast-index.yaml"
    elif isinstance(path, str):
        path = Path(path)

    data: dict[str, list[str] | str] = {
        "includes": config.includes,
        "excludes": config.excludes,
        "languages": config.languages,
    }
    if config.database_path:
        data["database_path"] = config.database_path

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
