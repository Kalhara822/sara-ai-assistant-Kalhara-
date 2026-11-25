"""
File Management Commands
Handles: create_folder, rename_file, delete_file, move_file, copy_file,
         search_files, show_recent_files, compress_files, extract_zip
Uses: Python stdlib (os, shutil, zipfile, glob) — no new packages needed.
"""

import os
import re
import shutil
import zipfile
import glob
import subprocess
from typing import Dict, Any, List
from commands.base import BaseCommand
from utils.logger import logger


def _expand(path: str) -> str:
    """Expand environment variables and user home in a path."""
    return os.path.expandvars(os.path.expanduser(path))


class CreateFolderCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "create_folder"

    @property
    def description(self) -> str:
        return "Create a new folder at a specified path (defaults to Desktop)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            name = (params.get("query") or params.get("application") or "").strip()
            if not name:
                return {"status": "error", "message": "Please specify a folder name. E.g. 'create folder MyProject'."}
            # If no path separator, create on Desktop
            if not os.path.isabs(name) and "\\" not in name and "/" not in name:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                path = os.path.join(desktop, name)
            else:
                path = _expand(name)
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created folder: {path}")
            return {"status": "success", "message": f"Folder '{name}' created on Desktop."}
        except Exception as e:
            logger.error(f"Create folder error: {e}")
            return {"status": "error", "message": str(e)}


class RenameFileCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "rename_file"

    @property
    def description(self) -> str:
        return "Rename a file or folder."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = (params.get("query") or "").strip()
            # Expect format: "rename <old> to <new>"
            m = re.search(r"(.+?)\s+to\s+(.+)", query, re.IGNORECASE)
            if not m:
                return {"status": "error", "message": "Say something like: 'rename report.txt to final_report.txt'"}
            old_name = m.group(1).strip().strip('"')
            new_name = m.group(2).strip().strip('"')
            # Search Desktop and common locations
            search_dirs = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
            ]
            old_path = None
            for d in search_dirs:
                candidate = os.path.join(d, old_name)
                if os.path.exists(candidate):
                    old_path = candidate
                    break
            if not old_path and os.path.exists(old_name):
                old_path = old_name
            if not old_path:
                return {"status": "error", "message": f"Could not find '{old_name}' on Desktop, Documents, or Downloads."}
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            os.rename(old_path, new_path)
            return {"status": "success", "message": f"Renamed '{old_name}' to '{new_name}'."}
        except Exception as e:
            logger.error(f"Rename file error: {e}")
            return {"status": "error", "message": str(e)}


class DeleteFileCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "delete_file"

    @property
    def requires_confirmation(self) -> bool:
        return True

    @property
    def description(self) -> str:
        return "Delete a file or folder (sends to Recycle Bin if possible)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            name = (params.get("query") or params.get("application") or "").strip().strip('"')
            if not name:
                return {"status": "error", "message": "Please specify a file or folder name to delete."}
            search_dirs = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
            ]
            target = None
            for d in search_dirs:
                candidate = os.path.join(d, name)
                if os.path.exists(candidate):
                    target = candidate
                    break
            if not target and os.path.exists(name):
                target = name
            if not target:
                return {"status": "error", "message": f"Could not find '{name}'."}
            # Send to recycle bin via shell command
            try:
                import winshell
                winshell.delete_file(target, no_confirm=True, allow_undo=True)
            except ImportError:
                # Fallback: use PowerShell Remove-Item
                subprocess.run(["powershell", "-NoProfile", "-Command",
                                f'Remove-Item -Path "{target}" -Recurse -Force'], timeout=10)
            logger.info(f"Deleted: {target}")
            return {"status": "success", "message": f"Deleted '{name}'."}
        except Exception as e:
            logger.error(f"Delete file error: {e}")
            return {"status": "error", "message": str(e)}


class MoveFileCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "move_file"

    @property
    def description(self) -> str:
        return "Move a file from one location to another."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = (params.get("query") or "").strip()
            # Expect: "move <file> to <destination>"
            m = re.search(r"(.+?)\s+to\s+(.+)", query, re.IGNORECASE)
            if not m:
                return {"status": "error", "message": "Say: 'move report.txt to Documents'"}
            src_name = m.group(1).strip().strip('"')
            dest_name = m.group(2).strip().strip('"')
            # Resolve source
            known_dirs = {
                "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
                "documents": os.path.join(os.path.expanduser("~"), "Documents"),
                "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
                "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
                "music": os.path.join(os.path.expanduser("~"), "Music"),
                "videos": os.path.join(os.path.expanduser("~"), "Videos"),
            }
            src = None
            for d in known_dirs.values():
                candidate = os.path.join(d, src_name)
                if os.path.exists(candidate):
                    src = candidate
                    break
            if not src and os.path.exists(src_name):
                src = src_name
            if not src:
                return {"status": "error", "message": f"Could not find '{src_name}'."}
            # Resolve destination
            dest_dir = known_dirs.get(dest_name.lower(), _expand(dest_name))
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            shutil.move(src, dest_dir)
            return {"status": "success", "message": f"Moved '{src_name}' to '{dest_name}'."}
        except Exception as e:
            logger.error(f"Move file error: {e}")
            return {"status": "error", "message": str(e)}


class CopyFileCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "copy_file"

    @property
    def description(self) -> str:
        return "Copy a file to another location."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = (params.get("query") or "").strip()
            m = re.search(r"(.+?)\s+to\s+(.+)", query, re.IGNORECASE)
            if not m:
                return {"status": "error", "message": "Say: 'copy report.txt to Desktop'"}
            src_name = m.group(1).strip().strip('"')
            dest_name = m.group(2).strip().strip('"')
            known_dirs = {
                "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
                "documents": os.path.join(os.path.expanduser("~"), "Documents"),
                "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
                "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
            }
            src = None
            for d in known_dirs.values():
                candidate = os.path.join(d, src_name)
                if os.path.exists(candidate):
                    src = candidate
                    break
            if not src and os.path.exists(src_name):
                src = src_name
            if not src:
                return {"status": "error", "message": f"Could not find '{src_name}'."}
            dest_dir = known_dirs.get(dest_name.lower(), _expand(dest_name))
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(src, dest_dir)
            return {"status": "success", "message": f"Copied '{src_name}' to '{dest_name}'."}
        except Exception as e:
            logger.error(f"Copy file error: {e}")
            return {"status": "error", "message": str(e)}


class SearchFilesCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return "Search for files by name across common user folders."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = (params.get("query") or params.get("application") or "").strip()
            if not query:
                return {"status": "error", "message": "Please specify what to search for. E.g. 'search for resume.pdf'"}
            search_root = os.path.expanduser("~")
            results: List[str] = []
            for root, dirs, files in os.walk(search_root):
                # Skip hidden and system dirs
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                           ['AppData', '$Recycle.Bin', 'Windows', 'System32']]
                for f in files:
                    if query.lower() in f.lower():
                        results.append(os.path.join(root, f))
                if len(results) >= 10:
                    break
            if results:
                msg = f"Found {len(results)} file(s) matching '{query}':\n" + "\n".join(results[:10])
                # Open the folder of the first result
                if results:
                    subprocess.Popen(f'explorer /select,"{results[0]}"', shell=True)
            else:
                msg = f"No files found matching '{query}'."
            return {"status": "success", "message": msg, "files": results}
        except Exception as e:
            logger.error(f"Search files error: {e}")
            return {"status": "error", "message": str(e)}


class ShowRecentFilesCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "show_recent_files"

    @property
    def description(self) -> str:
        return "Open the Windows Recent files folder."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            recent = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent")
            subprocess.Popen(f'explorer "{recent}"', shell=True)
            return {"status": "success", "message": "Opened your Recent files folder."}
        except Exception as e:
            logger.error(f"Show recent files error: {e}")
            return {"status": "error", "message": str(e)}


class CompressFilesCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "compress_files"

    @property
    def description(self) -> str:
        return "Compress a file or folder into a ZIP archive."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = (params.get("query") or params.get("application") or "").strip().strip('"')
            if not query:
                return {"status": "error", "message": "Please specify what to compress. E.g. 'compress MyFolder'"}
            known_dirs = {
                "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
                "documents": os.path.join(os.path.expanduser("~"), "Documents"),
                "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            }
            src = None
            for d in known_dirs.values():
                candidate = os.path.join(d, query)
                if os.path.exists(candidate):
                    src = candidate
                    break
            if not src and os.path.exists(query):
                src = query
            if not src:
                return {"status": "error", "message": f"Could not find '{query}' to compress."}
            zip_name = os.path.basename(src.rstrip("/\\")) + ".zip"
            zip_path = os.path.join(os.path.dirname(src), zip_name)
            if os.path.isdir(src):
                shutil.make_archive(src, 'zip', os.path.dirname(src), os.path.basename(src))
            else:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(src, os.path.basename(src))
            return {"status": "success", "message": f"Compressed '{query}' into '{zip_name}'."}
        except Exception as e:
            logger.error(f"Compress files error: {e}")
            return {"status": "error", "message": str(e)}


class ExtractZipCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "extract_zip"

    @property
    def description(self) -> str:
        return "Extract a ZIP archive to the same directory."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            query = (params.get("query") or params.get("application") or "").strip().strip('"')
            if not query:
                return {"status": "error", "message": "Please specify which ZIP file to extract. E.g. 'extract archive.zip'"}
            if not query.endswith(".zip"):
                query = query + ".zip"
            known_dirs = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.join(os.path.expanduser("~"), "Documents"),
            ]
            src = None
            for d in known_dirs:
                candidate = os.path.join(d, query)
                if os.path.exists(candidate):
                    src = candidate
                    break
            if not src and os.path.exists(query):
                src = query
            if not src:
                return {"status": "error", "message": f"Could not find '{query}'."}
            extract_to = os.path.splitext(src)[0]
            os.makedirs(extract_to, exist_ok=True)
            with zipfile.ZipFile(src, 'r') as zf:
                zf.extractall(extract_to)
            subprocess.Popen(f'explorer "{extract_to}"', shell=True)
            return {"status": "success", "message": f"Extracted '{os.path.basename(src)}' to '{os.path.basename(extract_to)}'."}
        except Exception as e:
            logger.error(f"Extract ZIP error: {e}")
            return {"status": "error", "message": str(e)}
