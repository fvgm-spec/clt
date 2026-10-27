import sys
import os

ROOT = os.path.dirname(os.path.dirname(__file__))

# prepend subproject paths so local modules take priority over PyPI packages (e.g. deepl)
for subdir in ("espn-results-cli", "deepl", "spotify"):
    path = os.path.join(ROOT, subdir)
    if path not in sys.path:
        sys.path.insert(0, path)
