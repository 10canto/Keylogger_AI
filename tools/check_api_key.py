"""
check_api_key.py
Diagnostic script — run from project root to verify GEMMA_API_KEY loading.
Usage: python tools/check_api_key.py
"""
import logging
import os
import sys

logging.basicConfig(level=logging.WARNING,
                    format="%(levelname)s %(name)s: %(message)s")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_chat_service import AIChatService, _dotenv_loaded_from

print()
print("=== GEMMA_API_KEY Diagnostic ===")
print()

loaded = _dotenv_loaded_from if _dotenv_loaded_from else "NOT FOUND"
print(f"  .env loaded from : {loaded}")

key = os.environ.get("GEMMA_API_KEY", "").strip()
if key and key != "your_gemini_api_key_here":
    print(f"  GEMMA_API_KEY    : SET ({len(key)} chars) -- ready to use")
elif key == "your_gemini_api_key_here":
    print("  GEMMA_API_KEY    : placeholder -- replace with your real key in .env")
else:
    print("  GEMMA_API_KEY    : NOT SET")

svc = AIChatService()
print(f"  api_key_present  : {svc.api_key_present}")
print(f"  sdk_available    : {svc.sdk_available}")
print()

if svc.api_key_present:
    print("  STATUS: Ready. Restart main.py to apply.")
else:
    print("  ACTION NEEDED:")
    print("    1. Open: .env")
    print("    2. Replace 'your_gemini_api_key_here' with your real Gemini API key")
    print("    3. Save the file")
    print("    4. Run: python main.py")
print()
