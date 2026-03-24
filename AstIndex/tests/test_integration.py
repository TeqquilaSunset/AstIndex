"""End-to-end integration tests for AST Index."""

import pytest
from pathlib import Path

from ast_index.config import Config
from ast_index.database import Database
from ast_index.indexer import Indexer
from ast_index.search import SearchEngine
from ast_index.utils.file_utils import djb2_hash


class TestDatabaseIntegration:
    """Test database operations."""

    def test_database_create_and_query(self, database):
        """Test basic database operations."""
        from ast_index.models import FileInfo, Symbol

        file_info = FileInfo(
            path="/test/file.py",
            language="python",
            content_hash="abc123",
            last_modified=1000.0,
            size=100,
        )

        database.insert_file(file_info)

        retrieved = database.get_file("/test/file.py")
        assert retrieved is not None
        assert retrieved["language"] == "python"

    def test_symbol_insert_and_search(self, database):
        """Test symbol insertion and FTS search."""
        from ast_index.models import Symbol

        symbol = Symbol(
            name="TestClass",
            kind="class",
            file_path="/test/file.py",
            line_start=1,
            line_end=10,
        )

        database.insert_symbol(symbol)

        results = database.get_symbols_by_name("TestClass")
        assert len(results) == 1
        assert results[0]["name"] == "TestClass"


class TestIndexerIntegration:
    """Test indexer operations."""

    def test_index_python_file(self, indexer, sample_python_file, database):
        """Test indexing a Python file."""
        from ast_index.parsers import get_parser

        parser_cls = get_parser("python")
        assert parser_cls is not None

        parser = parser_cls()
        content = sample_python_file.read_bytes()
        parsed = parser.parse(sample_python_file, content)

        assert parsed is not None
        assert len(parsed.symbols) > 0

        class_symbols = [s for s in parsed.symbols if s.kind == "class"]
        assert len(class_symbols) >= 2  # BaseClass, DerivedClass

        inheritance = parsed.inheritances
        assert len(inheritance) >= 1  # DerivedClass(BaseClass)

    def test_full_index_workflow(self, config, sample_project):
        """Test full indexing workflow."""
        with Indexer(config=config) as indexer:
            stats = indexer.index()

        assert stats["files_indexed"] >= 1
        assert stats["symbols_indexed"] >= 1

    def test_update_workflow(self, config, sample_python_file):
        """Test incremental update workflow."""
        with Indexer(config=config) as indexer:
            stats1 = indexer.index()
            assert stats1["files_indexed"] >= 1

            stats2 = indexer.update()
            assert stats2["files_modified"] == 0

            sample_python_file.write_text(sample_python_file.read_text() + "\n# comment\n")

            stats3 = indexer.update()
            assert stats3["files_modified"] >= 1

    def test_rebuild_workflow(self, config, sample_python_file):
        """Test rebuild (clear and reindex) workflow."""
        with Indexer(config=config) as indexer:
            stats1 = indexer.index()
            assert stats1["files_indexed"] >= 1

            stats2 = indexer.rebuild()
            assert stats2["files_indexed"] >= 1


class TestSearchIntegration:
    """Test search operations."""

    def test_search_after_index(self, config, sample_python_file):
        """Test search after indexing."""
        with Indexer(config=config) as indexer:
            indexer.index()

        with SearchEngine(config=config) as engine:
            results = engine.search("BaseClass", level="exact")

        assert len(results) >= 1
        assert any(r["name"] == "BaseClass" for r in results)

    def test_search_class(self, config, sample_python_file):
        """Test class search."""
        with Indexer(config=config) as indexer:
            indexer.index()

        with SearchEngine(config=config) as engine:
            results = engine.search_class("Derived")

        assert len(results) >= 1

    def test_search_inheritance(self, config, sample_python_file):
        """Test inheritance search."""
        with Indexer(config=config) as indexer:
            indexer.index()

        with SearchEngine(config=config) as engine:
            results = engine.search_inheritance("BaseClass", direction="children")

        assert "children" in results
        assert len(results["children"]) >= 1


class TestConfigIntegration:
    """Test configuration."""

    def test_config_defaults(self, temp_dir):
        """Test config with defaults."""
        config = Config(root=temp_dir)

        assert config.root == temp_dir
        assert "*.py" in config.includes
        assert "node_modules" in config.excludes

    def test_load_save_config(self, temp_dir):
        """Test loading and saving config."""
        from ast_index.config import load_config, save_config

        config = Config(root=temp_dir, includes=["*.py"])
        save_config(config)

        loaded = load_config(temp_dir)
        assert "*.py" in loaded.includes


class TestFileUtils:
    """Test file utilities."""

    def test_djb2_hash(self):
        """Test djb2 hash function."""
        result = djb2_hash(b"test")
        assert isinstance(result, str)
        assert len(result) > 0

        result2 = djb2_hash(b"test")
        assert result == result2

        result3 = djb2_hash(b"different")
        assert result != result3

    def test_scan_files(self, temp_dir, sample_python_file, sample_javascript_file):
        """Test file scanning."""
        from ast_index.utils.file_utils import scan_files

        files = list(
            scan_files(
                temp_dir,
                includes=["*.py", "*.js"],
                excludes=["node_modules"],
            )
        )

        assert len(files) >= 2

        languages = {lang for _, lang in files}
        assert "python" in languages
        assert "javascript" in languages
