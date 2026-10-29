import json
import io
import contextlib
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import espn_results as espn

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _capture(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            fn(*args)
        except Exception as e:
            return None, str(e)
    return buf.getvalue(), None


def _ok(text):
    return {"statusCode": 200, "headers": CORS, "body": json.dumps({"result": text})}


def _err(msg, code=400):
    return {"statusCode": code, "headers": CORS, "body": json.dumps({"error": msg})}


def lambda_handler(event, context):
    # API Gateway passes query params here
    qs = event.get("queryStringParameters") or {}
    action = qs.get("action", "results")

    # ── results ──────────────────────────────────────────────────────────
    if action == "results":
        date = espn.normalize_date(qs.get("date"))
        league = qs.get("league")
        try:
            html, source_url = espn.fetch_html(date)
            state = espn.extract_state(html)
            scoreboard = espn.get_scoreboard(state)
            out, err = _capture(espn.print_scoreboard, scoreboard, date, source_url, league)
        except Exception as e:
            return _err(str(e))
        return _ok(out) if not err else _err(err)

    # ── lineup ───────────────────────────────────────────────────────────
    if action == "lineup":
        team = qs.get("team")
        if not team:
            return _err("'team' parameter required")
        date = espn.normalize_date(qs.get("date"))
        out, err = _capture(espn.find_lineup, team, date)
        return _ok(out) if not err else _err(err)

    # ── standings ─────────────────────────────────────────────────────────
    if action == "standings":
        league = qs.get("league")
        if not league:
            return _err("'league' parameter required")
        slug = espn.LEAGUE_SLUGS.get(league.lower(), league)
        out, err = _capture(espn.fetch_standings, slug)
        return _ok(out) if not err else _err(err)

    # ── player ────────────────────────────────────────────────────────────
    if action == "player":
        name = qs.get("name")
        if not name:
            return _err("'name' parameter required")
        out, err = _capture(espn.find_player, name)
        return _ok(out) if not err else _err(err)

    # ── team ──────────────────────────────────────────────────────────────
    if action == "team":
        name = qs.get("name")
        if not name:
            return _err("'name' parameter required")
        out, err = _capture(espn.find_team_tier, name)
        return _ok(out) if not err else _err(err)

    return _err(f"Unknown action '{action}'. Valid: results, lineup, standings, player, team")
