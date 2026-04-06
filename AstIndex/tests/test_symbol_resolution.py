"""Tests for symbol resolution module."""

import pytest
from ast_index.symbol_resolution import SymbolResolver
from ast_index.database import Database
from ast_index.models import Symbol


def test_resolve_symbol_with_usings(db_path, sample_csharp_project):
    """Test resolving symbol with using directives."""
    db = Database(db_path)

    # Setup: insert test data
    symbol = Symbol(
        name="UserRepository",
        kind="class",
        file_path="/project/Models/UserRepository.cs",
        line_start=10,
        line_end=50
    )
    db.insert_symbol(symbol)

    # Insert usings
    db._conn.execute(
        "INSERT INTO usings (file_path, namespace, is_static) VALUES (?, ?, 0)",
        ("/project/Controllers/HomeController.cs", "App.Models",)
    )
    db._conn.commit()

    # Test
    resolver = SymbolResolver(db)
    result = resolver.resolve_symbol(
        symbol_name="UserRepository",
        reference_file="/project/Controllers/HomeController.cs"
    )

    assert result is not None
    assert result["name"] == "UserRepository"
    assert result["file_path"] == "/project/Models/UserRepository.cs"


def test_resolve_symbol_not_found(db_path):
    """Test resolving non-existent symbol."""
    from ast_index.database import Database
    from ast_index.symbol_resolution import SymbolResolver

    db = Database(db_path)
    resolver = SymbolResolver(db)

    result = resolver.resolve_symbol(
        symbol_name="NonExistentClass",
        reference_file="/project/File.cs"
    )

    assert result is None


def test_resolve_symbol_multiple_candidates(db_path):
    """Test resolving symbol with multiple definitions."""
    from ast_index.database import Database
    from ast_index.symbol_resolution import SymbolResolver

    db = Database(db_path)

    # Setup: multiple symbols with same name
    symbol1 = Symbol(
        name="User",
        kind="class",
        file_path="/project/Models/User.cs",
        line_start=1,
        line_end=10
    )
    symbol2 = Symbol(
        name="User",
        kind="class",
        file_path="/project/DTO/User.cs",
        line_start=1,
        line_end=10
    )

    db.insert_symbol(symbol1)
    db.insert_symbol(symbol2)

    # Add usings
    db._conn.execute(
        "INSERT INTO usings (file_path, namespace, is_static) VALUES (?, ?, 0)",
        ("/project/Controllers/HomeController.cs", "App.Models",)
    )
    db._conn.commit()

    # Test
    resolver = SymbolResolver(db)
    result = resolver.resolve_symbol(
        symbol_name="User",
        reference_file="/project/Controllers/HomeController.cs"
    )

    assert result is not None
    assert result["file_path"] == "/project/Models/User.cs"
