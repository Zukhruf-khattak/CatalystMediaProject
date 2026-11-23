import zipfile
from pathlib import Path

import pytest

from app.services.archive_service import (
    ArchiveSecurityError,
    is_safe_zip_entry,
    validate_and_extract_archive,
)


def test_is_safe_zip_entry(tmp_path: Path) -> None:
    target_dir = tmp_path / "dataset"
    target_dir.mkdir()

    # Valid relative entries
    assert is_safe_zip_entry(target_dir, "meeting.txt") is True
    assert is_safe_zip_entry(target_dir, "sub/meeting.txt") is True

    # Traversal attempts
    assert is_safe_zip_entry(target_dir, "../outside.txt") is False
    assert is_safe_zip_entry(target_dir, "../../etc/passwd") is False
    assert is_safe_zip_entry(target_dir, "sub/../../outside.txt") is False

    # Absolute paths
    assert is_safe_zip_entry(target_dir, "/etc/passwd") is False
    assert is_safe_zip_entry(target_dir, "C:\\Windows\\System32\\cmd.exe") is False


def test_reject_archive_traversal(tmp_path: Path) -> None:
    bad_zip = tmp_path / "bad_traversal.zip"
    dest_dir = tmp_path / "extracted"

    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../traversal.txt", "malicious payload")

    with pytest.raises(ArchiveSecurityError) as exc_info:
        validate_and_extract_archive(bad_zip, dest_dir)
    assert "traversal" in str(exc_info.value).lower()


def test_reject_disallowed_file_types(tmp_path: Path) -> None:
    bad_zip = tmp_path / "bad_extension.zip"
    dest_dir = tmp_path / "extracted"

    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("malicious.exe", "binary")

    with pytest.raises(ArchiveSecurityError) as exc_info:
        validate_and_extract_archive(bad_zip, dest_dir)
    assert "disallowed" in str(exc_info.value).lower()


def test_enforce_file_count_limit(tmp_path: Path) -> None:
    too_many_zip = tmp_path / "too_many.zip"
    dest_dir = tmp_path / "extracted"

    with zipfile.ZipFile(too_many_zip, "w") as zf:
        for i in range(10):
            zf.writestr(f"file_{i}.txt", f"content {i}")

    with pytest.raises(ArchiveSecurityError) as exc_info:
        validate_and_extract_archive(too_many_zip, dest_dir, max_files=5)
    assert "exceeding limit" in str(exc_info.value).lower()


def test_enforce_archive_size_limit(tmp_path: Path) -> None:
    large_zip = tmp_path / "large.zip"
    dest_dir = tmp_path / "extracted"

    with zipfile.ZipFile(large_zip, "w") as zf:
        zf.writestr("big.txt", "x" * 2000)

    # Limit to 500 bytes compressed
    with pytest.raises(ArchiveSecurityError) as exc_info:
        validate_and_extract_archive(large_zip, dest_dir, max_size_bytes=500)
    assert "exceeds limit" in str(exc_info.value).lower()


def test_valid_archive_extraction(tmp_path: Path) -> None:
    valid_zip = tmp_path / "valid.zip"
    dest_dir = tmp_path / "extracted"

    with zipfile.ZipFile(valid_zip, "w") as zf:
        zf.writestr("ES2002a.txt", "Meeting: ES2002a\n00:00:10 Speaker A\nHello")
        zf.writestr("sub/ES2002b.txt", "Meeting: ES2002b\n00:00:10 Speaker B\nWorld")

    extracted, sha = validate_and_extract_archive(valid_zip, dest_dir)
    assert len(extracted) == 2
    assert (dest_dir / "ES2002a.txt").exists()
    assert (dest_dir / "sub" / "ES2002b.txt").exists()
    assert len(sha) == 64
