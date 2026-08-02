"""
Bundled example incidents.

Reading these from disk rather than hard-coding them means the marker can drop
a new JSON file into data/samples/ and it appears in the sidebar without a code
change - which is also how we added incidents while testing prompt variants.
"""

from __future__ import annotations

import json
from functools import lru_cache

from ..config import SAMPLES_DIR
from ..models import SampleSummary

REQUIRED_KEYS = {"id", "title"}


@lru_cache(maxsize=1)
def _load_all() -> dict[str, dict]:
    samples: dict[str, dict] = {}
    if not SAMPLES_DIR.exists():
        return samples

    for path in sorted(SAMPLES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # A malformed sample should not take the server down; it just does
            # not appear in the list.
            continue
        if not REQUIRED_KEYS <= data.keys():
            continue
        data.setdefault("id", path.stem)
        samples[data["id"]] = data
    return samples


def list_samples() -> list[SampleSummary]:
    return [
        SampleSummary(
            id=data["id"],
            title=data["title"],
            scenario=data.get("scenario", ""),
            description=data.get("description", ""),
        )
        for data in _load_all().values()
    ]


def get_sample(sample_id: str) -> dict | None:
    return _load_all().get(sample_id)


def reload_samples() -> None:
    """Drop the cache. Used by the tests and after editing a sample by hand."""
    _load_all.cache_clear()
