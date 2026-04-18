import json
from pathlib import Path

import click

from . import __version__
from .config import Config, load_config, save_config
from .database import Database
from .indexer import Indexer
from .search import SearchEngine


def validate_limit(ctx, param, value):
    """Validate that limit is a positive integer."""
    if value is not None and value <= 0:
        raise click.BadParameter("Limit must be a positive integer")
    return value


def output_result(result, format: str, message: str = None):
    """Output result in specified format."""
    if format == "json":
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if isinstance(result, dict):
            for key, value in result.items():
                click.echo(f"{key}: {value}")
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    click.echo(f"- {item.get('name', item)}")
                else:
                    click.echo(f"- {item}")


@click.group()
@click.version_option(version=__version__)
def cli():
    """AST Index - Structural code search tool."""
    pass


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option(
    "--jobs", "-j", type=int, default=None, help="Number of parallel jobs (default: CPU count)"
)
@click.option("--no-parallel", is_flag=True, help="Disable parallel processing")
def index(root: str, format: str, jobs: int | None, no_parallel: bool):
    """Index the project."""
    config = load_config(Path(root))

    # Determine if parallel processing should be used
    use_parallel = not no_parallel

    # Prepare indexer kwargs
    indexer_kwargs = {"config": config, "use_parallel": use_parallel}
    if jobs and use_parallel:
        indexer_kwargs["max_workers"] = jobs

    with Indexer(**indexer_kwargs) as indexer:
        stats = indexer.index()

    elapsed = stats.pop("elapsed_time", None)
    if format == "json":
        if elapsed is not None:
            stats["elapsed_time"] = elapsed
        output_result(stats, format, "Indexing complete")
    else:
        click.echo("Indexing complete")
        for key, value in stats.items():
            click.echo(f"{key}: {value}")
        if elapsed is not None:
            click.echo(f"time: {elapsed}s")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
def update(root: str, format: str):
    """Update index (incremental)."""
    config = load_config(Path(root))

    with Indexer(config=config) as indexer:
        stats = indexer.update()

    elapsed = stats.pop("elapsed_time", None)
    if format == "json":
        if elapsed is not None:
            stats["elapsed_time"] = elapsed
        output_result(stats, format, "Update complete")
    else:
        click.echo("Update complete")
        for key, value in stats.items():
            click.echo(f"{key}: {value}")
        if elapsed is not None:
            click.echo(f"time: {elapsed}s")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
def rebuild(root: str, format: str):
    """Rebuild index from scratch."""
    config = load_config(Path(root))

    with Indexer(config=config) as indexer:
        stats = indexer.rebuild()

    elapsed = stats.pop("elapsed_time", None)
    if format == "json":
        if elapsed is not None:
            stats["elapsed_time"] = elapsed
        output_result(stats, format, "Rebuild complete")
    else:
        click.echo("Rebuild complete")
        for key, value in stats.items():
            click.echo(f"{key}: {value}")
        if elapsed is not None:
            click.echo(f"time: {elapsed}s")


@cli.command()
@click.argument("query", required=False, default=None)
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option(
    "--level",
    type=click.Choice(["exact", "prefix", "fuzzy"]),
    default="prefix",
    help="Search level",
)
@click.option("--limit", type=int, default=50, help="Maximum results", callback=validate_limit)
@click.option("--file", "file_filter", type=str, help="Filter results by file path")
@click.option("--case-sensitive", is_flag=True, help="Case-sensitive search")
def search(
    query: str | None,
    root: str,
    format: str,
    level: str,
    limit: int,
    file_filter: str | None,
    case_sensitive: bool,
):
    """Search for symbols by name. If QUERY is not provided, lists all symbols.

    Use quotes around patterns with wildcards to prevent shell expansion:
      ast-index search "*Service"
      ast-index search "get*"
    """
    if query is not None and not query.strip():
        click.echo(
            "Error: Query cannot be empty. Use 'search' without arguments to list all symbols."
        )
        return

    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.search(query, limit=limit, level=level, case_sensitive=case_sensitive)

    if file_filter:
        results = [r for r in results if file_filter in r.get("file_path", "")]

    if query is None:
        output_result(results, format, f"Found {len(results)} symbols (all)")
    else:
        output_result(results, format, f"Found {len(results)} symbols matching '{query}'")


