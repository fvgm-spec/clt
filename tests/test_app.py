import json
import sys
import os
import importlib.util
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))


def load(subdir, module):
    path = os.path.join(ROOT, subdir, f"{module}.py")
    spec = importlib.util.spec_from_file_location(f"{subdir}.{module}", path,
           submodule_search_locations=[os.path.join(ROOT, subdir)])
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(ROOT, subdir))
    spec.loader.exec_module(mod)
    return mod


espn_lh    = load("espn-results-cli", "lambda_handler")
deepl_lh   = load("deepl",            "lambda_handler")
spotify_lh = load("spotify",          "lambda_handler")


class TestEspnLambda:
    def test_returns_200(self):
        with patch.object(espn_lh.espn, "fetch_html", return_value=("<html>", "http://espn.com")), \
             patch.object(espn_lh.espn, "extract_state", return_value={}), \
             patch.object(espn_lh.espn, "get_scoreboard", return_value={"gmsByLeague": []}):
            r = espn_lh.lambda_handler({"queryStringParameters": {"action": "results"}}, None)
        assert r["statusCode"] == 200


class TestDeeplLambda:
    def test_no_source(self):
        with patch.object(deepl_lh, "detect_and_translate", return_value="Hello"):
            r = deepl_lh.lambda_handler({"text": "Hola", "target_lang": "EN-US"}, None)
        assert r["statusCode"] == 200
        assert json.loads(r["body"])["translation"] == "Hello"

    def test_with_source(self):
        with patch.object(deepl_lh, "translate", return_value="Hello"):
            r = deepl_lh.lambda_handler({"text": "Hola", "target_lang": "EN-US", "source_lang": "ES"}, None)
        assert r["statusCode"] == 200
        assert json.loads(r["body"])["translation"] == "Hello"


class TestSpotifyLambda:
    def test_top_tracks(self):
        with patch.object(spotify_lh, "get_access_token", return_value="tok"), \
             patch.object(spotify_lh, "get_top_tracks", return_value={"items": []}):
            r = spotify_lh.lambda_handler({"action": "top_tracks"}, None)
        assert r["statusCode"] == 200

    def test_search(self):
        with patch.object(spotify_lh, "get_access_token", return_value="tok"), \
             patch.object(spotify_lh, "search_tracks", return_value={"tracks": []}):
            r = spotify_lh.lambda_handler({"action": "search", "query": "radiohead"}, None)
        assert r["statusCode"] == 200

    def test_unknown_action(self):
        with patch.object(spotify_lh, "get_access_token", return_value="tok"):
            r = spotify_lh.lambda_handler({"action": "unknown"}, None)
        assert r["statusCode"] == 400
