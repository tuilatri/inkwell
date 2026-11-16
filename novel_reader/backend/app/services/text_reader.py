from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")


@dataclass(frozen=True)
class TextRead:
    text: str
    encoding: str


class TextReadError(Exception):
    """Raised when no configured encoding can decode the file."""


def read_text(path: Path) -> TextRead:
    data = path.read_bytes()
    for encoding in ENCODINGS:
        try:
            return TextRead(text=data.decode(encoding), encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise TextReadError(f"cannot decode {path.name}")