@cli.command("class")
@click.argument("name", required=False, default=None)
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=50, help="Maximum results", callback=validate_limit)
def search_class(name: str | None, root: str, format: str, limit: int):
    """Search for class/interface definitions. If NAME is not provided, lists all classes."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.search_class(name, limit=limit)

    if name is None:
        output_result(results, format, f"Found {len(results)} classes (all)")
    else:
        output_result(results, format, f"Found {len(results)} classes matching '{name}'")


@cli.command()
@click.argument("symbol", required=False, default=None)
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=500, help="Maximum results", callback=validate_limit)
@click.option("--show-context", is_flag=True, help="Show context of each reference")
@click.option("--file", type=str, help="Filter results by file path")
def usages(symbol: str | None, root: str, format: str, limit: int, show_context: bool, file: str):
    """Find all usages of a symbol. If SYMBOL is not provided, shows most referenced symbols."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        if symbol is None:
            # Show top referenced symbols
            results = engine.get_top_symbols(limit=limit)

            if format == "json":
                output_result(results, format, f"Top {len(results)} most referenced symbols")
            else:
                click.echo(f"Top {len(results)} most referenced symbols:")
                click.echo()
                for item in results:
                    ref_count = item.get("reference_count", 0)
                    files = item.get("file_paths", [])
                    files_str = ", ".join(files[:3])
                    if len(files) > 3:
                        files_str += f" (+{len(files) - 3} more)"
                    click.echo(f"  {ref_count:4d} - {item['name']} ({item['kind']}) [{files_str}]")
            return

        # Original behavior when symbol is provided
        results = engine.search_usages(symbol, limit=limit)

        # Filter by file if specified - filter references, not the whole result dict
        if file:
            results["references"] = [
                r for r in results["references"] if r.get("ref_file", "").endswith(file)
            ]

    if format == "json":
        output_result(results, format, f"Usages of {symbol}")
    elif show_context:
        # Custom output with context - iterate over references, not the dict
        references = results["references"]
        definitions = results.get("definitions", [])

        if not references and not definitions:
            click.echo(f"No usages found for {symbol}")
            return

        # Show definitions first
        if definitions:
            click.echo(f"Definitions of {symbol}:")
            for defn in definitions:
                click.echo(f"  {defn['file_path']}:{defn['line_start']}")
            click.echo()

        # Show references
        if references:
            click.echo(f"Usages of {symbol} ({len(references)} found):")
            click.echo()
            for ref in references:
                click.echo(f"  {ref['ref_file']}:{ref['ref_line']}")
                if ref.get("context"):
                    context = ref["context"]
                    if len(context) > 200:
                        context = context[:200] + "..."
                    context_lower = context.lower()
                    sym_lower = symbol.lower()
                    idx = context_lower.find(sym_lower)
                    if idx >= 0:
                        before = context[:idx]
                        match = context[idx : idx + len(symbol)]
                        after = context[idx + len(symbol) :]
                        click.echo(f"    {before}>>>{match}<<<{after}")
                    else:
                        click.echo(f"    {context}")
                click.echo()
    else:
        output_result(results, format, f"Usages of {symbol}")


@cli.command()
@click.argument("symbol")
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option(
    "--direction",
    type=click.Choice(["children", "parents", "both"]),
    default="both",
    help="Direction",
)
@click.option(
    "--limit", type=int, default=100, help="Maximum results per direction", callback=validate_limit
)
def inheritance(symbol: str, root: str, format: str, direction: str, limit: int):
    """Search inheritance hierarchy."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.search_inheritance(symbol, direction=direction)

    results["children"] = results["children"][:limit]
    results["parents"] = results["parents"][:limit]

    output_result(results, format, f"Inheritance for {symbol}")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
def stats(root: str, format: str):
    """Show index statistics."""
    config = load_config(Path(root))

    with Database(config.db_path) as db:
        stats = db.get_stats()

    output_result(stats, format, "Index statistics")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
def init(root: str):
    """Initialize project with default config."""
    config_path = Path(root) / ".ast-index.yaml"

    if config_path.exists():
        click.echo(f"Config already exists at {config_path}")
        return

    config = Config(root=Path(root))
    save_config(config, config_path)
    click.echo(f"Created config at {config_path}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--root", type=click.Path(exists=True), help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option(
    "--limit", type=int, default=100, help="Maximum results per category", callback=validate_limit
)
def usings(file_path: str, root: str, format: str, limit: int):
    """Показать using директивы для C# файла."""
    from pathlib import Path

    from .database import Database
    from .project_detection import detect_project_root

    if root:
        project_root = Path(root).resolve()
    else:
        project_root = detect_project_root(Path(file_path).resolve())

    if not project_root:
        click.echo("Error: Cannot find project root", err=True)
        return

    config = load_config(project_root)
    db = Database(config.db_path)
    file_path_str = str(Path(file_path).resolve())

    with db:
        mapping = db.get_usings_for_file(file_path_str)

    if format == "json":
        import json

        output = {
            "file": file_path_str,
            "imports": list(mapping.imports)[:limit],
            "static_imports": list(mapping.static_imports)[:limit],
            "aliases": dict(sorted(mapping.aliases.items())[:limit]),
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"Usings for {file_path}:")
        click.echo("\nImports:")
        for imp in sorted(mapping.imports)[:limit]:
            click.echo(f"  {imp}")

        if mapping.static_imports:
            click.echo("\nStatic Imports:")
            for imp in sorted(mapping.static_imports)[:limit]:
                click.echo(f"  {imp}")

        if mapping.aliases:
            click.echo("\nAliases:")
            for alias, target in sorted(mapping.aliases.items())[:limit]:
                click.echo(f"  {alias} = {target}")


