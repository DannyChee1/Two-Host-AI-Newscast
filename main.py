"""
Two-Host AI Newscast Generator - Main Entry Point

Usage:
    python main.py --personas config/personas.json --minutes 7 --topics tech,world
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run main
from main import main

if __name__ == "__main__":
    main()

