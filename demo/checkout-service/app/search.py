"""Search ranking flags are configured per environment in config/flags.yaml —
the application looks the flag key up from the map at runtime."""
from __future__ import annotations

import pathlib

import yaml

from .flags import is_enabled

_CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "flags.yaml"


def _flag_key(setting: str) -> str:
    with open(_CONFIG_PATH) as fh:
        mapping = yaml.safe_load(fh)
    return mapping["search"][setting]


def rank_results(query: str, results: list[dict]) -> list[dict]:
    key = _flag_key("ranking")
    if is_enabled(key):
        return sorted(results, key=lambda r: r.get("score", 0), reverse=True)
    return results
