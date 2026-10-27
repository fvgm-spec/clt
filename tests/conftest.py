import sys
import os
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(__file__))

# prepend subproject paths so local modules take priority over PyPI packages (e.g. deepl)
for subdir in ("espn-results-cli", "deepl", "spotify"):
    path = os.path.join(ROOT, subdir)
    if path not in sys.path:
        sys.path.insert(0, path)

# mock modules that read env vars / external resources at import time
os.environ.setdefault("DEEPL_API_KEY", "dummy")
os.environ.setdefault("CLIENT_ID", "dummy")
os.environ.setdefault("CLIENT_SECRET", "dummy")
os.environ.setdefault("REDIRECT_URI", "http://localhost")

sys.modules["deepl"] = MagicMock()
