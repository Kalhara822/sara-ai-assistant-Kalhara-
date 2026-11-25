"""
Folder/Directory Commands for SARA
Opens any Windows folder — standard ones (Desktop, Downloads, Documents, etc.)
or any custom path the user speaks.
"""

import os
import subprocess
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger


# Map common spoken folder names to real Windows paths
FOLDER_MAP: Dict[str, str] = {
    # Standard user folders
    "desktop":          os.path.join(os.path.expanduser("~"), "Desktop"),
    "downloads":        os.path.join(os.path.expanduser("~"), "Downloads"),
    "documents":        os.path.join(os.path.expanduser("~"), "Documents"),
    "music":            os.path.join(os.path.expanduser("~"), "Music"),
    "videos":           os.path.join(os.path.expanduser("~"), "Videos"),
    "pictures":         os.path.join(os.path.expanduser("~"), "Pictures"),
    "photos":           os.path.join(os.path.expanduser("~"), "Pictures"),
    # System folders
    "this pc":          "explorer.exe",           # Opens 'This PC' root
    "my computer":      "explorer.exe",
    "computer":         "explorer.exe",
    "c drive":          "C:\\",
    "c:":               "C:\\",
    "d drive":          "D:\\",
    "d:":               "D:\\",
    "program files":    "C:\\Program Files",
    "temp":             os.environ.get("TEMP", "C:\\Temp"),
    "recycle bin":      "shell:RecycleBinFolder",
    "startup":          "shell:Startup",
    "appdata":          os.environ.get("APPDATA", ""),
    # Quick access
    "projects":         os.path.join(os.path.expanduser("~"), "Documents", "Projects"),
    "sara":             "D:\\IT Projects\\sara AI",
    "it projects":      "D:\\IT Projects",
}


class OpenFolderCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "open_folder"

    @property
    def description(self) -> str:
        return "Open any Windows folder — Desktop, Downloads, Documents, D: drive, custom paths, etc."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Accept folder name from 'application', 'query', or 'params.folder'
        # Qwen sometimes puts the folder in 'query' or leaves 'application' as None
        folder_raw = (
            str(params.get("application") or
                params.get("query") or
                params.get("params", {}).get("folder", "") or
                "").lower().strip()
        )

        # If still empty, check if original user_input was passed through
        if not folder_raw:
            return {"status": "error", "message": "Please tell me which folder to open. Say something like 'open Desktop' or 'open Downloads'."}

        # Clean noise words
        folder_clean = (folder_raw
            .replace("the ", "").replace(" folder", "")
            .replace(" directory", "").strip())

        # 1. Check known folder map
        path = FOLDER_MAP.get(folder_clean)

        # 2. If not in map, check if it's a real absolute path
        if not path and os.path.isabs(folder_raw) and os.path.exists(folder_raw):
            path = folder_raw

        # 3. Try to find it in common parent dirs
        if not path:
            for base in [
                os.path.expanduser("~"),
                "C:\\",
                "D:\\",
                "D:\\IT Projects",
                os.path.join(os.path.expanduser("~"), "Documents"),
            ]:
                candidate = os.path.join(base, folder_raw.title())
                if os.path.isdir(candidate):
                    path = candidate
                    break

        # 4. Still not found — try to open user home
        if not path:
            return {
                "status": "error",
                "message": f"I couldn't find a folder called '{folder_clean}'. "
                           f"Try saying 'open Desktop', 'open Downloads', or 'open Documents'."
            }

        try:
            if path == "explorer.exe":
                subprocess.Popen("explorer.exe", shell=True)
            elif path.startswith("shell:"):
                subprocess.Popen(f'explorer.exe {path}', shell=True)
            elif os.path.isdir(path):
                subprocess.Popen(f'explorer.exe "{path}"', shell=True)
            else:
                subprocess.Popen(f'explorer.exe "{path}"', shell=True)

            display_name = folder_clean.title()
            logger.info(f"Opened folder: '{display_name}' -> '{path}'")
            return {"status": "success", "message": f"Opened {display_name} folder."}

        except Exception as e:
            logger.error(f"Failed to open folder '{path}': {e}")
            return {"status": "error", "message": f"Failed to open the {folder_clean} folder."}
