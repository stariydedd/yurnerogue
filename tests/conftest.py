import os
import sys
from pathlib import Path

# Игровые модули используют абсолютные импорты с корнем в game/ (требование pygbag).
sys.path.insert(0, str(Path(__file__).parent.parent / "game"))

# Тесты game flow гоняют pygame без окна (CI, headless).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
