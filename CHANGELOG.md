# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-04-19

### Fixed

- **Duplicate symbols (relative + absolute paths)** - `Config.__post_init__` now calls `self.root.resolve()`, and `scan_files()` yields `filepath.resolve()`. All symbols are stored with canonical absolute paths, eliminating duplicate entries that appeared in `search`, `class`, `methods`, `definition`, `interfaces`, `functions` commands.
- **`functions` returning 0 results without `--limit`** - `search_by_kind()` was fetching all rows via `get_symbols_by_kind()` without SQL `LIMIT` or `ORDER BY`, then slicing in Python with no deduplication. Now uses over-query (`limit * 3`) at SQL level with `ORDER BY name`, followed by `_deduplicate()` — matching the pattern of all other search methods.
- **`inheritance BaseParser` showing empty results** - Root cause was the duplicate path issue: parser files were indexed with both relative and absolute paths. After fixing path canonicalization, inheritance queries return correct results (4 children: CSharpParser, PythonParser, JavaScriptParser, TypeScriptParser).
- **241 mypy type errors resolved** - Added complete type annotations across all 25 source files: `database.py` (`_conn` type narrowed), `search.py` (`_resolver` typed as `SymbolResolver | None`), all 4 parsers (parameter/return types, `str | None` for optional params), `cli.py`, `config.py`, `indexer.py`, `parallel_indexer.py`, `symbol_resolution.py`, `utils/logging.py`, `utils/file_utils.py`.
- **129 ruff lint errors resolved** - Fixed: long lines (SQL statements, docstrings, build script), unused imports, unsorted imports, `== True/False` comparisons in tests, trailing whitespace, missing newlines at EOF, `N806` state machine constants suppressed with `noqa`.

### Changed

- `Database.get_symbols_by_kind()` now accepts optional `limit` parameter with SQL-level `ORDER BY name LIMIT ?`.
- `SearchEngine.search_by_kind()` now applies over-query + deduplication pattern consistent with all other search methods.
- `scan_files()` yields resolved (`Path.resolve()`) paths to prevent relative/absolute path mismatches.
- `Config.__post_init__` canonicalizes `self.root` via `.resolve()`.

### Fixed

