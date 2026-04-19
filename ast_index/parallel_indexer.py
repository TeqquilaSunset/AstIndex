import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .config import Config
from .database import Database
from .models import ParsedFile
from .parsers import get_parser
from .parsers.base import BaseParser
from .utils.file_utils import djb2_hash, get_file_info
from .utils.logging import get_logger

logger = get_logger(__name__)


class ParallelIndexer:
    def __init__(
        self,
        config: Config,
        max_workers: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ):
        self.config = config
        self.max_workers = max_workers or os.cpu_count() or 4
        self.progress_callback = progress_callback
        self._parsers: dict[str, Any] = {}
        self._db_path = config.db_path

    def index_files_parallel(
        self,
        files: list[tuple[Path, str]],
    ) -> dict[str, int]:
        stats = {
            "files_indexed": 0,
            "symbols_indexed": 0,
            "inheritances_indexed": 0,
            "references_indexed": 0,
            "errors": 0,
        }

        total_files = len(files)
        logger.info(
            f"Starting parallel indexing of {total_files} files with {self.max_workers} workers"
        )

        parsed_results: list[ParsedFile] = []
        errors = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._parse_file, file_path, language): (file_path, language)
                for file_path, language in files
            }

            completed = 0
            for future in as_completed(future_to_file):
                (file_path, language) = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        parsed_results.append(result)
                    completed += 1
                    if self.progress_callback:
                        self.progress_callback(completed, total_files)
                except Exception as e:
                    logger.error(f"Error parsing {file_path}: {e}")
                    errors += 1
                    completed += 1

        db = Database(self._db_path)
        try:
            write_stats = self._write_batch(db, parsed_results)
        finally:
            db.close()

        stats["files_indexed"] = write_stats["files_indexed"]
        stats["symbols_indexed"] = write_stats["symbols_indexed"]
        stats["inheritances_indexed"] = write_stats["inheritances_indexed"]
        stats["references_indexed"] = write_stats["references_indexed"]
        stats["errors"] = errors

        return stats

    def _write_batch(self, db: Database, parsed_files: list[ParsedFile]) -> dict[str, int]:
        stats = {
            "files_indexed": 0,
            "symbols_indexed": 0,
            "inheritances_indexed": 0,
            "references_indexed": 0,
        }

        write_batch_size = 100
        for i in range(0, len(parsed_files), write_batch_size):
            batch = parsed_files[i : i + write_batch_size]
            with db.transaction():
                for parsed in batch:
                    file_info = parsed.file_info

                    db.delete_symbols_for_file(file_info.path)
                    db.delete_inheritance_for_file(file_info.path)
                    db.delete_refs_for_file(file_info.path)

                    db.insert_file(file_info)
                    db.insert_symbols(parsed.symbols)
                    db.insert_inheritances(parsed.inheritances)
                    db.insert_references(parsed.references)

                    if hasattr(parsed, "namespace_mapping") and parsed.namespace_mapping:
                        db.save_usings(file_info.path, parsed.namespace_mapping)

                    stats["files_indexed"] += 1
                    stats["symbols_indexed"] += len(parsed.symbols)
                    stats["inheritances_indexed"] += len(parsed.inheritances)
                    stats["references_indexed"] += len(parsed.references)

        return stats

    def _parse_file(self, file_path: Path, language: str) -> ParsedFile | None:
        parser = self._get_parser(language)
        if not parser:
            return None

        if not parser.can_parse(file_path):
            return None

        try:
            content = file_path.read_bytes()

            file_info = get_file_info(file_path, language)
            file_info.content_hash = djb2_hash(content)

            parsed = parser.parse(file_path, content)
            parsed.file_info = file_info

            return parsed
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None

    def _get_parser(self, language: str) -> BaseParser | None:
        if language not in self._parsers:
            parser_cls = get_parser(language)
            if parser_cls:
                self._parsers[language] = parser_cls()
        return self._parsers.get(language)
