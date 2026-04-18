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
    ) -> list[dict[str, Any]]:
        if query is None:
            cursor = self.db._conn.execute(
                "SELECT * FROM symbols ORDER BY name LIMIT ?",
                (limit,),
            )
            return self._deduplicate([dict(row) for row in cursor.fetchall()])

        if case_sensitive:
            if level == "exact":
                cursor = self.db._conn.execute(
                    "SELECT * FROM symbols WHERE name = ? COLLATE BINARY LIMIT ?",
                    (query, limit),
                )
            else:
                cursor = self.db._conn.execute(
                    "SELECT * FROM symbols WHERE name LIKE ? COLLATE BINARY LIMIT ?",
                    (f"%{query}%", limit),
                )
            return self._deduplicate([dict(row) for row in cursor.fetchall()])

        if level == "exact":
            results = self.db.get_symbols_by_name(query)[:limit]
            return self._deduplicate(results)
        elif level == "prefix":
            if query.startswith("*"):
                clean_query = query.lstrip("*")
                return self._deduplicate(self._fuzzy_search(clean_query, limit))
            fts_query = f'"{query}"*'
            results = self.db.search_symbols(fts_query, limit)
            return self._deduplicate(results)
        else:
            return self._deduplicate(self._fuzzy_search(query, limit))

    def _deduplicate(self, symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        result = []
        for s in symbols:
            key = (s.get("name"), s.get("kind"), s.get("file_path"))
            if key not in seen:
                seen.add(key)
                result.append(s)
        return result

    def _fuzzy_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        clean = query.strip("*")
        pattern = f"%{clean}%"
        cursor = self.db._conn.execute(
            """
            SELECT * FROM symbols WHERE name LIKE ?
            ORDER BY
                CASE WHEN kind IN ('class', 'interface') THEN 0 ELSE 1 END,
                name
            LIMIT ?
            """,
            (pattern, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

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
            # Return all classes/interfaces
            cursor = self.db._conn.execute(
                "SELECT * FROM symbols WHERE kind IN ('class', 'interface') ORDER BY name LIMIT ?",
                (limit,),
            )
        else:
            # Search by name (fuzzy match)
            cursor = self.db._conn.execute(
                "SELECT * FROM symbols WHERE name LIKE ? AND kind IN ('class', 'interface') ORDER BY name LIMIT ?",
                (f"%{name}%", limit),
            )
        return [dict(row) for row in cursor.fetchall()]

    def search_usages(
        self, symbol_name: str, limit: int = 500, file_filter: str | None = None
    ) -> dict[str, Any]:
        usages = self.db.get_usages(symbol_name, limit=limit, file_filter=file_filter)
        total_count = self.db.get_usages_count(symbol_name, file_filter=file_filter)
        definitions = self.db.get_symbols_by_name(symbol_name)
        return {
            "symbol": symbol_name,
            "definitions": definitions,
            "references": usages,
            "total_count": total_count,
        }

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
        return [dict(row) for row in cursor.fetchall()]

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
