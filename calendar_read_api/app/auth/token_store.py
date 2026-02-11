from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path


class TokenStore(ABC):
    @abstractmethod
    def load(self) -> dict | None:
        ...

    @abstractmethod
    def save(self, tokens: dict) -> None:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...


class DevFileTokenStore(TokenStore):
    def __init__(self, path: str = "./token.json"):
        self._path = Path(path)

    def load(self) -> dict | None:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text())
        return data if data else None

    def save(self, tokens: dict) -> None:
        self._path.write_text(json.dumps(tokens))

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()


def get_token_store(store_type: str = "dev_file", path: str = "./token.json") -> TokenStore:
    if store_type == "dev_file":
        return DevFileTokenStore(path)
    raise ValueError(f"Unknown token store type: {store_type}")
