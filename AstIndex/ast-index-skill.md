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

### 1. **index** - Create/update project index
```bash
ast-index index [--root PATH] [--format text|json]
```

### 2. **update** - Incremental update (changed files only)
```bash
ast-index update [--root PATH]
```

### 3. **search** - Find symbols by name/pattern
```bash
ast-index search QUERY [--level exact|prefix|fuzzy] [--limit N]
```

### 4. **usages** - Find all symbol usages/references
```bash
ast-index usages SYMBOL [--show-context] [--file PATH] [--limit N]
```

### 5. **inheritance** - Show inheritance hierarchy
```bash
ast-index inheritance SYMBOL [--direction children|parents|both]
```

### 6. **stats** - Index statistics
```bash
ast-index stats
```

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
# After small changes (faster)
ast-index update

# After major refactoring (complete rebuild)
ast-index rebuild
```

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
3. Find usages: `ast-index usages --show-context SymbolName`
4. Analyze patterns: `ast-index search "*Pattern*" --level prefix`

### For Refactoring
1. **Before:** `ast-index usages --show-context OldSymbol`
2. **After changes:** `ast-index update`
3. **Verify:** `ast-index usages NewSymbol`

### For Documentation
1. Find main classes: `ast-index search "*" --limit 100`
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
ast-index usages MethodName                  # Find calls
ast-index usages --show-context MethodName   # Find with context
ast-index search "ClassName"                 # Find symbol
ast-index inheritance ClassName             # Show hierarchy
ast-index stats                              # Show statistics
```
