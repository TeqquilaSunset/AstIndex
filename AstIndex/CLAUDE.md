# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

```bash
# Install dependencies (development mode)
pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test file or test
pytest tests/test_integration.py
pytest tests/test_integration.py -k test_index

# Run tests with coverage report
pytest --cov=ast_index --cov-report=term-missing

# Linting
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Type checking
mypy ast_index
```

## Architecture Overview

**AST Index** is a structural code search tool that indexes codebases using Abstract Syntax Tree (AST) analysis via tree-sitter parsers. The system stores symbols in SQLite with FTS5 full-text search for fast queries.

### Core Components

- **Parsers** (`ast_index/parsers/`): Tree-sitter based parsers for Python, C#, JavaScript, and TypeScript
  - Uses automatic registration via `__init_subclass__` pattern
  - Each parser inherits from `BaseParser` and implements `parse()` and `can_parse()`

- **Database** (`ast_index/database.py`): SQLite operations with FTS5 full-text search
  - Schema: files, symbols, symbols_fts, inheritance, refs, metadata tables
  - Database location: `~/.cache/ast-index/{project_hash}/index.db`
  - Uses djb2 hash for project path

- **Indexer** (`ast_index/indexer.py`): Main indexing logic with batch processing
  - Processes files in batches of 500 (BATCH_SIZE)
  - Supports incremental updates (detects new/modified/deleted files)
  - Concurrent parsing with thread pool

- **Search Engine** (`ast_index/search.py`): Three-level search strategy
  1. Exact match (SELECT WHERE name = 'Symbol')
  2. Prefix search via FTS5 (MATCH 'Sym*')
  3. Fuzzy search via LIKE (LIKE '%Symbol%')

- **CLI** (`ast_index/cli.py`): Click-based command interface
  - Commands: index, update, rebuild, search, class, usages, inheritance, stats
  - All commands support `--format json` for AI integration

### Constants and Limits

- `BATCH_SIZE = 500` - Files processed per transaction
- `MAX_FILE_SIZE = 10MB` - Skip files larger than this
- Languages: Python, C#, JavaScript, TypeScript

### Data Flow

1. **Indexing**: Scan files → Parse with language-specific parsers → Extract symbols/inheritance/refs → Store in SQLite
2. **Searching**: Query → SearchEngine (3-level strategy) → Return results
3. **Updates**: Compare file mtimes → Parse changed files → Update database incrementally

### Language Parsers

All parsers follow the same pattern:
- Parse using tree-sitter grammar
- Extract: classes, functions, methods, interfaces, inheritance relationships
- Return `ParsedFile` with symbols, inheritances, and references

**Parser Registry**: Use `BaseParser.get_parser(language)` to get the appropriate parser class.

### Testing

- Tests use pytest fixtures in `tests/conftest.py`
- Test fixtures are in `tests/fixtures/` directory
- Integration tests cover full workflow: index → search → update → rebuild

### Configuration

- Project detection via `project_detection.py` using marker files (.csproj, package.json, etc.)
- Config file: `.ast-index.yaml` in project root (optional)
- Supports custom includes/excludes and language overrides
