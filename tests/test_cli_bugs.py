import yaml

from ast_index.config import Config, load_config
from ast_index.database import Database
from ast_index.indexer import Indexer
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


class TestNamespaceResolve:
    def test_search_usages_with_resolve(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Tag",
                kind="class",
                file_path="/project/NsA/Tag.cs",
                line_start=1,
                line_end=10,
                scope="NsA",
            )
        )
        db.insert_symbol(
            Symbol(
                name="Tag",
                kind="class",
                file_path="/project/NsB/Tag.cs",
                line_start=1,
                line_end=10,
                scope="NsB",
            )
        )
        db.insert_references(
            [
                Reference("Tag", "/project/NsA/Tag.cs", "/project/consumer_a.cs", 5, 0, "usage"),
                Reference("Tag", "/project/NsB/Tag.cs", "/project/consumer_b.cs", 10, 0, "usage"),
            ]
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        result = engine.search_usages("Tag", limit=500, resolve=True)
        assert "groups" in result
        assert len(result["groups"]) >= 1
        all_refs = []
        for g in result["groups"]:
            all_refs.extend(g["references"])
        assert len(all_refs) == 2
        engine.close()

    def test_search_usages_without_resolve(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Tag",
                kind="class",
                file_path="/project/NsA/Tag.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_references(
            [
                Reference("Tag", "/project/NsA/Tag.cs", "/project/consumer.cs", 5, 0, "usage"),
            ]
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        result = engine.search_usages("Tag", limit=500, resolve=False)
        assert "groups" not in result
        engine.close()

    def test_cli_usages_resolve_flag(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        db.insert_symbol(
            Symbol(
                name="Tag",
                kind="class",
                file_path="/project/NsA/Tag.cs",
                line_start=1,
                line_end=5,
                scope="NsA",
            )
        )
        db.insert_symbol(
            Symbol(
                name="Tag",
                kind="class",
                file_path="/project/NsB/Tag.cs",
                line_start=1,
                line_end=5,
                scope="NsB",
            )
        )
        db.insert_references(
            [
                Reference("Tag", "/project/NsA/Tag.cs", "/project/consumer.cs", 5, 0, "usage"),
                Reference("Tag", "/project/NsB/Tag.cs", "/project/consumer.cs", 10, 0, "usage"),
            ]
        )
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "usages",
                "Tag",
                "--root",
                str(temp_dir),
                "--resolve",
            ],
        )
        assert result.exit_code == 0


class TestDotPathSearch:
    def test_search_with_dot_path(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="SourceMeta",
                kind="class",
                file_path="/project/Api/Source.cs",
                line_start=1,
                line_end=10,
                scope="Api.Source",
            )
        )
        db.insert_symbol(
            Symbol(
                name="SourceMeta",
                kind="class",
                file_path="/project/Other/Meta.cs",
                line_start=1,
                line_end=10,
                scope="Other.Meta",
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Api.Source.SourceMeta", limit=50, level="exact")
        assert len(results) == 1
        assert results[0]["scope"] == "Api.Source"
        engine.close()

    def test_search_dot_path_fuzzy(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="SourceMeta",
                kind="class",
                file_path="/project/Api/Source.cs",
                line_start=1,
                line_end=10,
                scope="Api.Source",
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Api.Source.SourceMeta", limit=50, level="prefix")
        assert len(results) >= 1
        assert results[0]["name"] == "SourceMeta"
        engine.close()

    def test_search_dot_path_no_match_falls_back(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="MyClass",
                kind="class",
                file_path="/project/some/Other.cs",
                line_start=1,
                line_end=10,
                scope="Wrong.Namespace",
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Some.Namespace.MyClass", limit=50, level="exact")
        assert len(results) == 1
        assert results[0]["name"] == "MyClass"
        engine.close()


class TestBugConfigRootOverride:
    def test_load_config_preserves_user_root(self, temp_dir):
        parent_dir = temp_dir / "parent"
        parent_dir.mkdir()
        project_dir = parent_dir / "project"
        project_dir.mkdir()

        config_file = parent_dir / ".ast-index.yaml"
        config_file.write_text(yaml.dump({"includes": ["*.cs"], "excludes": ["bin", "obj"]}))

        config = load_config(project_dir)
        assert config.root == project_dir.resolve()

    def test_load_config_without_yaml_uses_root(self, temp_dir):
        config = load_config(temp_dir)
        assert config.root == temp_dir.resolve()

    def test_load_config_with_yaml_in_project_root(self, temp_dir):
        config_file = temp_dir / ".ast-index.yaml"
        config_file.write_text(yaml.dump({"includes": ["*.cs"], "excludes": ["bin"]}))
        config = load_config(temp_dir)
        assert config.root == temp_dir.resolve()

    def test_load_config_db_path_uses_user_root(self, temp_dir):
        project_dir = temp_dir / "project"
        project_dir.mkdir()

        parent_config = temp_dir / ".ast-index.yaml"
        parent_config.write_text(yaml.dump({"includes": ["*.cs"], "excludes": ["bin"]}))

        config = load_config(project_dir)
        assert str(project_dir.resolve()) in config.db_path


class TestBugUpdateDeletesAll:
    def test_update_preserves_unmodified_files(self, temp_dir):
        cs_file = temp_dir / "Engine.cs"
        cs_file.write_text("public class Engine { }\n")

        config = Config(root=temp_dir)
        with Indexer(config=config, use_parallel=False) as indexer:
            indexer.index()

        with Database(config.db_path) as db:
            stats = db.get_stats()
            assert stats["files"] == 1
            assert stats["symbols"] >= 1

        cs_file.write_text("public class Engine { public int Id { get; set; } }\n")

        config2 = Config(root=temp_dir)
        with Indexer(config=config2, use_parallel=False) as indexer:
            update_stats = indexer.update()

        assert update_stats["files_deleted"] == 0
        assert update_stats["files_modified"] == 1

    def test_update_does_not_delete_when_config_in_parent(self, temp_dir):
        parent_dir = temp_dir / "workspace"
        parent_dir.mkdir()
        project_dir = parent_dir / "myproject"
        project_dir.mkdir()

        config_file = parent_dir / ".ast-index.yaml"
        config_file.write_text(yaml.dump({"excludes": ["bin", "obj"]}))

        cs_file = project_dir / "App.cs"
        cs_file.write_text("public class App { }\n")

        config = Config(root=project_dir)
        with Indexer(config=config, use_parallel=False) as indexer:
            indexer.index()

        with Database(config.db_path) as db:
            assert db.get_stats()["files"] == 1

        config2 = Config(root=project_dir)
        with Indexer(config=config2, use_parallel=False) as indexer:
            update_stats = indexer.update()

        assert update_stats["files_deleted"] == 0


class TestBugFileCommand:
    def test_search_in_file_finds_symbols(self, temp_dir):
        cs_file = temp_dir / "Engine.cs"
        cs_file.write_text("public class Engine { public void Run() { } }\n")

        config = Config(root=temp_dir)
        with Indexer(config=config, use_parallel=False) as indexer:
            indexer.index()

        with SearchEngine(config=config) as engine:
            resolved = str(cs_file.resolve())
            results = engine.search_in_file(resolved)

        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert "Engine" in names

    def test_search_in_file_fuzzy_fallback(self, temp_dir):
        db = Database(str(temp_dir / "test.db"))
        abs_path = str(temp_dir.resolve() / "Engine.cs")
        db.insert_symbol(
            Symbol(
                name="Engine",
                kind="class",
                file_path=abs_path,
                line_start=1,
                line_end=10,
            )
        )
        db.close()

        engine = SearchEngine(db_path=str(temp_dir / "test.db"))
        results = engine.search_in_file("Engine.cs")
        assert len(results) == 1
        engine.close()


class TestSearchFileFilterSQL:
    def test_search_file_filter_at_sql_level(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Controller",
                kind="class",
                file_path="/project/ioServer/Controllers/HomeController.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Controller",
                kind="class",
                file_path="/project/other/Controller.cs",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search(
            "Controller", limit=50, level="exact", file_filter="ioServer/Controllers/"
        )
        assert len(results) == 1
        assert "ioServer" in results[0]["file_path"]
        engine.close()

    def test_search_file_filter_nonexistent_returns_empty(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Controller",
                kind="class",
                file_path="/project/Controllers/HomeController.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search(
            "Controller", limit=50, level="exact", file_filter="nonexistent_path"
        )
        assert len(results) == 0
        engine.close()

    def test_search_file_filter_prefix_level(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="HomeController",
                kind="class",
                file_path="/project/ioServer/Controllers/HomeController.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="AdminController",
                kind="class",
                file_path="/project/other/AdminController.cs",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Controller", limit=50, level="prefix", file_filter="ioServer/")
        assert len(results) == 1
        assert results[0]["name"] == "HomeController"
        engine.close()

    def test_search_file_filter_fuzzy_level(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="MyService",
                kind="class",
                file_path="/project/services/MyService.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="MyService",
                kind="class",
                file_path="/project/handlers/MyService.cs",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Serv", limit=50, level="fuzzy", file_filter="services/")
        assert len(results) == 1
        engine.close()

    def test_search_file_filter_none_returns_all(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Handler",
                kind="class",
                file_path="/project/a/Handler.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Handler",
                kind="class",
                file_path="/project/b/Handler.cs",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Handler", limit=50, level="exact", file_filter=None)
        assert len(results) == 2
        engine.close()

    def test_search_all_with_file_filter(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Foo",
                kind="class",
                file_path="/project/dir_a/Foo.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Bar",
                kind="class",
                file_path="/project/dir_b/Bar.cs",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search(None, limit=50, file_filter="dir_a/")
        assert len(results) == 1
        assert results[0]["name"] == "Foo"
        engine.close()

    def test_cli_search_file_filter(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        db.insert_symbol(
            Symbol(
                name="Controller",
                kind="class",
                file_path="/project/ioServer/Controllers/HomeController.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Controller",
                kind="class",
                file_path="/project/other/Controller.cs",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "Controller", "--root", str(temp_dir), "--file", "ioServer/"],
        )
        assert result.exit_code == 0
        assert "ioServer" in result.output
        assert "other" not in result.output

    def test_search_file_filter_with_kind(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="Test",
                kind="class",
                file_path="/project/dir_a/Test.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="Test",
                kind="method",
                file_path="/project/dir_b/Test.cs",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("Test", limit=50, level="exact", kind="class", file_filter="dir_a/")
        assert len(results) == 1
        assert results[0]["kind"] == "class"
        engine.close()

    def test_search_case_sensitive_with_file_filter(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="MyClass",
                kind="class",
                file_path="/project/dir_a/MyClass.cs",
                line_start=1,
                line_end=10,
            )
        )
        db.insert_symbol(
            Symbol(
                name="myclass",
                kind="function",
                file_path="/project/dir_b/helper.py",
                line_start=1,
                line_end=5,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search(
            "MyClass", limit=50, level="exact", case_sensitive=True, file_filter="dir_a/"
        )
        assert len(results) == 1
        assert results[0]["name"] == "MyClass"
        engine.close()


class TestDefinitionLimit:
    def test_definition_with_limit(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        for i in range(20):
            db.insert_symbol(
                Symbol(
                    name="Id",
                    kind="property",
                    file_path=f"/test/file_{i}.cs",
                    line_start=i + 1,
                    line_end=i + 2,
                )
            )
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["definition", "Id", "--root", str(temp_dir), "--limit", "5"],
        )
        assert result.exit_code == 0
        assert "Found 5 definitions" in result.output

    def test_definition_without_limit_shows_all(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        for i in range(10):
            db.insert_symbol(
                Symbol(
                    name="MySymbol",
                    kind="class",
                    file_path=f"/test/file_{i}.cs",
                    line_start=i + 1,
                    line_end=i + 2,
                )
            )
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["definition", "MySymbol", "--root", str(temp_dir)],
        )
        assert result.exit_code == 0
        assert "Found 10 definitions" in result.output

    def test_definition_limit_json(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        for i in range(10):
            db.insert_symbol(
                Symbol(
                    name="Tag",
                    kind="class",
                    file_path=f"/test/file_{i}.cs",
                    line_start=i + 1,
                    line_end=i + 2,
                )
            )
        db.close()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["definition", "Tag", "--root", str(temp_dir), "--limit", "3", "--format", "json"],
        )
        assert result.exit_code == 0
        import json

        data = json.loads(result.output)
        assert len(data) == 3


class TestUsagesNoSymbolCapped:
    def test_usages_no_symbol_caps_at_50(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        for i in range(100):
            db.insert_symbol(
                Symbol(
                    name=f"Sym_{i}",
                    kind="class",
                    file_path=f"/test/file_{i}.cs",
                    line_start=1,
                    line_end=5,
                )
            )
            db.insert_references(
                [
                    Reference(
                        f"Sym_{i}", f"/test/file_{i}.cs", f"/test/usage_{i}.cs", 10, 0, "usage"
                    ),
                ]
            )
        db.close()

        runner = CliRunner()
        result = runner.invoke(cli, ["usages", "--root", str(temp_dir)])
        assert result.exit_code == 0
        assert "Top 50 most referenced" in result.output

    def test_usages_no_symbol_respects_lower_limit(self, temp_dir):
        from click.testing import CliRunner
        from ast_index.cli import cli
        from ast_index.config import Config

        config = Config(root=temp_dir)
        db = Database(config.db_path)
        for i in range(100):
            db.insert_symbol(
                Symbol(
                    name=f"Sym_{i}",
                    kind="class",
                    file_path=f"/test/file_{i}.cs",
                    line_start=1,
                    line_end=5,
                )
            )
            db.insert_references(
                [
                    Reference(
                        f"Sym_{i}", f"/test/file_{i}.cs", f"/test/usage_{i}.cs", 10, 0, "usage"
                    ),
                ]
            )
        db.close()

        runner = CliRunner()
        result = runner.invoke(cli, ["usages", "--root", str(temp_dir), "--limit", "10"])
        assert result.exit_code == 0
        assert "Top 10 most referenced" in result.output


class TestFileFilterPathSeparator:
    def test_file_filter_with_forward_slash_matches_backslash(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="SampleClass",
                kind="class",
                file_path="C:\\project\\src\\app.py",
                line_start=1,
                line_end=10,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("SampleClass", limit=50, level="exact", file_filter="src/")
        assert len(results) == 1
        engine.close()

    def test_file_filter_apply_normalizes_separators(self, db_path):
        db = Database(db_path)
        db.insert_symbol(
            Symbol(
                name="OtherClass",
                kind="class",
                file_path="C:\\project\\subdir\\other.py",
                line_start=1,
                line_end=10,
            )
        )
        db.close()

        engine = SearchEngine(db_path=db_path)
        results = engine.search("OtherClass", limit=50, level="exact")
        filtered = engine._apply_file_filter(results, "subdir/")
        assert len(filtered) == 1
        engine.close()
