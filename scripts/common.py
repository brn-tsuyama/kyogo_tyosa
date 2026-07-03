"""Shared helpers for the per-source scraping scripts."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")


def output_path(source: str, label: str) -> Path:
    """Build a timestamped output path under data/raw/<source>/."""
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    return DATA_DIR / source / f"{label}_{timestamp}.jsonl"


class JsonlWriter:
    """Append-as-you-go JSON Lines writer, so partial progress survives interruption."""

    def __init__(self, path: Path) -> None:
        """Set the target path; the file is opened on __enter__."""
        self._path = path
        self._count = 0

    def __enter__(self) -> Self:
        """Open the output file, creating parent directories as needed."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._path.open("w", encoding="utf-8")
        return self

    def write(self, record: dict[str, Any]) -> None:
        """Write one record and flush, so a crash mid-run loses at most one line."""
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._file.flush()
        self._count += 1

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the output file and log how many records were written."""
        self._file.close()
        logger.info("wrote %d records to %s", self._count, self._path)
