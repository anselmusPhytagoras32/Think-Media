"""Input normalization and validation shared by schemas and services.

All defaults/lengths here come from the Phase 1 contract and are implementation
defaults, not approved pilot policy.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

EMAIL_MAX_LENGTH = 254
DISPLAY_NAME_MAX_LENGTH = 100
PROFILE_TEXT_MAX_LENGTH = 200
COMPANY_NAME_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000
LOCATION_MAX_LENGTH = 200
WEBSITE_MAX_LENGTH = 2048
SKILLS_MAX_ENTRIES = 30
SKILL_MAX_LENGTH = 80
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
REASON_MAX_LENGTH = 1000

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Email must be a string.")
    normalized = value.strip().casefold()
    if len(normalized) > EMAIL_MAX_LENGTH:
        raise ValueError(f"Email must be at most {EMAIL_MAX_LENGTH} characters.")
    if not _EMAIL_RE.match(normalized):
        raise ValueError("Enter a valid email address.")
    return normalized


def normalize_display_name(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Display name must be a string.")
    normalized = value.strip()
    if not (1 <= len(normalized) <= DISPLAY_NAME_MAX_LENGTH):
        raise ValueError(
            f"Display name must be between 1 and {DISPLAY_NAME_MAX_LENGTH} characters after trimming."
        )
    return normalized


def normalize_profile_text(
    value: str | None, *, field: str, max_length: int, allow_empty: bool = True
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string.")
    normalized = value.strip()
    if not allow_empty and not normalized:
        raise ValueError(f"{field} is required.")
    if len(normalized) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters.")
    return normalized


def normalize_website(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Website must be a string or null.")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > WEBSITE_MAX_LENGTH:
        raise ValueError(f"Website must be at most {WEBSITE_MAX_LENGTH} characters.")
    if any(ch.isspace() or ord(ch) < 32 for ch in normalized):
        raise ValueError("Website must not contain whitespace or control characters.")
    parsed = urlparse(normalized)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Website must be an absolute HTTP(S) URL.")
    return normalized


def normalize_string_list(value: list[str], *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings.")
    if len(value) > SKILLS_MAX_ENTRIES:
        raise ValueError(f"{field} may contain at most {SKILLS_MAX_ENTRIES} entries.")
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Each {field} entry must be a string.")
        normalized = item.strip()
        if not (1 <= len(normalized) <= SKILL_MAX_LENGTH):
            raise ValueError(
                f"Each {field} entry must be between 1 and {SKILL_MAX_LENGTH} characters after trimming."
            )
        if normalized in seen:
            raise ValueError(f"{field} entries must be unique after trimming.")
        seen.add(normalized)
        result.append(normalized)
    return result


def validate_password(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Password must be a string.")
    if not (PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH):
        raise ValueError(
            f"Password must be between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters."
        )
    return value


def normalize_reason(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Reason must be a string.")
    normalized = value.strip()
    if not (1 <= len(normalized) <= REASON_MAX_LENGTH):
        raise ValueError(
            f"Reason must be between 1 and {REASON_MAX_LENGTH} characters after trimming."
        )
    return normalized
