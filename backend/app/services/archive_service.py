import hashlib
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger("app.services.archive")

ALLOWED_EXTENSIONS: Set[str] = {".txt", ".json"}


class ArchiveSecurityError(AppException):
    """Raised when an archive fails security or integrity validation."""

    def __init__(self, message: str, details: Optional[Dict[str, str]] = None) -> None:
        super().__init__(message=message, status_code=400, details=details or {})


def compute_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_string_sha256(content: str) -> str:
    """Calculate SHA-256 hash of a string (UTF-8 encoded)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def is_safe_zip_entry(target_dir: Path, entry_name: str) -> bool:
    """Validate that entry_name does not escape target_dir via traversal or absolute path."""
    # Reject absolute paths or drive prefixes
    if os.path.isabs(entry_name) or (len(entry_name) > 1 and entry_name[1] == ":"):
        return False

    # Normalize target directory and prospective destination path
    resolved_target = target_dir.resolve()
    destination = (resolved_target / entry_name).resolve()

    try:
        # Destination must be relative to or child of target_dir
        destination.relative_to(resolved_target)
        return True
    except ValueError:
        return False


def validate_and_extract_archive(
    archive_path: Path,
    destination_dir: Path,
    max_size_bytes: int = 52428800,  # 50 MB
    max_files: int = 500,
    allowed_extensions: Optional[Set[str]] = None,
) -> Tuple[List[Path], str]:
    """Safely validate and extract a zip archive to a destination directory.

    Returns:
        Tuple of (list of extracted Paths, archive SHA-256 checksum).
    Raises:
        ArchiveSecurityError if any security constraint is violated.
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS

    if not archive_path.exists():
        raise ArchiveSecurityError(
            f"Archive file not found: {archive_path}",
            details={"archive_path": str(archive_path)},
        )

    # Check compressed size
    compressed_size = archive_path.stat().st_size
    if compressed_size > max_size_bytes:
        raise ArchiveSecurityError(
            f"Archive size ({compressed_size} bytes) exceeds limit ({max_size_bytes} bytes)",
            details={"size": str(compressed_size), "max": str(max_size_bytes)},
        )

    archive_sha256 = compute_sha256(archive_path)

    destination_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="catalist_extract_") as temp_dir_str:
        temp_dir = Path(temp_dir_str).resolve()

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                infolist = zf.infolist()

                if len(infolist) > max_files:
                    raise ArchiveSecurityError(
                        f"Archive contains {len(infolist)} entries, exceeding limit of {max_files}",
                        details={"file_count": str(len(infolist)), "max_files": str(max_files)},
                    )

                total_uncompressed = 0
                for info in infolist:
                    total_uncompressed += info.file_size
                    if total_uncompressed > max_size_bytes * 5:  # Zip bomb protection
                        raise ArchiveSecurityError(
                            "Uncompressed size exceeds decompression limit",
                            details={"uncompressed_bytes": str(total_uncompressed)},
                        )

                    entry_path = Path(info.filename)

                    # Skip directory markers
                    if info.is_dir() or info.filename.endswith("/"):
                        continue

                    # Validate path traversal
                    if not is_safe_zip_entry(temp_dir, info.filename):
                        logger.warning(
                            f"Rejected unsafe archive entry path traversal: {info.filename}"
                        )
                        raise ArchiveSecurityError(
                            f"Zip traversal entry detected: {info.filename}",
                            details={"entry": info.filename},
                        )

                    # Validate extension
                    suffix = entry_path.suffix.lower()
                    if suffix not in allowed_extensions:
                        logger.warning(
                            f"Rejected disallowed archive file extension: {info.filename} ({suffix})"
                        )
                        raise ArchiveSecurityError(
                            f"Disallowed file extension '{suffix}' for entry {info.filename}",
                            details={"entry": info.filename, "extension": suffix},
                        )

                    # Check for symlinks or device files (Unix mode attributes)
                    # Mode 0o120000 indicates symlink
                    if (info.external_attr >> 16) & 0o120000 == 0o120000:
                        raise ArchiveSecurityError(
                            f"Symlink entry rejected in archive: {info.filename}",
                            details={"entry": info.filename},
                        )

                # All entries verified safe, extract to temporary staging directory
                zf.extractall(path=temp_dir)

        except zipfile.BadZipFile as e:
            raise ArchiveSecurityError(
                f"Corrupt or invalid zip archive: {e}",
                details={"archive_path": str(archive_path)},
            ) from e

        # Promote extracted files into destination_dir
        extracted_paths: List[Path] = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                source_file = Path(root) / file
                rel_path = source_file.relative_to(temp_dir)
                dest_file = destination_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_file)
                extracted_paths.append(dest_file)

    logger.info(
        f"Safely extracted {len(extracted_paths)} files from archive to {destination_dir} "
        f"[archive_sha256: {archive_sha256[:12]}...]"
    )
    return extracted_paths, archive_sha256
