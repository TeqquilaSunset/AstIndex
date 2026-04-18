"""
Модуль для разрешения символов с учётом импортов/usings.

Позволяет точно определить, на какой символ ссылается использование,
учитывая using директивы (C#) и import statements (другие языки).
"""
from typing import Any


class SymbolResolver:
    """Разрешение символов с учётом импортов/usings."""

    def __init__(self, db):
        """
        Initialize resolver.

        Args:
            db: Database instance
        """
        self.db = db

    def resolve_symbol(
        self,
        symbol_name: str,
        reference_file: str
    ) -> dict[str, Any] | None:
        """
        Разрешить символ с учётом using директив.

        Алгоритм:
        1. Получить usings для файла reference_file
        2. Найти все символы с именем symbol_name
        3. Отфильтровать по namespace:
           - Точное совпадение (если symbol в том же файле)
           - Совпадение через using (если symbol.namespace в usings)
        4. Вернуть наиболее вероятное определение

        Args:
            symbol_name: Имя символа для разрешения
            reference_file: Файл, где используется символ

        Returns:
            Словарь с информацией о символе или None
        """
        # Получить usings для файла
        namespace_mapping = self.db.get_usings_for_file(reference_file)

        # Найти все символы с таким именем
        candidates = self.db.get_symbols_by_name(symbol_name)

        if not candidates:
            return None

        # Если только один кандидат - вернуть его
        if len(candidates) == 1:
            return candidates[0]

        # Приоритеты разрешения
        scored_candidates = []

        for candidate in candidates:
            score = 0
            candidate_file = candidate["file_path"]

            # Приоритет 1: символ в том же файле
            if candidate_file == reference_file:
                score += 1000

            # Приоритет 2: символ в пространстве имён из usings
            candidate_namespace = self._extract_namespace(candidate_file)
            if candidate_namespace in namespace_mapping.imports:
                score += 500

            # Приоритет 3: символ через alias
            for alias, target_ns in namespace_mapping.aliases.items():
                if alias == symbol_name and candidate_namespace == target_ns:
                    score += 600

            scored_candidates.append((score, candidate))

        # Вернуть кандидата с наивысшим скором
        if scored_candidates:
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            return scored_candidates[0][1]

        return candidates[0]  # fallback

    def _extract_namespace(self, file_path: str) -> str:
        """
        Извлечь namespace из пути к файлу.

        Пример: /project/Models/UserRepository.cs -> App.Models

        Args:
            file_path: Путь к файлу

        Returns:
            Namespace или пустая строка
        """
        parts = file_path.replace("\\", "/").split("/")
        result_parts = []

        for part in parts:
            # Пропуск src, project, etc.
            if part.lower() in ["src", "project", "app", "code"]:
                continue
            # Пропуск файлов с расширением
            if "." in part and part.endswith(".cs"):
                continue
            if part and not part.startswith("."):
                result_parts.append(part)

        return ".".join(result_parts) if result_parts else ""
