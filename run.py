#!/usr/bin/env python3
"""
One-click launcher.

Double-click run.bat (Windows) or run.sh (macOS/Linux) and this script:

  1. creates .env from .env.example if it is missing, so a fresh checkout starts
     without editing anything
  2. reports whether an API key was found, and says plainly what happens if not
  3. starts the server and opens a browser at it

It deliberately does no dependency installation - that is the shell wrapper's
job, because a script cannot reliably install the interpreter it is already
running under.
"""

from __future__ import annotations

import shutil
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LINE = "=" * 68


def ensure_env_file() -> bool:
    """Create .env from the template on first run. Returns True if created."""
    env = ROOT / ".env"
    template = ROOT / ".env.example"
    if env.exists() or not template.exists():
        return False
    shutil.copyfile(template, env)
    return True


def check_dependencies() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        print(LINE)
        print(" Dependencies are missing.")
        print()
        print("   pip install -r requirements.txt")
        print()
        print(" Or just use run.bat / run.sh, which does this for you.")
        print(LINE)
        sys.exit(1)


def open_browser_later(url: str, delay: float = 1.5) -> None:
    def worker() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 - a headless box is not an error
            pass

    threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    created = ensure_env_file()
    check_dependencies()

    # Imported only after .env exists, because config.py reads it at import time.
    from backend.config import settings

    url = f"http://{settings.host}:{settings.port}"

    print()
    print(LINE)
    print(" IncidentIQ")
    print(LINE)
    if created:
        print(" Created .env from .env.example (first run).")
    if settings.offline:
        print(" MODE     : OFFLINE - no API key found")
        print()
        print(" The tool will still run. It will index the evidence, build the")
        print(" timeline and rank error clusters, but it cannot do causal")
        print(" reasoning or the bias audit without a model. Every screen will")
        print(" say so.")
        print()
        print(" To enable the full analysis, put a key in .env:")
        print(f"   {ROOT / '.env'}")
        print("   ANTHROPIC_API_KEY=sk-ant-...")
    else:
        print(f" MODE     : {settings.provider}")
        print(f" MODEL    : {settings.active_model}")
    print(f" ADDRESS  : {url}")
    print()
    print(" Press Ctrl+C to stop.")
    print(LINE)
    print()

    if settings.auto_open_browser:
        open_browser_later(url)

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        log_level="warning",   # the app logs what matters; uvicorn's noise is not it
        access_log=False,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
