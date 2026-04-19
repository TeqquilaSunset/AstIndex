from typing import Any

from .config import Config, load_config
from .database import Database
from .symbol_resolution import SymbolResolver


class SearchEngine:
    def __init__(self, db_path: str | None = None, config: Config | None = None):
        if config:
            self.db = Database(config.db_path)
        elif db_path:
            self.db = Database(db_path)
        else:
            config = load_config()
            self.db = Database(config.db_path)

        self._resolver = None  # Lazy initialization

    def _get_resolver(self) -> SymbolResolver:
        """Get or create SymbolResolver instance."""
        if self._resolver is None:
            self._resolver = SymbolResolver(self.db)
        return self._resolver

    def search(
        self,
        query: str | None,
        limit: int = 50,
        level: str = "prefix",
        case_sensitive: bool = False,
        kind: str | None = None,
        file_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        if query is None:
            return self._search_all(limit, kind=kind, file_filter=file_filter)

        if "." in query and not query.startswith("*"):
            return self._search_dot_path(query, limit, kind=kind, file_filter=file_filter)

        if case_sensitive:
            return self._search_case_sensitive(
                query, limit, level, kind=kind, file_filter=file_filter
            )

        if level == "exact":
            results = self.db.get_symbols_by_name(query, kind=kind)
            results = self._apply_file_filter(results, file_filter)
            return self._deduplicate(results)[:limit]
        elif level == "prefix":
            if query.startswith("*"):
                clean_query = query.lstrip("*")
                results = self._fuzzy_search(
                    clean_query, limit * 3, kind=kind, file_filter=file_filter
                )
                return self._deduplicate(results)[:limit]
            clean_query = query.rstrip("*")
            if kind or file_filter:
                results = self._fuzzy_search(
                    clean_query, limit * 3, kind=kind, file_filter=file_filter
                )
                return self._deduplicate(results)[:limit]
            fts_query = f'"{clean_query}"*'
            results = self.db.search_symbols(fts_query, limit * 3)
            results = self._apply_file_filter(results, file_filter)
            return self._deduplicate(results)[:limit]
        else:
            results = self._fuzzy_search(query, limit * 3, kind=kind, file_filter=file_filter)
            return self._deduplicate(results)[:limit]

    def _apply_file_filter(
        self, symbols: list[dict[str, Any]], file_filter: str | None
    ) -> list[dict[str, Any]]:
        if not file_filter:
            return symbols
        return [s for s in symbols if file_filter in s.get("file_path", "")]

    def _build_file_clause(self, file_filter: str | None) -> tuple[str, list[Any]]:
        if file_filter:
            return " AND file_path LIKE ?", [f"%{file_filter}%"]
        return "", []

    def _search_all(
        self, limit: int, kind: str | None = None, file_filter: str | None = None
    ) -> list[dict[str, Any]]:
        file_clause, file_params = self._build_file_clause(file_filter)
        if kind:
            cursor = self.db._conn.execute(
                f"SELECT * FROM symbols WHERE kind = ?{file_clause} ORDER BY name LIMIT ?",
                [kind] + file_params + [limit * 3],
            )
        else:
            cursor = self.db._conn.execute(
                f"SELECT * FROM symbols WHERE 1=1{file_clause} ORDER BY name LIMIT ?",
                file_params + [limit * 3],
            )
        return self._deduplicate([dict(row) for row in cursor.fetchall()])[:limit]

    def _search_case_sensitive(
        self,
        query: str,
        limit: int,
        level: str,
        kind: str | None = None,
        file_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        file_clause, file_params = self._build_file_clause(file_filter)
        if level == "exact":
            if kind:
                cursor = self.db._conn.execute(
                    "SELECT * FROM symbols WHERE name = ? COLLATE BINARY "
                    f"AND kind = ?{file_clause} LIMIT ?",
                    [query, kind] + file_params + [limit * 3],
                )
            else:
                cursor = self.db._conn.execute(
                    f"SELECT * FROM symbols WHERE name = ? COLLATE BINARY{file_clause} LIMIT ?",
                    [query] + file_params + [limit * 3],
                )
        else:
            if kind:
                cursor = self.db._conn.execute(
                    f"SELECT * FROM symbols "
                    f"WHERE name LIKE ? COLLATE BINARY AND kind = ?{file_clause} LIMIT ?",
                    [f"%{query}%", kind] + file_params + [limit * 3],
                )
            else:
                cursor = self.db._conn.execute(
                    f"SELECT * FROM symbols WHERE name LIKE ? COLLATE BINARY{file_clause} LIMIT ?",
                    [f"%{query}%"] + file_params + [limit * 3],
                )
        return self._deduplicate([dict(row) for row in cursor.fetchall()])[:limit]

    def _deduplicate(self, symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        result = []
        for s in symbols:
            key = (s.get("name"), s.get("kind"), s.get("file_path"))
            if key not in seen:
                seen.add(key)
                result.append(s)
        return result

    def _fuzzy_search(
        self, query: str, limit: int, kind: str | None = None, file_filter: str | None = None
    ) -> list[dict[str, Any]]:
        clean = query.strip("*")
        pattern = f"%{clean}%"
        file_clause, file_params = self._build_file_clause(file_filter)
        if kind:
            cursor = self.db._conn.execute(
                f"""
                SELECT * FROM symbols WHERE name LIKE ? AND kind = ?{file_clause}
                ORDER BY
                    CASE WHEN kind IN ('class', 'interface') THEN 0 ELSE 1 END,
                    name
                LIMIT ?
                """,
                [pattern, kind] + file_params + [limit],
            )
        else:
            cursor = self.db._conn.execute(
                f"""
                SELECT * FROM symbols WHERE name LIKE ?{file_clause}
                ORDER BY
                    CASE WHEN kind IN ('class', 'interface') THEN 0 ELSE 1 END,
                    name
                LIMIT ?
                """,
                [pattern] + file_params + [limit],
            )
        return [dict(row) for row in cursor.fetchall()]

    def _search_dot_path(
        self, query: str, limit: int, kind: str | None = None, file_filter: str | None = None
    ) -> list[dict[str, Any]]:
        parts = query.split(".")
        symbol_name = parts[-1]
        namespace_parts = parts[:-1]
        namespace_hint = ".".join(namespace_parts)
        file_clause, file_params = self._build_file_clause(file_filter)

        if kind:
            cursor = self.db._conn.execute(
                f"SELECT * FROM symbols "
                f"WHERE name = ? AND kind = ? "
                f"AND (scope LIKE ? OR file_path LIKE ?){file_clause} LIMIT ?",
                (
                    [symbol_name, kind, f"%{namespace_hint}%", f"%{'/'.join(namespace_parts)}%"]
                    + file_params
                    + [limit * 3]
                ),
            )
        else:
            cursor = self.db._conn.execute(
                f"SELECT * FROM symbols "
                f"WHERE name = ? AND (scope LIKE ? OR file_path LIKE ?){file_clause} LIMIT ?",
                (
                    [symbol_name, f"%{namespace_hint}%", f"%{'/'.join(namespace_parts)}%"]
                    + file_params
                    + [limit * 3]
                ),
            )

        results = [dict(row) for row in cursor.fetchall()]
        if not results:
            results = self.db.get_symbols_by_name(symbol_name, kind=kind)
            results = self._apply_file_filter(results, file_filter)
        return self._deduplicate(results)[:limit]

    def search_class(self, name: str | None, limit: int = 50) -> list[dict[str, Any]]:
        """
        Search for class/interface definitions.

        Args:
            name: Class name to search for (fuzzy match). If None, returns all classes.
            limit: Maximum number of results.

        Returns:
            List of class/interface symbols.
        """
        if name is None:
            cursor = self.db._conn.execute(
                "SELECT * FROM symbols WHERE kind IN ('class', 'interface') ORDER BY name LIMIT ?",
                (limit * 3,),
            )
        else:
            cursor = self.db._conn.execute(
                "SELECT * FROM symbols WHERE name LIKE ? "
                "AND kind IN ('class', 'interface') ORDER BY name LIMIT ?",
                (f"%{name}%", limit * 3),
            )
        return self._deduplicate([dict(row) for row in cursor.fetchall()])[:limit]

    def search_usages(
        self,
        symbol_name: str,
        limit: int = 500,
        file_filter: str | None = None,
        kind: str | None = None,
        resolve: bool = False,
    ) -> dict[str, Any]:
        usages = self.db.get_usages(symbol_name, limit=limit, file_filter=file_filter)
        total_count = self.db.get_usages_count(symbol_name, file_filter=file_filter)
        definitions = self.db.get_symbols_by_name(symbol_name, kind=kind)

        result = {
            "symbol": symbol_name,
            "definitions": definitions,
            "references": usages,
            "total_count": total_count,
        }

        if resolve and definitions:
            resolver = self._get_resolver()
            groups: dict[str, list[dict[str, Any]]] = {}
            for ref in usages:
                resolved = resolver.resolve_symbol(symbol_name, ref["ref_file"])
                if resolved:
                    scope = resolved.get("scope", "")
                    name = resolved["name"]
                    fp = resolved["file_path"]
                    line = resolved.get("line_start", "")
                    key = f"{scope}.{name} ({fp}:{line})"
                else:
                    key = f"{symbol_name} (unresolved)"
                groups.setdefault(key, []).append(ref)
            result["groups"] = [
                {"definition": defn_key, "references": refs} for defn_key, refs in groups.items()
            ]

        return result

    def search_inheritance(self, symbol_name: str, direction: str = "children") -> dict[str, Any]:
        result = {
            "symbol": symbol_name,
            "children": [],
            "parents": [],
        }
        if direction in ("children", "both"):
            result["children"] = self.db.get_children(symbol_name)
        if direction in ("parents", "both"):
            result["parents"] = self.db.get_parents(symbol_name)
        return result

    def search_by_kind(self, kind: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.db.get_symbols_by_kind(kind)[:limit]

    def search_in_file(self, file_path: str, limit: int = 100) -> list[dict[str, Any]]:
        cursor = self.db._conn.execute(
            "SELECT * FROM symbols WHERE file_path = ? ORDER BY line_start LIMIT ?",
            (file_path, limit),
        )
        results = [dict(row) for row in cursor.fetchall()]
        if not results:
            cursor = self.db._conn.execute(
                "SELECT * FROM symbols WHERE file_path LIKE ? ORDER BY line_start LIMIT ?",
                (f"%{file_path}%", limit),
            )
            results = [dict(row) for row in cursor.fetchall()]
        return results

    def search_definition(
        self,
        symbol_name: str,
        reference_file: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        if reference_file:
            resolver = self._get_resolver()
            return resolver.resolve_symbol(symbol_name, reference_file)

        symbols = self.db.get_symbols_by_name(symbol_name)

        if not symbols:
            return None

        if len(symbols) == 1:
            return symbols[0]

        return symbols

    def get_top_symbols(self, limit: int = 50) -> list[dict[str, Any]]:
        cursor = self.db._conn.execute(
            """
            SELECT s.name, s.kind,
                   (SELECT GROUP_CONCAT(distinct_path, '||')
                    FROM (SELECT DISTINCT s2.file_path as distinct_path
                          FROM symbols s2 WHERE s2.name = s.name AND s2.kind = s.kind)) as files,
                   COUNT(r.id) as reference_count
            FROM symbols s
            LEFT JOIN refs r ON s.name = r.symbol_name
            GROUP BY s.name, s.kind
            HAVING reference_count > 0
            ORDER BY reference_count DESC, s.name
            LIMIT ?
            """,
            (limit,),
        )
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            d["file_paths"] = d.pop("files", "").split("||") if d.get("files") else []
            results.append(d)
        return results

    def get_all_kinds(self) -> list[dict[str, Any]]:
        """
        Get all symbol kinds present in the database with counts.

        Returns:
            List of unique kinds with their counts.
        """
        cursor = self.db._conn.execute(
            """
            SELECT kind, COUNT(*) as count
            FROM symbols
            GROUP BY kind
            ORDER BY count DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
