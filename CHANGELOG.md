# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
