"""Root launcher entrypoint for Streamlit ATS application."""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.ui.app import main

if __name__ == "__main__":
    main()
