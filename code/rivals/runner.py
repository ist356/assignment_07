"""
runner.py — run the scraper from Streamlit, in its own process.  *(Provided.)*

Playwright and Streamlit both want to run the show — each has its own event loop
and threads — and on Windows they clash when one runs inside the other (lesson
5-3). The fix is the one you saw in class: the Streamlit page starts the scraper
as a separate Python program, waits for it, and reads what it wrote.

    result = run_scraper(["Hilltop Grind"])
    result.returncode   # 0 when it worked
    result.stdout       # what scrape_menus.py printed
"""

import os
import subprocess
import sys

from .settings import REPO_ROOT

SCRAPER = os.path.join(REPO_ROOT, "code", "scrape_menus.py")


def run_scraper(cafes: list[str]) -> subprocess.CompletedProcess:
    """Run code/scrape_menus.py for these cafés; return the finished process."""
    return subprocess.run([sys.executable, SCRAPER, *cafes], capture_output=True,
                          text=True, cwd=REPO_ROOT, timeout=300)
