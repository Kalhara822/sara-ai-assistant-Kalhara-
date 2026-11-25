import sys
sys.path.insert(0, '.')
from ai.ollama_engine import OllamaIntentEngine

engine = OllamaIntentEngine()

# Test bare app names
bare_tests = ['telegram', 'whatsapp', 'chrome', 'spotify', 'discord', 'notepad', 'calculator']
print("\n--- Bare App Name Tests ---")
for test in bare_tests:
    result = engine._rule_based_fallback(test)
    if result:
        print(f"  '{test}' -> action={result.action}, app={result.application}")
    else:
        print(f"  '{test}' -> None (will go to LLM)")

# Test open commands
print("\n--- Open Command Tests ---")
open_tests = ['open chrome', 'open downloads', 'open desktop', 'open telegram']
for test in open_tests:
    result = engine._rule_based_fallback(test)
    if result:
        print(f"  '{test}' -> action={result.action}, app={result.application}")
    else:
        print(f"  '{test}' -> None (will go to LLM)")

# Test folder with app=None
print("\n--- Folder Command with app=None ---")
from commands.folder_commands import OpenFolderCommand
cmd = OpenFolderCommand()
for params in [
    {'application': None, 'query': 'downloads'},
    {'application': 'desktop', 'query': None},
    {'application': None, 'query': None, 'params': {}},
]:
    result = cmd.execute(params)
    print(f"  params={params} -> {result}")
