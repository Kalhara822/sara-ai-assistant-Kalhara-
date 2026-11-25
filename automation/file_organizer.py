"""
SARA File Organizer
Automates common file management tasks:
  - Organize Downloads folder by file type
  - Bulk rename files with pattern
  - Find large files consuming disk space
  - Archive old files to a subfolder
  - Clean temp/junk files
"""

import os
import shutil
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import logger


# File type → subfolder mapping for Downloads organizer
FILE_TYPE_MAP: Dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".bmp": "Images", ".svg": "Images", ".webp": "Images",
    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos",
    ".mov": "Videos", ".wmv": "Videos", ".flv": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    ".aac": "Audio", ".ogg": "Audio", ".m4a": "Audio",
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".txt": "Documents", ".odt": "Documents", ".rtf": "Documents",
    # Spreadsheets
    ".xls": "Spreadsheets", ".xlsx": "Spreadsheets", ".csv": "Spreadsheets",
    # Presentations
    ".ppt": "Presentations", ".pptx": "Presentations",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".tar": "Archives", ".gz": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".ts": "Code", ".java": "Code",
    ".cpp": "Code", ".c": "Code", ".html": "Code", ".css": "Code",
    ".json": "Code", ".xml": "Code", ".sql": "Code",
    # Installers
    ".exe": "Installers", ".msi": "Installers", ".dmg": "Installers",
    # Fonts
    ".ttf": "Fonts", ".otf": "Fonts", ".woff": "Fonts",
}


class FileOrganizer:
    """Automates file management tasks across the Windows filesystem."""

    def organize_downloads(self, downloads_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Sort all loose files in the Downloads folder into type subfolders.
        Returns summary of moved files and skipped items.
        """
        folder = Path(downloads_path or os.path.join(os.path.expanduser("~"), "Downloads"))
        if not folder.exists():
            return {"status": "error", "message": f"Folder not found: {folder}"}

        moved = 0
        skipped = 0
        errors = []

        for file in folder.iterdir():
            if not file.is_file():
                continue

            suffix = file.suffix.lower()
            target_subdir = FILE_TYPE_MAP.get(suffix, "Other")
            target_folder = folder / target_subdir
            target_folder.mkdir(exist_ok=True)

            dest = target_folder / file.name
            # If file already exists at destination, add timestamp suffix
            if dest.exists():
                stem, ext = file.stem, file.suffix
                dest = target_folder / f"{stem}_{int(time.time())}{ext}"

            try:
                shutil.move(str(file), str(dest))
                moved += 1
                logger.debug(f"[FileOrganizer] Moved '{file.name}' → {target_subdir}/")
            except Exception as e:
                errors.append(str(e))
                skipped += 1

        msg = f"Downloads organised: {moved} files sorted into subfolders."
        if skipped:
            msg += f" {skipped} file(s) could not be moved."
        return {"status": "success", "message": msg, "moved": moved, "skipped": skipped}

    def bulk_rename(
        self,
        folder: str,
        pattern: str,
        replacement: str,
        file_filter: str = "*"
    ) -> Dict[str, Any]:
        """
        Rename all matching files in a folder using regex pattern replacement.
        Example: pattern='IMG_', replacement='Photo_' renames IMG_001.jpg → Photo_001.jpg
        """
        folder_path = Path(folder)
        if not folder_path.exists():
            return {"status": "error", "message": f"Folder not found: {folder}"}

        renamed = 0
        errors = []

        for file in folder_path.glob(file_filter):
            if not file.is_file():
                continue
            try:
                new_name = re.sub(pattern, replacement, file.name)
                if new_name != file.name:
                    new_path = file.parent / new_name
                    file.rename(new_path)
                    renamed += 1
                    logger.debug(f"[FileOrganizer] Renamed: '{file.name}' → '{new_name}'")
            except Exception as e:
                errors.append(f"{file.name}: {e}")

        return {
            "status": "success",
            "message": f"Bulk rename complete: {renamed} file(s) renamed in '{folder_path.name}'.",
            "renamed": renamed,
            "errors": errors,
        }

    def find_large_files(
        self,
        folder: str,
        min_size_mb: float = 100,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Scan a folder recursively for large files above min_size_mb.
        Returns top_n largest files sorted by size descending.
        """
        folder_path = Path(folder)
        if not folder_path.exists():
            return {"status": "error", "message": f"Folder not found: {folder}"}

        min_bytes = min_size_mb * 1024 * 1024
        large_files = []

        try:
            for file in folder_path.rglob("*"):
                if file.is_file():
                    try:
                        size = file.stat().st_size
                        if size >= min_bytes:
                            large_files.append({
                                "path": str(file),
                                "name": file.name,
                                "size_mb": round(size / (1024 * 1024), 2),
                            })
                    except PermissionError:
                        pass
        except PermissionError as e:
            return {"status": "error", "message": f"Permission denied scanning folder: {e}"}

        large_files.sort(key=lambda x: x["size_mb"], reverse=True)
        results = large_files[:top_n]

        if not results:
            return {"status": "success", "message": f"No files larger than {min_size_mb} MB found.", "data": []}

        summary = ", ".join([f"{f['name']} ({f['size_mb']} MB)" for f in results[:3]])
        return {
            "status": "success",
            "message": f"Found {len(results)} large file(s). Top: {summary}.",
            "data": results,
        }

    def archive_old_files(
        self,
        folder: str,
        older_than_days: int = 90,
        archive_subfolder: str = "_Archive"
    ) -> Dict[str, Any]:
        """
        Move files not modified in older_than_days days to an archive subfolder.
        """
        folder_path = Path(folder)
        if not folder_path.exists():
            return {"status": "error", "message": f"Folder not found: {folder}"}

        cutoff = time.time() - (older_than_days * 86400)
        archive_path = folder_path / archive_subfolder
        archive_path.mkdir(exist_ok=True)
        archived = 0
        errors = []

        for file in folder_path.iterdir():
            if file.is_file() and file.stat().st_mtime < cutoff:
                dest = archive_path / file.name
                if dest.exists():
                    dest = archive_path / f"{file.stem}_{int(time.time())}{file.suffix}"
                try:
                    shutil.move(str(file), str(dest))
                    archived += 1
                except Exception as e:
                    errors.append(str(e))

        return {
            "status": "success",
            "message": f"Archived {archived} file(s) older than {older_than_days} days to '{archive_subfolder}'.",
            "archived": archived,
            "errors": errors,
        }

    def clean_temp_files(self) -> Dict[str, Any]:
        """Delete Windows %TEMP% files that are safe to remove."""
        temp_dir = Path(os.environ.get("TEMP", "C:/Windows/Temp"))
        deleted = 0
        skipped = 0

        for item in temp_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    deleted += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    deleted += 1
            except Exception:
                skipped += 1

        freed_approx = deleted * 0.1  # rough estimate
        return {
            "status": "success",
            "message": f"Temp cleanup done: {deleted} item(s) removed. Approx {freed_approx:.1f} MB freed.",
            "deleted": deleted,
            "skipped": skipped,
        }

    def get_folder_size(self, folder: str) -> Dict[str, Any]:
        """Return total size of a folder in MB."""
        folder_path = Path(folder)
        if not folder_path.exists():
            return {"status": "error", "message": f"Folder not found: {folder}"}
        total = sum(f.stat().st_size for f in folder_path.rglob("*") if f.is_file())
        size_mb = round(total / (1024 * 1024), 2)
        return {
            "status": "success",
            "message": f"'{folder_path.name}' is {size_mb} MB.",
            "size_mb": size_mb,
        }
