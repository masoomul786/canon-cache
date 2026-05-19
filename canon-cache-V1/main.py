#!/usr/bin/env python3
"""
CanonCache — Entry Point
Semantic KV-Cache Canonicalization Research Tool

Usage:
    python main.py

Requirements:
    pip install requests tkinter
    LM Studio running locally with a model loaded.
"""

import sys
import os

# Ensure project root is on path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def check_dependencies():
    """Check required packages are installed."""
    missing = []
    try:
        import requests  # noqa
    except ImportError:
        missing.append("requests")
    try:
        import tkinter  # noqa
    except ImportError:
        missing.append("tkinter (install python3-tk on Linux)")

    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"  pip install {pkg}")
        sys.exit(1)


def main():
    check_dependencies()

    from ui.app import CanonCacheApp

    app = CanonCacheApp()
    app.mainloop()


if __name__ == "__main__":
    main()