@cli.command()
@click.argument("symbol")
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option(
    "--file",
    type=str,
    help="File where symbol is used (helps resolve which definition when multiple exist)",
)
def definition(symbol: str, root: str, format: str, file: str | None):
    """Find symbol definition with import resolution."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        result = engine.search_definition(symbol_name=symbol, reference_file=file)

    if result is None:
        if format == "json":
            click.echo(json.dumps({"error": "Definition not found"}, indent=2))
        else:
            click.echo(f"Definition not found: {symbol}")
        return

    if isinstance(result, list):
        if format == "json":
            output = [
                {
                    "name": r["name"],
                    "kind": r["kind"],
                    "file_path": r["file_path"],
                    "line_start": r["line_start"],
                    "line_end": r["line_end"],
                    "signature": r.get("signature"),
                }
                for r in result
            ]
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            click.echo(f"Found {len(result)} definitions for {symbol}:")
            for r in result:
                click.echo(f"  {r['kind']} {r['name']} - {r['file_path']}:{r['line_start']}")
                if r.get("signature"):
                    click.echo(f"    Signature: {r['signature']}")
    else:
        if format == "json":
            output = {
                "name": result["name"],
                "kind": result["kind"],
                "file_path": result["file_path"],
                "line_start": result["line_start"],
                "line_end": result["line_end"],
                "signature": result.get("signature"),
            }
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            click.echo(f"Definition of {symbol}:")
            click.echo(f"  Kind: {result['kind']}")
            click.echo(f"  File: {result['file_path']}")
            click.echo(f"  Lines: {result['line_start']}-{result['line_end']}")
            if result.get("signature"):
                click.echo(f"  Signature: {result['signature']}")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=50, help="Maximum results", callback=validate_limit)
def methods(root: str, format: str, limit: int):
    """List all methods."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.search_by_kind("method", limit=limit)

    output_result(results, format, f"Found {len(results)} methods")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=50, help="Maximum results", callback=validate_limit)
def functions(root: str, format: str, limit: int):
    """List all functions."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.search_by_kind("function", limit=limit)

    output_result(results, format, f"Found {len(results)} functions")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=50, help="Maximum results", callback=validate_limit)
def interfaces(root: str, format: str, limit: int):
    """List all interfaces."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.search_by_kind("interface", limit=limit)

    output_result(results, format, f"Found {len(results)} interfaces")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=50, help="Maximum results", callback=validate_limit)
def types(root: str, format: str, limit: int):
    """List all type aliases."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.search_by_kind("type_alias", limit=limit)

    output_result(results, format, f"Found {len(results)} type aliases")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=50, help="Maximum results", callback=validate_limit)
def top(root: str, format: str, limit: int):
    """Show most referenced symbols."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.get_top_symbols(limit=limit)

    if format == "json":
        output_result(results, format, f"Top {len(results)} most referenced symbols")
    else:
        click.echo(f"Top {len(results)} most referenced symbols:")
        click.echo()
        for item in results:
            ref_count = item.get("reference_count", 0)
            files = item.get("file_paths", [])
            files_str = ", ".join(files[:3])
            if len(files) > 3:
                files_str += f" (+{len(files) - 3} more)"
            click.echo(f"  {ref_count:4d} - {item['name']} ({item['kind']}) [{files_str}]")


@cli.command()
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
def kinds(root: str, format: str):
    """List all symbol kinds present in the project."""
    config = load_config(Path(root))

    with SearchEngine(config=config) as engine:
        results = engine.get_all_kinds()

    if format == "json":
        output_result(results, format, f"Found {len(results)} symbol kinds")
    else:
        click.echo(f"Symbol kinds in project ({len(results)} total):")
        click.echo()
        for item in results:
            click.echo(f"  {item['kind']:20s} - {item['count']:4d} symbols")


@cli.command("file")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--root", type=click.Path(exists=True), default=".", help="Project root directory")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--limit", type=int, default=200, help="Maximum results", callback=validate_limit)
def file_symbols(file_path: str, root: str, format: str, limit: int):
    """Show all symbols in a specific file."""
    config = load_config(Path(root))

    resolved_path = str(Path(file_path).resolve())

    with SearchEngine(config=config) as engine:
        results = engine.search_in_file(resolved_path, limit=limit)

    if format == "json":
        output_result(results, format, f"Found {len(results)} symbols in {file_path}")
    else:
        click.echo(f"Symbols in {file_path} ({len(results)} found):")
        click.echo()
        for item in results:
            kind = item.get("kind", "unknown")
            name = item.get("name", "")
            line = item.get("line_start", 0)
            parent = item.get("parent")
            if parent:
                click.echo(f"  {line:5d}  {kind:12s}  {parent}.{name}")
            else:
                click.echo(f"  {line:5d}  {kind:12s}  {name}")


def main():
    cli()


if __name__ == "__main__":
    main()
