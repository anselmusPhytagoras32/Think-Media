"""FR10/NFR03: reviewed public guides available without seeding user data.

Only these versioned files are part of the assistant's approved read-only corpus.
They are not database learning records and cannot be edited through the admin API.
"""

import json
from pathlib import Path


_KNOWLEDGE = Path(__file__).resolve().parents[2] / "knowledge"
_FILES = (
    "ojt-preparation.json",
    "thinkmedia-workflows.json",
    "thinkmedia-help.json",
)


def _load():
    guides = {}
    for name in _FILES:
        for row in json.loads((_KNOWLEDGE / name).read_text(encoding="utf-8")):
            slug = row["slug"]
            if slug in guides or not all(row.get(field) for field in ("title", "summary", "body", "tags")):
                raise ValueError(f"Invalid bundled guidance in {name}.")
            guides[slug] = {
                "id": f"guide:{slug}",
                "title": row["title"],
                "summary": row["summary"],
                "body": row["body"],
                "tags": row["tags"],
            }
    return guides


GUIDES = _load()


def guide_detail(slug):
    guide = GUIDES.get(slug)
    if guide is None:
        return None
    return {**guide, "status": "published", "has_quiz": False,
            "saved": False, "reacted": False, "read_only": True}
