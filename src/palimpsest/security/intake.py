"""Security intake layer for manuscript image validation and sanitization.

Validates file type (magic bytes), file size, and strips EXIF metadata
before any image bytes reach the Gemini API pipeline.

SEC-04 (prompt injection defense) is handled in agents/transcription.py
via structured output schema and system prompt boundary.
"""

import io
from pathlib import Path

import filetype
from PIL import Image, ImageOps

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


class IntakeError(ValueError):
    """Raised when a file fails security validation."""


def validate_and_clean(file_path: str) -> tuple[bytes, str]:
    """Validate and sanitize a manuscript image file.

    Returns (clean_bytes, mime_type) where clean_bytes have no EXIF metadata
    and mime_type is a proper MIME string (e.g. "image/jpeg").

    Raises IntakeError if validation fails.
    """
    path = Path(file_path)

    # SEC-02: size check first (cheapest gate — reads only file metadata)
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise IntakeError(
            f"File too large: {file_size} bytes (max {MAX_FILE_SIZE_BYTES})"
        )

    raw_bytes = path.read_bytes()

    # SEC-01: magic-byte validation via filetype (reads first 261 bytes, no decoding)
    # NEVER use file extension; NEVER call Pillow before this check
    kind = filetype.guess(raw_bytes)
    if kind is None or kind.mime not in ALLOWED_MIME_TYPES:
        detected = kind.mime if kind else "unknown"
        raise IntakeError(
            f"Invalid file type: {detected}. Must be JPEG or PNG."
        )

    # SEC-03: EXIF strip via Pillow
    # Use filetype.mime (returns "image/jpeg") NOT Pillow's Image.format ("JPEG")
    # for the MIME type returned — see Pitfall 3 in RESEARCH.md
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img = ImageOps.exif_transpose(img)  # apply EXIF rotation, then discard EXIF

        # Reconstruct image from pixel data only — zero metadata carried over
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(list(img.getdata()))

        out_buffer = io.BytesIO()
        fmt = "JPEG" if kind.mime == "image/jpeg" else "PNG"
        clean_img.save(out_buffer, format=fmt)
        clean_bytes = out_buffer.getvalue()
    except Image.DecompressionBombError:
        raise IntakeError(
            "Image dimensions exceed safe limits (possible decompression bomb)"
        )
    except Exception as e:
        raise IntakeError(f"Image validation failed: {e}") from e

    return clean_bytes, kind.mime  # mime_type from filetype, not Pillow
