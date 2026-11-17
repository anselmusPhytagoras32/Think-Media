"""Bounded PDF validation shared by application and learning uploads."""

import re

from app.errors import ApiError

MAX_PDF_BYTES = 5 * 1024 * 1024


def pdf_filename(name: str | None, content_type: str | None, data: bytes) -> str:
    if len(data) > MAX_PDF_BYTES:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "PDF must be at most 5 MiB.")
    if (
        not name
        or not name.lower().endswith(".pdf")
        or content_type != "application/pdf"
        or not data.startswith(b"%PDF-")
        or b"%%EOF" not in data[-1024:]
    ):
        raise ApiError(422, "INVALID_UPLOAD", "Attach a valid PDF document.")
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", name.replace("\\", "/").split("/")[-1])[:196]
    return safe if safe.lower().endswith(".pdf") else safe + ".pdf"
