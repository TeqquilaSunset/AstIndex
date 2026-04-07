#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for AST Index CLI tool.

Creates standalone executable for Windows.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and print output."""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Error: {description} failed with return code {result.returncode}")
        sys.exit(1)
    return result


def build_wheel():
    """Build wheel package."""
    print("\n[Building] wheel package...")
    run_command("python -m build", "Build wheel")
    print("\n[Success] Wheel package built successfully!")
    print("[Location] dist/")
    ls_dist = run_command("dir dist\\*.whl", "List wheel files")
    return ls_dist


def build_installer_script():
    """Create installation script."""
    script_content = """@echo off
REM AST Index Installation Script

echo Installing AST Index CLI tool...
python -m pip install --upgrade ast_index-0.1.1-py3-none-any.whl

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Installation complete!
    echo.
    echo You can now use: ast-index --help
) else (
    echo.
    echo [ERROR] Installation failed!
    echo Make sure Python 3.10+ is installed and in PATH.
)

pause
"""
    with open("dist/install.bat", "w") as f:
        f.write(script_content)
    print("\n[Success] Created installation script: dist/install.bat")


def create_portable_script():
    """Create portable Python script wrapper."""
    script_content = """@echo off
REM AST Index Portable Script

set SCRIPT_DIR=%~dp0
set PYTHONPATH=%SCRIPT_DIR%%PYTHONPATH%

python -c "import sys; sys.path.insert(0, r'%SCRIPT_DIR%'); from ast_index.cli import cli; cli()" %*

"""
    with open("dist/ast-index-portable.bat", "w") as f:
        f.write(script_content)
    print("\n[Success] Created portable script: dist/ast-index-portable.bat")


def create_readme():
    """Create installation README."""
    readme_content = """# AST Index - Installation Guide

## Method 1: Install from Wheel (Recommended)

1. Install Python 3.10+ from https://www.python.org
2. Run: `install.bat`
3. Use: `ast-index --help`

## Method 2: Install with pip

```bash
pip install ast_index-0.1.1-py3-none-any.whl
```

## Method 3: Portable Usage

1. Extract the entire dist folder
2. Run: `ast-index-portable.bat <command>`
   Example: `ast-index-portable.bat index`

## Usage Examples

```bash
# Index a project
ast-index index

# Search for symbols
ast-index search "User*"

# Find definition with import resolution
ast-index definition UserRepository --file Controllers/HomeController.cs

# Find usages
ast-index usages MyClass --show-context

# Show using directives (C#)
ast-index usings Models/UserRepository.cs

# Show inheritance hierarchy
ast-index inheritance BaseController
```

## Uninstallation

```bash
pip uninstall ast-index
```

## Troubleshooting

1. Make sure Python 3.10+ is in your PATH
2. If tree-sitter parsers fail to load, reinstall dependencies:
   ```bash
   pip install --upgrade tree-sitter tree-sitter-python tree-sitter-c-sharp tree-sitter-javascript tree-sitter-typescript
   ```

## Features

- Fast symbol search using AST analysis
- Support for Python, C#, JavaScript, TypeScript
- Import resolution for C# using directives
- Full-text search with FTS5
- Find usages and definitions
- Inheritance hierarchy analysis
"""
    with open("dist/README.md", "w") as f:
        f.write(readme_content)
    print("\n[Success] Created README: dist/README.md")


def main():
    """Main build process."""
    print("="*60)
    print("AST Index Build Script")
    print("="*60)

    # Create dist directory
    Path("dist").mkdir(exist_ok=True)

    # Build wheel
    build_wheel()

    # Copy ast_index folder to dist for portable usage
    print("\n[Copying] source files for portable usage...")
    run_command("xcopy /E /I /Y ast_index dist\\ast_index", "Copy source files")
    run_command("copy /Y pyproject.toml dist\\", "Copy pyproject.toml")

    # Create helper files
    build_installer_script()
    create_portable_script()
    create_readme()

    print("\n" + "="*60)
    print("Build Complete!")
    print("="*60)
    print("\nDistribution files created in dist/:")
    print("  - ast_index-0.1.1-py3-none-any.whl (Wheel package)")
    print("  - install.bat (Installation script)")
    print("  - ast-index-portable.bat (Portable wrapper)")
    print("  - ast_index/ (Source files for portable usage)")
    print("  - README.md (Installation instructions)")
    print("\nTo install:")
    print("  1. Copy the dist/ folder to target machine")
    print("  2. Run install.bat")
    print("  3. Use: ast-index --help")


if __name__ == "__main__":
    main()
