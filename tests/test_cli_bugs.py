from ast_index.database import Database
from ast_index.models import Reference, Symbol
from ast_index.search import SearchEngine


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


class TestKindFilter:
    def test_search_with_kind_filter(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Handler",
                kind="class",
                file_path="/test/handler.py",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Handler",
                kind="function",
                file_path="/test/utils.py",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Handler", limit=50, level="exact", kind="class")
        assert len(results) == 1
        assert results[0]["kind"] == "class"
        engine.close()

    def test_search_with_kind_none_returns_all(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Processor",
                kind="class",
                file_path="/test/a.py",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Processor",
                kind="method",
                file_path="/test/b.py",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Processor", limit=50, level="exact", kind=None)
        assert len(results) == 2
        engine.close()

    def test_cli_search_with_kind(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        db.insert_symbol(
            Symbol(
                name="Processor",
                kind="class",
                file_path="/test/proc.py",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Processor",
                kind="method",
                file_path="/test/proc.py",
                line_start=11,
                line_end=15,
            )
        )
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "search",
                "Processor",
                "--root",
                str(temp_dir),
                "--kind",
                "class",
            ],
        )
        assert result.exit_code == 0
        assert "class" in result.output

    def test_cli_usages_with_kind(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        db.insert_symbol(
            Symbol(
                name="doWork",
                kind="method",
                file_path="/test/a.py",
                line_start=1,
                line_end=5,
            )
        )
        db.insert_symbol(
            Symbol(
                name="doWork",
                kind="function",
                file_path="/test/b.py",
                line_start=1,
                line_end=5,
            )
        )
        db.insert_references(
            [
                Reference("doWork", "/test/a.py", "/test/c.py", 10, 0, "usage"),
                Reference("doWork", "/test/b.py", "/test/c.py", 20, 0, "usage"),
            ]
        )
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "usages",
                "doWork",
                "--root",
                str(temp_dir),
                "--kind",
                "method",
            ],
        )
        assert result.exit_code == 0

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


class TestDeduplication:
    def test_search_deduplicates_within_limit(self, db_path):
        db = Database(db_path)
        for i in range(10):
            db.insert_symbol(
                Symbol(
                    name="DupClass",
                    kind="class",
                    file_path="/test/file.py",
                    line_start=i,
                    line_end=i + 1,
                )
            )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("DupClass", limit=5, level="exact")
        assert len(results) == 1
        engine.close()

    def test_search_class_deduplicates(self, db_path):
        db = Database(db_path)
        for i in range(10):
            db.insert_symbol(
                Symbol(
                    name="DupService",
                    kind="class",
                    file_path="/test/service.py",
                    line_start=i,
                    line_end=i + 1,
                )
            )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search_class("DupService", limit=5)
        assert len(results) == 1
        engine.close()

    def test_search_returns_up_to_limit_unique(self, db_path):
        db = Database(db_path)
        for letter in "ABCDEFGHIJ":
            db.insert_symbol(
                Symbol(
                    name=f"Unique_{letter}",
                    kind="class",
                    file_path=f"/test/{letter}.py",
                    line_start=1,
                    line_end=2,
                )
            )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Unique_", limit=5, level="prefix")
        assert len(results) == 5
        engine.close()


class TestOutputResult:
    def test_text_output_shows_kind_and_file(self, capsys):
        from ast_index.cli import output_result

        items = [
            {"name": "TestClass", "kind": "class", "file_path": "src/test.py", "line_start": 42},
            {"name": "my_func", "kind": "function", "file_path": "src/funcs.py", "line_start": 10},
        ]
        output_result(items, "text", "Results")
        captured = capsys.readouterr()
        assert "TestClass" in captured.out
        assert "class" in captured.out
        assert "src/test.py" in captured.out
        assert "42" in captured.out
        assert "my_func" in captured.out
        assert "function" in captured.out

    def test_text_output_fallback_when_no_extra_fields(self, capsys):
        from ast_index.cli import output_result

        items = [{"name": "SimpleSymbol"}]
        output_result(items, "text", "Results")
        captured = capsys.readouterr()
        assert "SimpleSymbol" in captured.out


class TestWildcardSearch:
    def test_trailing_wildcard_prefix_search(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="UserRepository",
                kind="class",
                file_path="/test/repo.py",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="UserService",
                kind="class",
                file_path="/test/service.py",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="UnrelatedThing",
                kind="class",
                file_path="/test/other.py",
                line_start=1,
                line_end=10,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("User*", limit=10, level="prefix")
        names = [r["name"] for r in results]
        assert "UserRepository" in names
        assert "UserService" in names
        assert "UnrelatedThing" not in names
        engine.close()
