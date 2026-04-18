from ast_index.database import Database
from ast_index.models import Reference


class TestLimitInUsages:
    def test_get_usages_with_limit(self, db_path):
        db = Database(db_path)
        try:
            refs = [
                Reference(
                    symbol_name="TestSym",
                    symbol_file="/test/a.py",
                    ref_file=f"/test/file_{i}.py",
                    ref_line=i,
                    ref_col=0,
                    ref_kind="usage",
                    context=f"ref {i}",
                )
                for i in range(20)
            ]
            db.insert_references(refs)

            limited = db.get_usages("TestSym", limit=5)
            assert len(limited) == 5

            all_refs = db.get_usages("TestSym")
            assert len(all_refs) == 20
        finally:
            db.close()

    def test_get_usages_count(self, db_path):
        db = Database(db_path)
        try:
            refs = [
                Reference(
                    symbol_name="TestSym",
                    symbol_file="/test/a.py",
                    ref_file=f"/test/file_{i}.py",
                    ref_line=i,
                    ref_col=0,
                    ref_kind="usage",
                )
                for i in range(20)
            ]
            db.insert_references(refs)

            count = db.get_usages_count("TestSym")
            assert count == 20
        finally:
            db.close()

    def test_search_usages_passes_limit(self, db_path):
        from ast_index.search import SearchEngine

        db = Database(db_path)
        try:
            refs = [
                Reference(
                    symbol_name="TestSym",
                    symbol_file="/test/a.py",
                    ref_file=f"/test/file_{i}.py",
                    ref_line=i,
                    ref_col=0,
                    ref_kind="usage",
                )
                for i in range(20)
            ]
            db.insert_references(refs)
        finally:
            db.close()

        engine = SearchEngine(db_path=db_path)
        try:
            result = engine.search_usages("TestSym", limit=5)
            assert len(result["references"]) == 5
        finally:
            engine.close()

    def test_get_usages_with_file_filter(self, db_path):
        db = Database(db_path)
        try:
            refs = [
                Reference(
                    symbol_name="TestSym",
                    symbol_file="/test/a.py",
                    ref_file=f"/test/dir_{i // 10}/file_{i}.py",
                    ref_line=i,
                    ref_col=0,
                    ref_kind="usage",
                )
                for i in range(30)
            ]
            db.insert_references(refs)

            filtered = db.get_usages("TestSym", file_filter="dir_1")
            assert len(filtered) == 10
            for r in filtered:
                assert "dir_1" in r["ref_file"]
        finally:
            db.close()

    def test_get_usages_with_limit_and_file_filter(self, db_path):
        db = Database(db_path)
        try:
            refs = [
                Reference(
                    symbol_name="TestSym",
                    symbol_file="/test/a.py",
                    ref_file=f"/test/dir_1/file_{i}.py",
                    ref_line=i,
                    ref_col=0,
                    ref_kind="usage",
                )
                for i in range(20)
            ]
            db.insert_references(refs)

            filtered = db.get_usages("TestSym", limit=5, file_filter="dir_1")
            assert len(filtered) == 5
        finally:
            db.close()

    def test_cli_usages_showing_count_message(self, temp_dir):
        from click.testing import CliRunner

        from ast_index.cli import cli
        from ast_index.config import Config
        from ast_index.database import Database

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        refs = [
            Reference(
                symbol_name="TestSym",
                symbol_file="/test/a.py",
                ref_file=f"/test/file_{i}.py",
                ref_line=i,
                ref_col=0,
                ref_kind="usage",
            )
            for i in range(20)
        ]
        db.insert_references(refs)
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["usages", "TestSym", "--root", str(temp_dir), "--limit", "5"],
        )
        assert result.exit_code == 0
        assert "showing 5 of 20" in result.output
