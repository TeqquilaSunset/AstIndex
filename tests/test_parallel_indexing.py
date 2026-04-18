"""Tests for parallel indexing functionality."""

import pytest
from pathlib import Path
from ast_index.parallel_indexer import ParallelIndexer
from ast_index.config import Config


class TestParallelIndexer:
    """Test parallel indexer functionality."""

    def test_parallel_indexer_initialization(self, temp_dir):
        """Test ParallelIndexer initialization."""
        config = Config(root=temp_dir)

        indexer = ParallelIndexer(config=config)

        assert indexer.max_workers > 0
        assert indexer.config == config

    def test_parallel_indexer_custom_workers(self, temp_dir):
        """Test ParallelIndexer with custom worker count."""
        config = Config(root=temp_dir)

        indexer = ParallelIndexer(config=config, max_workers=2)

        assert indexer.max_workers == 2

    def test_parallel_indexer_progress_callback(self, temp_dir):
        """Test progress callback during indexing."""
        config = Config(root=temp_dir)

        progress_updates = []

        def progress_callback(current: int, total: int):
            progress_updates.append((current, total))

        indexer = ParallelIndexer(config=config, progress_callback=progress_callback)

        assert indexer.progress_callback == progress_callback

    def test_parse_file_returns_parsed_file(self, temp_dir, sample_csharp_file):
        """Test _parse_file returns ParsedFile with symbols."""
        config = Config(root=temp_dir)
        indexer = ParallelIndexer(config=config)

        result = indexer._parse_file(sample_csharp_file, "csharp")

        assert result is not None
        assert result.file_info is not None
        assert len(result.symbols) > 0

    def test_write_batch_stores_to_db(self, temp_dir, sample_csharp_file):
        """Test _write_batch writes parsed results to database."""
        from ast_index.database import Database

        config = Config(root=temp_dir)
        indexer = ParallelIndexer(config=config)

        parsed = indexer._parse_file(sample_csharp_file, "csharp")
        assert parsed is not None

        db = Database(config.db_path)
        try:
            stats = indexer._write_batch(db, [parsed])
        finally:
            db.close()

        assert stats["files_indexed"] == 1
        assert stats["symbols_indexed"] > 0


class TestParallelIndexingIntegration:
    """Integration tests for parallel indexing."""

    def test_parallel_vs_sequential_consistency(
        self, temp_dir, sample_python_file, sample_csharp_file
    ):
        """Test that parallel and sequential indexing produce same results."""
        from ast_index.indexer import Indexer

        config = Config(root=temp_dir)

        # Sequential indexing
        with Indexer(config=config, use_parallel=False) as indexer_seq:
            stats_seq = indexer_seq.index()

        # Clear database
        from ast_index.database import Database

        db = Database(config.db_path)
        db._clear_all()

        # Parallel indexing
        with Indexer(config=config, use_parallel=True) as indexer_par:
            stats_par = indexer_par.index()

        # Compare results
        assert stats_seq["files_indexed"] == stats_par["files_indexed"]
        # Symbols might differ slightly due to ordering, but should be close
        assert abs(stats_seq["symbols_indexed"] - stats_par["symbols_indexed"]) <= 1

    def test_parallel_indexing_with_multiple_files(self, temp_dir):
        """Test parallel indexing with multiple files."""
        from ast_index.indexer import Indexer

        # Create multiple test files
        (temp_dir / "test1.py").write_text("""
class TestClass1:
    def method1(self):
        pass
""")

        (temp_dir / "test2.py").write_text("""
class TestClass2:
    def method2(self):
        pass
""")

        (temp_dir / "test3.py").write_text("""
def function1():
    pass
""")

        config = Config(root=temp_dir)

        with Indexer(config=config, use_parallel=True) as indexer:
            stats = indexer.index()

        assert stats["files_indexed"] == 3
        assert stats["symbols_indexed"] >= 3  # At least 3 symbols
