---
name: code-search-ast-index
description: Structural code search and symbol usage tracking with AST Index tool for efficient codebase navigation
type: reference
---

# AST Index - Structural Code Search Skill

## Overview

AST Index is a structural code search tool that indexes codebases using Abstract Syntax Tree (AST) analysis. It provides fast symbol search, usage tracking, and inheritance hierarchy analysis for Python, JavaScript, TypeScript, and C# codebases.

## When to Use This Skill

Use AST Index when you need to:
- Find where a symbol (class, method, function) is used/called
- Navigate codebase by symbol names rather than text search
- Understand inheritance hierarchies
- Get statistics about codebase structure
- Search for symbols by pattern (regex-style)

**NOT for:**
- Text-based content search (use grep/ripgrep)
- Semantic code understanding (use LSP/cody)
- Runtime behavior analysis

## Prerequisites

Project must be indexed first:
```bash
cd /path/to/project
ast-index index
```

## Available Commands

### 1. **init** - Initialize project with default config
```bash
ast-index init [--root PATH]
```
Creates `.ast-index.yaml` with default configuration for the project.

### 2. **index** - Create full project index
```bash
ast-index index [--root PATH] [--format text|json] [--jobs N]
```
Performs complete indexing of all files in the project. Use for first-time indexing or after major changes.

### 3. **update** - Incremental update (changed files only)
```bash
ast-index update [--root PATH]
```
Updates index by processing only new/modified/deleted files since last index. **Faster than full indexing** - use after code changes.

### 4. **rebuild** - Rebuild index from scratch
```bash
ast-index rebuild [--root PATH]
```
Clears existing index and performs complete reindexing. Use after major refactoring or if index becomes corrupted.

### 5. **search** - Find symbols by name/pattern
```bash
ast-index search [QUERY] [--level exact|prefix|fuzzy] [--limit N]
```
If QUERY is not provided, lists all symbols.

### 6. **usages** - Find all symbol usages/references
```bash
ast-index usages [SYMBOL] [--show-context] [--file PATH] [--limit N]
```
If SYMBOL is not provided, shows most referenced symbols (top-N).

### 7. **inheritance** - Show inheritance hierarchy
```bash
ast-index inheritance SYMBOL [--direction children|parents|both]
```

### 8. **stats** - Index statistics
```bash
ast-index stats
```

### 9. **definition** - Find symbol definition with import resolution
```bash
ast-index definition SYMBOL [--file PATH]
```

### 10. **class** - Search for class/interface definitions
```bash
ast-index class [NAME] [--limit N]
```
If NAME is not provided, lists all classes.

### 11. **methods** - List all methods
```bash
ast-index methods [--limit N]
```

### 12. **functions** - List all functions
```bash
ast-index functions [--limit N]
```

### 13. **interfaces** - List all interfaces
```bash
ast-index interfaces [--limit N]
```

### 14. **types** - List all type aliases
```bash
ast-index types [--limit N]
```

### 15. **top** - Show most referenced symbols
```bash
ast-index top [--limit N]
```

### 16. **kinds** - List all symbol kinds in project
```bash
ast-index kinds
```
Finds the definition of a symbol. Use `--file` to specify which file is using the symbol (helps resolve which definition when multiple exist).

### 10. **class** - Search for class/interface definitions
```bash
ast-index class [NAME] [--limit N]
```
If NAME is not provided, lists all classes in the index.

## Common Workflows

### Finding Method/Function Calls

**Task:** Find all places where a method is called

```bash
# Basic usage search
ast-index usages methodName

# With context (shows actual code lines)
ast-index usages --show-context methodName

# Filter by specific file
ast-index usages --file UserService.cs methodName

# Limit results
ast-index usages --limit 20 methodName
```

### Understanding Class Hierarchy

**Task:** Explore inheritance relationships

```bash
# Find all children (subclasses)
ast-index inheritance BaseController --direction children

# Find all parents (base classes/interfaces)
ast-index inheritance UserService --direction parents

# Both directions (full hierarchy)
ast-index inheritance UserService --direction both
```

### Searching for Symbols

**Task:** Find symbols by pattern

```bash
# Exact match
ast-index search "UserService"

# Prefix search (UserService, UserValidator, etc.)
ast-index search "User*" --level prefix

# Fuzzy search (contains "User")
ast-index search "User" --level fuzzy

# Pattern search (regex)
ast-index search "get.*User" --level fuzzy
```

### Codebase Exploration

**Task:** Get overview of codebase structure

```bash
# Get statistics
ast-index stats

# Output:
# files: 150
# symbols: 2340
# inheritances: 85
# references: 5670

# List all classes (first 50)
ast-index class

# List all classes with custom limit
ast-index class --limit 100

# Find all classes in a module
ast-index search "Repository*" --level prefix

# Find all test files/classes
ast-index search "*Test*" --level fuzzy
```

### Impact Analysis

**Task:** Understand impact of changing a symbol

