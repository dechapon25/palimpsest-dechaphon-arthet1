"""Unit tests for security intake layer (SEC-01 through SEC-04).

All tests are pure Python logic — no API calls, no network access, no ADK imports.
"""

import io

import pytest
from PIL import Image

from palimpsest.security.intake import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    IntakeError,
    validate_and_clean,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jpeg(tmp_path, name="test.jpg", size=(100, 80), color=(128, 64, 32), exif=None):
    """Create a minimal JPEG file and return its path."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    if exif is not None:
        img.save(buf, format="JPEG", exif=exif)
    else:
        img.save(buf, format="JPEG")
    path = tmp_path / name
    path.write_bytes(buf.getvalue())
    return str(path)


def _make_png(tmp_path, name="test.png", size=(100, 80), color=(64, 128, 32)):
    """Create a minimal PNG file and return its path."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    path = tmp_path / name
    path.write_bytes(buf.getvalue())
    return str(path)


# ---------------------------------------------------------------------------
# SEC-02: File size rejection
# ---------------------------------------------------------------------------

def test_rejects_oversized_file(tmp_path):
    """A file over 20 MB raises IntakeError with 'too large' in message."""
    large_file = tmp_path / "big.jpg"
    large_file.write_bytes(b"\x00" * (20 * 1024 * 1024 + 1))
    with pytest.raises(IntakeError, match="too large"):
        validate_and_clean(str(large_file))


def test_accepts_file_at_exact_limit(tmp_path):
    """A file exactly at the 20 MB limit should NOT be rejected for size.

    Note: this file has garbage bytes so it will fail the type check,
    but it must NOT fail with 'too large'.
    """
    edge_file = tmp_path / "edge.bin"
    edge_file.write_bytes(b"\x00" * (20 * 1024 * 1024))
    with pytest.raises(IntakeError, match="Invalid file type"):
        validate_and_clean(str(edge_file))


# ---------------------------------------------------------------------------
# SEC-01: Magic-byte file type validation
# ---------------------------------------------------------------------------

def test_rejects_pdf(tmp_path):
    """A file with PDF magic bytes raises IntakeError with 'Invalid file type'."""
    pdf_file = tmp_path / "doc.pdf"
    pdf_file.write_bytes(b"%PDF-1.4" + b"\x00" * 100)
    with pytest.raises(IntakeError, match="Invalid file type"):
        validate_and_clean(str(pdf_file))


def test_accepts_jpeg(tmp_path):
    """A valid JPEG under 20 MB passes validation and returns clean bytes with mime 'image/jpeg'."""
    path = _make_jpeg(tmp_path)
    clean_bytes, mime_type = validate_and_clean(path)
    assert mime_type == "image/jpeg"
    assert len(clean_bytes) > 0
    # Verify returned bytes are a valid JPEG
    img = Image.open(io.BytesIO(clean_bytes))
    assert img.format == "JPEG"


def test_accepts_png(tmp_path):
    """A valid PNG under 20 MB passes validation and returns clean bytes with mime 'image/png'."""
    path = _make_png(tmp_path)
    clean_bytes, mime_type = validate_and_clean(path)
    assert mime_type == "image/png"
    assert len(clean_bytes) > 0
    # Verify returned bytes are a valid PNG
    img = Image.open(io.BytesIO(clean_bytes))
    assert img.format == "PNG"


def test_extension_is_irrelevant(tmp_path):
    """A PNG file named with .jpg extension passes validation — only magic bytes matter."""
    # Create a PNG but save it with .jpg extension
    path = _make_png(tmp_path, name="disguised.jpg")
    clean_bytes, mime_type = validate_and_clean(path)
    # filetype detects PNG magic bytes regardless of .jpg extension
    assert mime_type == "image/png"


# ---------------------------------------------------------------------------
# SEC-03: EXIF metadata stripping
# ---------------------------------------------------------------------------

def test_exif_strip(tmp_path):
    """EXIF strip produces clean output: Pillow cannot read EXIF metadata from returned bytes."""
    # Create a JPEG with EXIF data using Pillow's built-in Exif API
    img = Image.new("RGB", (100, 80), color=(128, 64, 32))
    exif = img.getexif()
    # Tag 271 = Make, Tag 272 = Model (standard EXIF IFD tags)
    exif[271] = "TestCamera"
    exif[272] = "TestModel"

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif.tobytes())

    # Verify EXIF was actually written to the source file
    buf.seek(0)
    source_img = Image.open(buf)
    source_exif = source_img.getexif()
    assert 271 in source_exif, "Test setup failed: EXIF not written to source image"

    path = tmp_path / "exif_test.jpg"
    buf.seek(0)
    path.write_bytes(buf.getvalue())

    clean_bytes, mime_type = validate_and_clean(str(path))
    assert mime_type == "image/jpeg"

    # Verify EXIF is stripped from the clean output
    clean_img = Image.open(io.BytesIO(clean_bytes))
    exif_data = clean_img.getexif()
    assert len(exif_data) == 0, f"EXIF data should be empty but got: {dict(exif_data)}"


def test_exif_strip_preserves_dimensions(tmp_path):
    """EXIF stripping preserves image pixel dimensions."""
    path = _make_jpeg(tmp_path, size=(200, 150))
    clean_bytes, _ = validate_and_clean(path)
    clean_img = Image.open(io.BytesIO(clean_bytes))
    assert clean_img.size == (200, 150)


# ---------------------------------------------------------------------------
# Constants validation
# ---------------------------------------------------------------------------

def test_max_file_size_constant():
    """MAX_FILE_SIZE_BYTES equals 20 MB."""
    assert MAX_FILE_SIZE_BYTES == 20 * 1024 * 1024


def test_allowed_mime_types():
    """ALLOWED_MIME_TYPES contains exactly JPEG and PNG."""
    assert ALLOWED_MIME_TYPES == {"image/jpeg", "image/png"}
