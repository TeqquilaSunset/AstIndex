"""
Пример интеграции AST Index с AI-агентом

Этот пример показывает, как AI-агент может использовать AST Index
для анализа кодовой базы и принятия решений.
"""

import json
import subprocess
from pathlib import Path
from typing import Any


class ASTIndexHelper:
    """Helper class для AI-агента для работы с AST Index"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()

    def run_command(self, cmd: list[str]) -> str:
        """Выполнить CLI команду и вернуть вывод"""
        full_cmd = ["ast-index"] + cmd
        result = subprocess.run(
            full_cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout

    def index_project(self) -> dict[str, int]:
        """Индексировать проект"""
        output = self.run_command(["index", "--root", str(self.project_root), "--format", "json"])
        return json.loads(output)

    def update_index(self) -> dict[str, int]:
        """Обновить индекс (инкрементально)"""
        output = self.run_command(["update", "--root", str(self.project_root), "--format", "json"])
        return json.loads(output)

    def find_usages(self, symbol: str, show_context: bool = False) -> list[dict]:
        """Найти все использования символа"""
        cmd = ["usages", symbol, "--root", str(self.project_root)]
        if show_context:
            cmd.append("--show-context")
        output = self.run_command(cmd)
        # Парсим вывод (формат зависит от реализации)
        return self._parse_usages(output)

    def search_symbols(self, query: str, level: str = "fuzzy", limit: int = 50) -> list[dict]:
        """Поиск символов по запросу"""
        cmd = ["search", query, "--root", str(self.project_root),
               "--level", level, "--limit", str(limit)]
        output = self.run_command(cmd)
        return self._parse_search_results(output)

    def get_inheritance(self, symbol: str, direction: str = "both") -> list[dict]:
        """Получить иерархию наследования"""
        cmd = ["inheritance", symbol, "--root", str(self.project_root),
               "--direction", direction]
        output = self.run_command(cmd)
        return self._parse_inheritance(output)

    def get_stats(self) -> dict[str, int]:
        """Получить статистику индекса"""
        output = self.run_command(["stats", "--root", str(self.project_root)])
        return self._parse_stats(output)

    def _parse_usages(self, output: str) -> list[dict]:
        """Распарсить вывод usages"""
        lines = output.strip().split('\n')
        usages = []
        for line in lines:
            if ':' in line and not line.startswith('Usages of'):
                parts = line.split(':')
                if len(parts) >= 2:
                    usages.append({
                        'file': parts[0],
                        'line': parts[1].split()[0],
                        'context': ' '.join(parts[1].split()[1:]) if len(parts) > 1 else ''
                    })
        return usages

    def _parse_search_results(self, output: str) -> list[dict]:
        """Распарсить вывод search"""
        lines = output.strip().split('\n')
        results = []
        for line in lines:
            if line.strip().startswith('- '):
                name = line.strip()[2:]
                results.append({'name': name})
        return results

    def _parse_inheritance(self, output: str) -> list[dict]:
        """Распарсить вывод inheritance"""
        # Упрощённый парсинг
        return []

    def _parse_stats(self, output: str) -> dict[str, int]:
        """Распарсить вывод stats"""
        stats = {}
        for line in output.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                stats[key.strip()] = int(value.strip())
        return stats


# ==================== AGENT WORKFLOWS ====================

class CodeAnalysisAgent:
    """AI-агент для анализа кода с использованием AST Index"""

    def __init__(self, project_root: str):
        self.ast = ASTIndexHelper(project_root)

    def analyze_symbol_usage(self, symbol_name: str) -> dict[str, Any]:
        """
        Анализ использования символа

        Возвращает:
        - Количество использований
        - Файлы где используется
        - Контекст использования
        - Рекомендации
        """
        print(f"🔍 Анализ символа: {symbol_name}")

        # 1. Найти использования
        usages = self.ast.find_usages(symbol_name, show_context=True)

        # 2. Сгруппировать по файлам
        files = {}
        for usage in usages:
            file = usage['file']
            if file not in files:
                files[file] = []
            files[file].append(usage)

        # 3. Сформировать отчёт
        report = {
            'symbol': symbol_name,
            'total_usages': len(usages),
            'files_count': len(files),
            'files': files,
            'recommendations': self._generate_recommendations(usages)
        }

        return report

    def find_refactoring_candidates(self) -> list[dict]:
        """
        Найти кандидатов для рефакторинга

        Ищет:
        - Методы с большим количеством использований
        - Классы с сложной иерархией наследования
        - Символы с подозрительными именами
        """
        print("🔍 Поиск кандидатов для рефакторинга")

        # 1. Получить статистику
        self.ast.get_stats()

        # 2. Найти популярные символы (анализ usages)
        # Это упрощённый пример - в реальности нужно анализировать больше

        candidates = []

        # Поиск методов с большим количеством usages
        # (в реальном скрипте нужно пройти по основным символам)

        return candidates

    def understand_codebase_structure(self) -> dict[str, Any]:
        """
        Понять структуру кодовой базы

        Возвращает:
        - Основные модули/компоненты
        - Иерархию классов
        - Связи между компонентами
        """
        print("🏗️ Анализ структуры кодовой базы")

        stats = self.ast.get_stats()

        structure = {
            'overview': stats,
            'main_components': [],
            'inheritance_hierarchy': {}
        }

        return structure

    def impact_analysis(self, symbol_name: str) -> dict[str, Any]:
        """
        Анализ влияния изменений символа

        Показывает что сломается если изменить символ
        """
        print(f"💥 Анализ влияния изменений: {symbol_name}")

        # 1. Найти все использования
        usages = self.ast.find_usages(symbol_name, show_context=True)

        # 2. Проверить наследование
        inheritance = self.ast.get_inheritance(symbol_name, direction="children")

        # 3. Оценить влияние
        impact = {
            'symbol': symbol_name,
            'direct_usages': len(usages),
            'subclasses': len(inheritance),
            'risk_level': self._calculate_risk(usages, inheritance),
            'affected_files': list(set(u['file'] for u in usages)),
            'recommendations': []
        }

        return impact

    def _generate_recommendations(self, usages: list[dict]) -> list[str]:
        """Генерировать рекомендации на основе использования"""
        recommendations = []

        if len(usages) > 50:
            recommendations.append("⚠️ Символ используется много раз - рассмотреть рефакторинг")

        # Анализ контекста
        [u.get('context', '') for u in usages]
        # Здесь можно добавить больше анализа

        return recommendations

    def _calculate_risk(self, usages: list[dict], inheritance: list[dict]) -> str:
        """Рассчитать уровень риска изменений"""
        total_impact = len(usages) + len(inheritance) * 2

        if total_impact > 100:
            return "HIGH"
        elif total_impact > 20:
            return "MEDIUM"
        else:
            return "LOW"


# ==================== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ====================

if __name__ == "__main__":
    # Пример 1: Анализ использования символа
    agent = CodeAnalysisAgent(".")

    # Проверить индекс
    stats = agent.ast.get_stats()
    print(f"📊 Статистика: {stats}")

    if stats.get('symbols', 0) == 0:
        print("📝 Проект не проиндексирован, индексируем...")
        agent.ast.index_project()

    # Найти использования
    usages = agent.ast.find_usages("someMethod", show_context=True)
    print(f"🔍 Найдено использований: {len(usages)}")

    # Поиск символов
    results = agent.ast.search_symbols("User*", level="prefix")
    print(f"🔎 Результаты поиска: {results}")

    # Анализ влияния
    impact = agent.impact_analysis("UserService")
    print(f"💥 Анализ влияния: {impact}")
