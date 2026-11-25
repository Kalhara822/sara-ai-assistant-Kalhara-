import sys
sys.path.insert(0, '.')
from voice.stt_engine import _apply_corrections

tests = [
    ("open whatsup",              "open whatsapp"),
    ("open you tube",             "open youtube"),
    ("open crome",                "open chrome"),
    ("screen shot",               "screenshot"),
    ("sara open vs cold",         "open vs code"),
    ("open tele gram",            "open telegram"),
    ("lock the pc",               "lock pc"),
    ("open cap cut",              "open capcut"),
    ("open git hub",              "open github"),
    ("open g mail",               "open gmail"),
    ("ok sara, open whats app",   "open whatsapp"),
    ("search you tube for lofi",  "search youtube for lofi"),
]

all_passed = True
for raw, expected in tests:
    result = _apply_corrections(raw)
    passed = expected.lower() in result.lower()
    status = "[OK]" if passed else "[FAIL]"
    if not passed:
        all_passed = False
    print(f'{status} "{raw}" -> "{result}" (expected contains: "{expected}")')

print()
print("[ALL PASSED]" if all_passed else "[SOME TESTS FAILED]")