- **Path duplication in all parsers** - All 4 parsers (Python, C#, JavaScript, TypeScript) stored symbols with relative paths while cleanup used absolute paths, causing duplicate entries on every `index`/`rebuild`. Now all parsers use `str(file_path.resolve())`.
- **False-positive references for common methods** - `close`, `get`, `set`, `add`, `remove`, `open`, and 60+ other common method names were extracted as symbol references, creating massive noise. Added `COMMON_METHOD_NAMES` exclusion set merged into all language filters.
- **`--file` filter broken on Windows** - `LIKE '%path/%'` didn't match paths with `\` separators. Both `_build_file_clause` (SQL) and `_apply_file_filter` (Python) now normalize separators to `/` before comparison.
- **Case-sensitive search broken on Windows** - SQLite's `LIKE` is ASCII case-insensitive on Windows by default, even with `COLLATE BINARY`. Now enables `PRAGMA case_sensitive_like = ON` during case-sensitive queries.
- **`methods` command listing all methods** - `ast-index methods` had no symbol argument, making it identical to `--kind method`. Now accepts optional `SYMBOL` argument: `ast-index methods Database`.
- **Duplicate file counts in `stats`** - `get_stats()` counted rows in `files` table instead of distinct file paths in `symbols`. Now uses `COUNT(DISTINCT file_path)` for resilience.

### Added

- Test for reference context from stripped content (verifies docstrings don't leak into references).

## [0.6.0] - 2026-04-19

### Fixed

- **`search --file` filter not working** - Root cause: file filter was applied in Python after SQL `LIMIT`, so results were fetched without filtering then truncated. Now filter is applied at SQL level via `AND file_path LIKE ?` in all search paths (exact, prefix, fuzzy, case-sensitive, dot-path).
- **`usages --file` showing all definitions** - Definitions were fetched without file filter, making it appear the filter wasn't working. Definitions in the result dict are now informational only (references are properly filtered).

### Added

- **`definition --limit` option** - Limit number of definitions shown when multiple exist. Previously, symbols like `Id` with 296 definitions would dump all results. Usage: `ast-index definition "Id" --limit 10`.

### Changed

- **`usages` without symbol capped at 50** - Previously used the default `--limit 500`, generating massive output. Now capped at `min(limit, 50)` for the "top referenced symbols" view. Users can still override with `--limit`.
- **`SearchEngine.search()` accepts `file_filter` parameter** - File filtering moved from CLI layer into the search engine, ensuring consistent behavior across all code paths.

## [0.5.1] - 2026-04-18

### Fixed

- **Config root override bug** - `load_config()` now always uses the user-specified root directory instead of overwriting it with `config_file.parent`. Previously, if `.ast-index.yaml` existed in a parent directory, `config.root` was set to that parent, causing all subsequent operations to use wrong paths.
- **`update` command deleting all files** - Root cause: when config root was wrong, `scan_files()` returned 0 files, making `update()` treat all indexed files as deleted. Now correctly preserves unmodified files.
- **`file` command returning 0 results** - Root cause: wrong `config.root` led to wrong `db_path`, querying an empty database. Additionally, `search_in_file()` now falls back to LIKE substring matching when exact path match fails.
- **`index`/`rebuild` returning 0 files with config** - Same root cause as above; `scan_files()` was walking the wrong directory.

## [0.4.1] - 2026-04-18

### Fixed

- **`top`/`usages` crash on older SQLite** - `GROUP_CONCAT(DISTINCT col, sep)` unsupported in SQLite < 3.44.0; replaced with subquery approach
- **`--file` filter in `usages`** - Changed from `endswith()` to substring match (`in`) for consistency with `search --file`
- **Duplicate search results** - Added `_deduplicate()` method applied across all search levels (exact, prefix, fuzzy, case-sensitive)
- **Fuzzy search returning same results as prefix** - Removed `GROUP BY name` from `_fuzzy_search()`, now returns all file-specific matches
- **`\r` in usages context** - Windows CRLF stripped from reference context at extraction time and display time
- **Wildcard patterns in fuzzy search** - `*Controller` pattern now cleaned before LIKE matching

### Added

- **Warning for ambiguous symbols** - `usages` command warns (stderr) when symbol has 10+ definitions
- Empty context lines skipped in `usages --show-context` output

## [0.4.0] - 2026-04-18

### Added

- **`file` command** - Show all symbols in a specific file
  - `ast-index file PATH [--format text|json] [--limit N]`
  - Displays symbol name, kind, line number, and parent

- **`--case-sensitive` flag** for `search` command
  - Uses `COLLATE BINARY` for case-sensitive matching
  - Works with exact and fuzzy search levels

- **`--file` filter** for `search` command
  - Filter search results by file path substring
  - `ast-index search "SymbolName" --file "Controllers/"`

- **`--limit` for `inheritance`** command
  - Truncate children/parents lists (default: 100)

- **`--limit` for `usings`** command
  - Truncate imports, static imports, and aliases (default: 100)

- **Symbol highlighting in `usages --show-context`**
  - Matches highlighted with `>>>symbol<<<` in context output

- Empty query validation for `search` command
  - Helpful error message suggesting to omit query for listing all

### Changed

- **ParallelIndexer rewritten to parse-parallel/write-sequential**
  - Files parsed in ThreadPoolExecutor (CPU-bound)
  - Results written in single-threaded batched transactions (I/O-bound)
  - Eliminates "database is locked" errors
  - Eliminates duplicate symbols from concurrent writes
  - Batch size: 100 files per transaction

- **`rebuild()` uses bulk `Database._clear_all()`** instead of file-by-file deletion
  - Significantly faster rebuild
  - Prevents partial states from concurrent operations

- **`Database` layer improvements**
  - `PRAGMA busy_timeout=5000` for better concurrency
  - `executemany` for `insert_symbols`, `insert_inheritances`, `insert_references`
  - Improved batch insert performance

- **`get_top_symbols` SQL fixed** to properly aggregate files
  - Uses `GROUP_CONCAT(DISTINCT file_path)` with `HAVING reference_count > 0`
  - Returns `file_paths` list instead of single random file
  - `top` command shows aggregated file list

- **`usages` default limit increased** from 100 to 500

- **`definition` shows all matches** when multiple definitions exist
  - Returns list instead of single result
  - Text output shows all definitions with file/line info

- **Wildcard documentation** added to `search` help text

### Fixed

- **#1: Duplicate symbols in output** - Root cause: concurrent DB writes without transactions
- **#2: Doubled statistics after rebuild** - Root cause: file-by-file deletion in `_clear_all`
- **#3: `usages --show-context` shows few results** - Increased limit, added symbol highlighting
- **#7: "database is locked" errors** - Root cause: per-thread DB connections without busy_timeout
- **#8: Empty query returns results** - Added validation to reject empty queries
- **#11: Inaccurate `top` results** - Fixed SQL to properly group by name+kind with file aggregation

## [0.3.0] - 2026-04-12

### Added

- Parallel indexing support with ThreadPoolExecutor
- Progress callback for indexing operations
- `--jobs` and `--no-parallel` CLI options for index command

### Changed

- Improved indexing performance with concurrent file parsing

## [0.2.0] - 2026-04-06

### Added

- **Definition command** - New CLI command for finding symbol definitions with import resolution
  - `ast-index definition SYMBOL [--file PATH] [--format text|json]`
  - Resolves symbols considering using/import directives
  - Supports namespace-aware symbol lookup for C#

- **SymbolResolver module** - Core module for import-aware symbol resolution
  - Scoring system for multiple symbol candidates
  - Namespace extraction from file paths
  - Integration with existing usings table

- **Database enhancements**
  - `Database.get_symbols_by_name_and_namespace()` method
  - Namespace-filtered symbol queries

- **SearchEngine enhancements**
  - `SearchEngine.search_definition()` method
  - Lazy-loaded SymbolResolver integration

- **Comprehensive testing**
  - 4 new test modules for symbol resolution
  - Integration tests for definition command
  - Edge case coverage (not found, multiple candidates)

- **Documentation**
  - Updated CLAUDE.md with definition command
  - New `docs/definition-command.md` with usage examples
  - Architecture documentation for import resolution system

### Changed

- Improved symbol search accuracy with import resolution
- Better handling of ambiguous symbol names

### Fixed

- Namespace extraction for different project structures
- Symbol resolution priority scoring

## [0.1.1] - 2026-04-06

### Added

- C# parser improvements
  - Using directives extraction and storage
  - Generic types reference extraction
  - Context filters for XML docs, attributes, string interpolation
  - LINQ extension method identification

- CLI `usings` command for C# files
- NamespaceMapping model
- Database schema updates (usings table)

### Changed

- Enhanced reference extraction for C# projects
- Improved filtering of false positives

## [0.1.0] - Initial Release

### Added

- Core AST indexing functionality
- Support for Python, JavaScript, TypeScript, C#
- CLI commands: index, search, class, usages, inheritance, stats
- SQLite database with FTS5 full-text search
- Regex-based reference extraction
- Tree-sitter parser integration