```bash
# 1. Find all usages with context
ast-index usages --show-context SymbolName

# 2. Check inheritance (if class/interface)
ast-index inheritance SymbolName --direction both

# 3. Search for related symbols
ast-index search "SymbolName.*" --level prefix
```

## Best Practices

### 1. **Always Index First**
Before searching, ensure the project is indexed:
```bash
ast-index index  # or ast-index update if already indexed
```

### 2. **Use --show-context for Impact Analysis**
When analyzing changes, always see the context:
```bash
ast-index usages --show-context methodName
```

### 3. **Leverage Pattern Matching**
Use patterns instead of exact names when exploring:
```bash
# Find all handlers
ast-index search "*Handler" --level prefix

# Find all repositories
ast-index search "*Repository" --level prefix
```

### 4. **Combine with Other Tools**

**With grep/ripgrep:**
```bash
# First find symbol with AST Index
ast-index usages processData

# Then search for related strings
grep -r "processData" --include="*.py" .
```

**With git log:**
```bash
# Find who last modified the symbol
ast-index search symbolName
git log -p --all -S "symbolName" -- "*.py"
```

### 5. **Keep Index Updated**

After code changes:
```bash
# After small changes (faster - only processes changed files)
ast-index update

# After major refactoring (complete rebuild)
ast-index rebuild

# First time indexing
ast-index init      # Create config file (optional)
ast-index index     # Build initial index
```

**When to use each command:**
- **`init`**: First time setting up a project (creates `.ast-index.yaml`)
- **`index`**: First time indexing or when you want to rebuild everything
- **`update`**: After regular code changes (fast - only processes changed files)
- **`rebuild`**: When index is corrupted or after massive refactoring

## Limitations

### AST Index Limitations
- **No import resolution:** May find references to symbols with same name from different modules
- **No scope awareness:** Doesn't distinguish between local/remote symbols
- **Language-specific:** Works best with CamelCase conventions
- **False positives:** Some string literals/comments may match (partially mitigated)
- **False negatives:** snake_case symbols without calls may be missed

### When to Use Other Tools

| Task | Tool | Why |
|------|------|-----|
| Semantic understanding | LSP/Cody | Full type info, import resolution |
| Text content search | grep/ripgrep | Raw text search |
| Runtime behavior | Debugger | Actual execution flow |
| Git history | git log/blame | Change tracking |

## Examples

### Example 1: Refactoring a Method

```bash
# 1. Find all usages
ast-index usages --show-context oldMethodName

# 2. Check if it's overridden
ast-index inheritance oldMethodName --direction children

# 3. After refactoring, update index
ast-index update

# 4. Verify new method is found
ast-index usages newMethodName
```

### Example 2: Understanding a Codebase

```bash
# 1. Get overview
ast-index stats

# 2. Find main entry points
ast-index search "main" --level fuzzy

# 3. Explore controllers
ast-index search "*Controller" --level prefix

# 4. Check inheritance
ast-index inheritance BaseController --direction children

# 5. Find usages of specific service
ast-index usages --show-context AuthService
```

### Example 3: Finding Test Coverage

```bash
# Find all test classes
ast-index search "*Test*" --level fuzzy

# Check if a class has tests
ast-index usages --show-context UserService
# Look for results containing "Test"

# Find test methods
ast-index search "test_*" --level prefix
```

## Integration with AI Workflows

### For Code Analysis
1. Index the project: `ast-index index`
2. Get symbol info: `ast-index search SymbolName`
3. List all classes: `ast-index class --limit 100`
4. Find usages: `ast-index usages --show-context SymbolName`
5. Analyze patterns: `ast-index search "*Pattern*" --level prefix`

### For Refactoring
1. **Before:** `ast-index usages --show-context OldSymbol`
2. **After changes:** `ast-index update`
3. **Verify:** `ast-index usages NewSymbol`

### For Documentation
1. Find main classes: `ast-index class --limit 100`
2. Get inheritance: `ast-index inheritance ClassName --direction both`
3. Find public APIs: `ast-index search "public*" --level prefix`

## Troubleshooting

### No results found
```bash
# Check if indexed
ast-index stats

# If symbols=0, reindex
ast-index rebuild
```

### Database location
- **Linux/Mac:** `~/.cache/ast-index/{project_hash}/index.db`
- **Windows:** `%USERPROFILE%\.cache\ast-index\{project_hash}\index.db`

### Slow indexing
- Large codebases (>10k files): Expected to take several minutes
- Consider `.ast-index.yaml` configuration to exclude unnecessary files

## Quick Reference

```bash
# Most common commands
ast-index index                              # Index project
ast-index search [QUERY]                     # Search symbols (all if no query)
ast-index usages [SYMBOL]                    # Find usages (top if no symbol)
ast-index class [NAME]                       # List/search classes
ast-index methods                            # List all methods
ast-index functions                          # List all functions
ast-index interfaces                         # List all interfaces
ast-index top                                # Most referenced symbols
ast-index kinds                              # Symbol kinds in project
ast-index stats                              # Show statistics
```
