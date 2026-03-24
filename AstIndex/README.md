# AST Index

A structural code search tool that indexes codebases using Abstract Syntax Tree (AST) analysis.

## Features

- Multi-language support (Python, JavaScript, TypeScript, C#)
- Structural code search (find functions, classes, methods by name/pattern)
- SQLite-based index for fast queries
- Incremental indexing with file change detection

## Installation

```bash
pip install ast-index
```

## Usage

```bash
# Index a project
ast-index index /path/to/project

# Search for functions
ast-index search function "handle.*"

# Search for classes
ast-index search class "User"
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy ast_index
```
