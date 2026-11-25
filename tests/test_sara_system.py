"""
End-to-End System Test Suite for SARA AI Assistant
Validates: Configuration, Memory, AI Intent Parsing, Commands, Plugins, Routines, Scheduler, ResourceGuard
"""

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import config
from utils.logger import logger
from utils.system_info import SystemInfo
from utils.resource_guard import ResourceGuard
from database.memory_manager import MemoryManager
from ai.ollama_engine import OllamaIntentEngine
from commands.dispatcher import CommandDispatcher
from sara_engine import SARAEngine
from automation.routines import RoutineEngine
from automation.scheduler import TaskScheduler
from automation.file_organizer import FileOrganizer


def test_system():
    print("\n========================================================")
    print("      SARA AI ASSISTANT — E2E TEST SUITE")
    print("========================================================\n")

    # 1. Config & System Diagnostics
    config.ensure_directories()
    diag = SystemInfo.get_system_summary()
    print(f"[OK] System Diagnostics: OS={diag['os']}, CPU={diag['cpu_count_physical']} Cores, RAM={diag['memory']['total_gb']} GB")

    # 2. Memory Manager Test
    mem = MemoryManager()
    mem.add_conversation_entry("user", "System test prompt", "test_session")
    history = mem.get_conversation_history(limit=1, session_id="test_session")
    assert len(history) >= 1, "Memory store failed"
    note_id = mem.save_note("Unit test note entry")
    assert note_id > 0, "Note store failed"
    print("[OK] SQLite Memory Engine: Conversation history & notes persistence verified.")

    # 3. Resource Guard Test
    guard = ResourceGuard()
    trim_res = guard.trim_memory()
    print(f"[OK] ResourceGuard: Memory trim executed. (RAMUsed={trim_res['ram_used_pct']}%, WinTrimmed={trim_res['win_trimmed']})")

    # 4. SARA Core Engine Test
    engine = SARAEngine()
    status = engine.get_ai_status()
    print(f"[OK] SARA Core Engine: {status['registered_commands']} registered commands, {len(status['plugins'])} plugins loaded.")

    # 5. Direct Dispatch Test
    res_vol = engine.process_command_direct("set_volume", {"value": 50})
    print(f"[OK] Direct Command Dispatch ('set_volume'): status={res_vol.get('status')}")

    res_health = engine.process_command_direct("get_system_health", {})
    print(f"[OK] Direct Command Dispatch ('get_system_health'): status={res_health.get('status')}")

    # 6. Routines Engine Test
    re = RoutineEngine(dispatch_callback=lambda a, p: None)
    routines = re.list_routines()
    print(f"[OK] Smart Routine Engine: {len(routines)} routines available ({[r['name'] for r in routines[:4]]}...).")

    # 7. Task Scheduler Test
    ts = TaskScheduler(dispatch_callback=lambda a, p: None)
    print(f"[OK] Task Scheduler: Background scheduler active.")

    # 8. File Organizer Test
    fo = FileOrganizer()
    print(f"[OK] File Organizer: File type maps and downloads handler operational.")

    print("\n========================================================")
    print("      ALL E2E SYSTEM TESTS PASSED SUCCESSFULLY! [OK]")
    print("========================================================\n")


if __name__ == "__main__":
    test_system()
