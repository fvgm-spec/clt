import sys
import os
from unittest.mock import patch, MagicMock

ROOT = os.path.dirname(os.path.dirname(__file__))

# prepend subproject paths so local modules take priority over PyPI packages (e.g. deepl)
for subdir in ("espn-results-cli", "deepl", "spotify"):
    path = os.path.join(ROOT, subdir)
    if path not in sys.path:
        sys.path.insert(0, path)

# translator.py instantiates deepl.Translator at import time — mock it before collection
os.environ.setdefault("DEEPL_API_KEY", "dummy")
sys.modules["deepl"] = MagicMock()
