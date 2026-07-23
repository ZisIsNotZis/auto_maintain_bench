from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any


class TelemetryArchive:
    def __init__(
        self,
        root: Path,
        *,
        max_files: int = 10080,
        max_age_s: int | None = 7 * 24 * 60 * 60,
    ) -> None:
        if max_files < 1:
            raise ValueError("max_files must be positive")
        self.root = root
        self.max_files = max_files
        self.max_age_s = max_age_s

    def store(
        self,
        telemetry: dict[str, Any],
        *,
        observed_at: str | None = None,
    ) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        timestamp = _parse_time(observed_at or str(telemetry.get("observed_at", "")))
        stem = timestamp.strftime("%Y%m%dT%H%M%S.%fZ")
        path = self._unique_path(stem)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(telemetry, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
        self._replace_latest(path)
        self.rotate()
        return path

    def rotate(self) -> None:
        files = self._data_files()
        if self.max_age_s is not None:
            cutoff = time.time() - self.max_age_s
            for path in list(files):
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
            files = self._data_files()
        for path in files[: max(0, len(files) - self.max_files)]:
            path.unlink(missing_ok=True)

    def _data_files(self) -> list[Path]:
        return sorted(
            path
            for path in self.root.glob("*.json")
            if path.name != "latest.json" and not path.is_symlink()
        )

    def _unique_path(self, stem: str) -> Path:
        candidate = self.root / f"{stem}.json"
        suffix = 1
        while candidate.exists():
            candidate = self.root / f"{stem}-{suffix:03d}.json"
            suffix += 1
        return candidate

    def _replace_latest(self, path: Path) -> None:
        latest = self.root / "latest.json"
        temporary = self.root / ".latest.json.tmp"
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(path.name)
        os.replace(temporary, latest)


def _parse_time(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("observed_at must include a timezone")
    return parsed.astimezone(timezone.utc)
