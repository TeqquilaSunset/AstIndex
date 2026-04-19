# AST Index

**Version:** 0.8.0

A structural code search tool that indexes codebases using Abstract Syntax Tree (AST) analysis.

## What's New in 0.8.0

### Bug Fixes

1. **Fixed duplicate symbols from relative/absolute paths** - `Config.__post_init__` now calls `self.root.resolve()`, and `scan_files()` yields `filepath.resolve()`. All symbols stored with canonical absolute paths.
2. **Fixed `functions` returning 0 results without `--limit`** - `search_by_kind()` now uses SQL-level over-query + deduplication instead of fetching all rows.
3. **Fixed `inheritance` showing empty results** - Root cause was duplicate paths; now returns correct hierarchy (e.g., 4 children of `BaseParser`).
4. **241 mypy type errors resolved** - Complete type annotations across all 25 source files.
5. **129 ruff lint errors resolved** - Fixed long lines, unused imports, sorting, comparisons, trailing whitespace.

## What's New in 0.7.0

### Critical Bug Fixes

1. **Fixed path duplication** - All 4 parsers now use resolved absolute paths, preventing duplicate symbols on every `index`/`rebuild`.
2. **Fixed false-positive references** - 66 common method names (`close`, `get`, `set`, etc.) excluded from reference extraction.
3. **Fixed `--file` filter on Windows** - Path separators normalized for cross-platform compatibility.
4. **Fixed case-sensitive search on Windows** - Uses `PRAGMA case_sensitive_like` for correct ASCII case matching.
5. **Fixed `methods` command** - Now accepts optional symbol argument: `ast-index methods Database`.
6. **Fixed duplicate counts in `stats`** - Uses `COUNT(DISTINCT file_path)` for accurate file counts.

## What's New in 0.6.0

### Bug Fixes

1. **Fixed `search --file` filter** - Was filtering in Python after SQL LIMIT, returning 0 results for valid file paths. Now filters at SQL level.
2. **Fixed `usages --file` showing unfiltered definitions** - Definitions are now correctly scoped to filtered context.

### New Features

3. **`definition --limit`** - Limit output when symbol has many definitions (e.g., `ast-index definition "Id" --limit 10`)

### Improvements

4. **`usages` without arguments capped at 50** - No more 131KB output; use `--limit` to override.

## What's New in 0.5.1

### Bug Fixes

1. **Fixed `top`/`usages` crash** - `GROUP_CONCAT(DISTINCT)` incompatible with older SQLite versions, now uses subquery
2. **Fixed `--file` filter in `usages`** - Was using `endswith` instead of substring match
3. **Fixed duplicate search results** - Added deduplication across all search levels (exact, prefix, fuzzy)
4. **Fixed fuzzy returning same results as prefix** - Removed `GROUP BY name` from fuzzy search
5. **Fixed `\r` in usages context** - Windows CRLF now stripped from context lines
6. **Fixed wildcard patterns in fuzzy search** - `*Controller` now works correctly

### Improvements

7. **Warning for ambiguous symbols** - Alerts when `usages` finds 10+ definitions of the same name
8. **Empty context lines skipped** in `usages --show-context` output

## What's New in 0.4.0

### Critical Bug Fixes

1. **Fixed duplicate symbols** - Rewrote parallel indexer to parse-parallel/write-sequential pattern, eliminating concurrent DB writes
2. **Fixed doubled statistics** - Rebuild now uses bulk database clear instead of file-by-file deletion
3. **Fixed "database is locked"** - Added `busy_timeout=5000` and single-threaded write transactions
4. **Fixed inaccurate `top` results** - SQL now properly aggregates files per symbol with `GROUP_CONCAT`

### New Features

5. **`file` command** - Show all symbols in a specific file (`ast-index file PATH`)
6. **`--case-sensitive` flag** for search - Uses `COLLATE BINARY` for exact case matching
7. **`--file` filter** for search - Filter results by file path substring
8. **`--limit` for inheritance and usings** - Truncate results
9. **`definition` shows all matches** - Returns list when multiple definitions exist
10. **Symbol highlighting** in `usages --show-context` - Matches shown as `>>>symbol<<<`

### Improvements

11. **`executemany` for batch inserts** - Faster database writes
12. **Batch transactions** of 100 files - Better write performance
13. **Empty query validation** - Helpful error instead of random results
14. **Wildcard documentation** - Help text explains shell expansion

## Features

- Multi-language support (Python, JavaScript, TypeScript, C#)
- Structural code search (find functions, classes, methods by name/pattern)
- Case-sensitive search for case-sensitive languages
- Symbol usage tracking (find where symbols are referenced/called)
- File-level symbol listing
- SQLite-based index with FTS5 full-text search
- Incremental indexing with file change detection
- Inheritance hierarchy analysis
- JSON output for AI/CI integration

## Installation

### Quick install from source:

```bash
cd /path/to/AstIndex
pip install -e .
```

### Install from wheel:

```bash
cd /path/to/AstIndex/dist
pip install ast_index-0.8.0-py3-none-any.whl
```

## Usage

```bash
# Index a project
ast-index index

# Search for symbols
ast-index search "SymbolName"

# Case-sensitive search (for C# and other case-sensitive languages)
ast-index search "ToString" --case-sensitive

# Search in specific files
ast-index search "Service" --file "Controllers/"

# Search for classes
ast-index class "ClassName"

# Find all usages of a symbol
ast-index usages "SymbolName"

# Find usages with context and highlighting
ast-index usages --show-context "SymbolName"

# Filter usages by file
ast-index usages "SymbolName" --file "path/to/file.cs"

# Show all symbols in a file
ast-index file src/UserService.cs

# Find symbol definition (shows all matches if multiple)
ast-index definition "SymbolName"

# Limit definitions when many exist
ast-index definition "Id" --limit 10

# Analyze inheritance
ast-index inheritance "BaseClass" --direction children

# View index statistics
ast-index stats

# Most referenced symbols (aggregated by file)
ast-index top --limit 20
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

## Symbol Usage Tracking

AST Index includes a **usages** command that finds where symbols are referenced in your codebase. This uses a regex-based approach with the following characteristics:

### What Works Well

- Finds CamelCase type references (classes, interfaces)
- Finds function/method calls
- Filters out language keywords and standard types
- Excludes locally-defined symbols
- Removes comments and string literals from search
- Shows context lines for each reference with symbol highlighting
- Case-sensitive search for case-sensitive languages

### C# Enhancements

For C# projects, AST Index provides enhanced reference extraction:

- **Using Directives Analysis**: Extracts and stores `using` statements
- **Generic Types**: Extracts references to generic types like `List<T>`, `Dictionary<K,V>`
- **Context-Aware Filtering**: Excludes symbols from XML docs, attributes, and string interpolation
- **LINQ Extension Methods**: Identifies common LINQ methods

**Show using directives for a C# file:**
```bash
ast-index usings Models/UserRepository.cs
```

### Known Limitations

The regex-based approach has some limitations:

- **False positives**: May find symbol references in string literals or comments
- **No import resolution**: Doesn't resolve imports/using statements for reference matching
- **No scope awareness**: Doesn't understand variable scope or namespaces
- **Language-specific patterns**: Works best with CamelCase conventions

For more accurate results in complex scenarios, consider using language server protocol (LSP) based tools.
