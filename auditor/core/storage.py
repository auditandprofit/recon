from __future__ import annotations

"""Storage helpers for events and blobs.

The event log is a very small newline-delimited JSON file that records
all actions performed by the orchestrator.  The blob store keeps raw
artifacts referenced from the log.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Dict
import hashlib


@dataclass
class EventLog:
    """Append-only JSON-lines event log."""

    path: Path

    def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        record = {"type": event_type, **data}
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")


@dataclass
class BlobStore:
    """Simple content-addressed storage."""

    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes) -> str:
        digest = hashlib.sha256(data).hexdigest()
        (self.root / digest).write_bytes(data)
        return digest

    def get(self, digest: str) -> bytes:
        return (self.root / digest).read_bytes()
