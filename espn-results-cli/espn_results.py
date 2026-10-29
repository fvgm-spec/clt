#!/usr/bin/env python3
import argparse
import json
import re
import unicodedata
import sys
from datetime import datetime, timezone
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


BASE_URL       = "https://www.espn.com.uy/futbol/resultados/_/fecha/{date}"
STANDINGS_URL  = "https://www.espn.com.uy/futbol/posiciones/_/liga/{league}"
PLAYER_BIO_URL = "https://www.espn.com/soccer/player/bio/_/id/{id}/{slug}"
SEARCH_API_URL = "https://site.web.api.espn.com/apis/common/v3/search?query={query}&type={type}&sport=soccer&limit=5"
STANDINGS_API_URL  = "https://site.web.api.espn.com/apis/v2/sports/soccer/{league}/standings"
LINEUP_API_URL     = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary?event={event_id}"
SCOREBOARD_API_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={date}"
STATE_MARKER   = "window['__espnfitt__']="
DISPLAY_TIMEZONE = ZoneInfo("Europe/Madrid")


def normalize_date(value):
    if value is None:
        return datetime.now().strftime("%Y%m%d")

    value = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y%m%d")
        except ValueError:
            pass

    raise argparse.ArgumentTypeError("date must be YYYYMMDD or YYYY-MM-DD")


def fetch_html(date):
    url = BASE_URL.format(date=date)
    request = Request(
        url,
        headers={
            "User-Agent": "espn-results-cli/0.1 (+local personal script)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8"), url
    except HTTPError as exc:
        raise RuntimeError(f"ESPN returned HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc.reason}") from exc


LEAGUE_SLUGS = {
    "premier":      "eng.1",
    "premier league": "eng.1",
    "championship": "eng.2",
    "laliga":       "esp.1",
    "la liga":      "esp.1",
    "bundesliga":   "ger.1",
    "serie a":      "ita.1",
    "ligue 1":      "fra.1",
    "champions":    "UEFA.Champions_League",
    "champions league": "UEFA.Champions_League",
    "europa":       "UEFA.Europa_League",
    "conference":   "UEFA.Europa_Conference_League",
    "libertadores": "CONMEBOL.Libertadores",
    "sudamericana": "CONMEBOL.Sudamericana",
    "primera chile": "chi.1",
    "primera colombia": "col.1",
    "primera peru": "per.1",
    "primera argentina": "arg.1",
}


def extract_state(html):
    start = html.find(STATE_MARKER)
    if start == -1:
        raise RuntimeError("Could not find ESPN app state in the page HTML")

    start += len(STATE_MARKER)
    end = html.find(";</script>", start)
    if end == -1:
        raise RuntimeError("Could not find the end of ESPN app state")

    raw = unescape(html[start:end])
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse ESPN app state as JSON: {exc}") from exc


def get_scoreboard(state):
    try:
        return state["page"]["content"]["scoreboard"]
    except KeyError as exc:
        raise RuntimeError("Could not find scoreboard data in ESPN app state") from exc


def parse_score(value):
    if value is None:
        return ""
    return str(value)


def normalize_text(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def league_title(league):
    return league.get("moduleHeader") or (league.get("league") or {}).get("name") or "Unknown league"


def league_matches(league, query):
    if not query:
        return True

    league_data = league.get("league") or {}
    haystack = " ".join(
        normalize_text(str(value))
        for value in [
            league_title(league),
            league_data.get("name"),
            league_data.get("abbrev"),
            league_data.get("slug"),
        ]
        if value
    )
    words = normalize_text(query).split()
    return all(word in haystack for word in words)


def format_kickoff_time(event):
    raw_date = event.get("date")
    if not raw_date:
        return event.get("time") or "Time TBD"

    try:
        kickoff = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
    except ValueError:
        return event.get("time") or raw_date

    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)

    local = kickoff.astimezone(DISPLAY_TIMEZONE)
    return f"{local.strftime('%I:%M %p').lstrip('0')} {local.tzname()}"


def venue_line(event):
    venue = event.get("vnue") or event.get("venue") or {}
    address = venue.get("address") or {}
    parts = [venue.get("fullName"), address.get("city"), address.get("country")]
    parts = [part for part in parts if part]
    return " | ".join(parts) if parts else "Venue TBD"


def event_line(event):
    teams = event.get("competitors") or event.get("teams") or []
    away = next((team for team in teams if not team.get("isHome")), teams[0] if teams else {})
    home = next((team for team in teams if team.get("isHome")), teams[1] if len(teams) > 1 else {})

    away_name = away.get("displayName") or away.get("shortDisplayName") or "TBD"
    home_name = home.get("displayName") or home.get("shortDisplayName") or "TBD"
    away_score = parse_score(away.get("score"))
    home_score = parse_score(home.get("score"))

    status = event.get("status") or {}
    description = status.get("description") or status.get("detail") or ""
    time = format_kickoff_time(event)
    note = event.get("note")

    if away_score or home_score:
        matchup = f"{away_name} {away_score} - {home_score} {home_name}"
    else:
        matchup = f"{away_name} @ {home_name}"

    details = [venue_line(event)]
    if description:
        details.append(description)
    if note:
        details.append(note)

    detail_text = " | ".join(details)
    return f"{time:>8}  {matchup}  [{detail_text}]"


def print_scoreboard(scoreboard, date, source_url, league_filter=None):
    all_leagues = scoreboard.get("gmsByLeague") or []
    if not all_leagues:
        print(f"No soccer games found for {date}.")
        return

    leagues = [league for league in all_leagues if league_matches(league, league_filter)]
    if not leagues:
        print(f"No leagues matched {league_filter!r} for {date}.")
        print()
        print("Available leagues:")
        for league in all_leagues:
            print(f"- {league_title(league)}")
        print()
        print(f"Want to browse the full board? ESPN has it here: {source_url}")
        return

    heading = f"ESPN Uruguay soccer results for {date}"
    if league_filter:
        heading += f" - filtered by league: {league_filter}"
    print(heading)
    print(source_url)
    print()

    total_events = 0
    for league in leagues:
        events = league.get("evts") or []
        if not events:
            continue

        total_events += len(events)
        title = league.get("moduleHeader") or (league.get("league") or {}).get("name") or "Unknown league"
        print(title)
        print("-" * len(title))
        for event in events:
            print(event_line(event))
        print()

    print(f"{len(leagues)} leagues, {total_events} events")
    if not league_filter:
        print()
        print("League filters you can use with -l:")
        for league in leagues:
            print(f"- {league_title(league)}")
    print()
    print(f"Want the full match center view? Review the day on ESPN: {source_url}")


def fetch_standings(league):
    url = STANDINGS_URL.format(league=league)
    html, source_url = fetch_html_url(url)
    state = extract_state(html)
    try:
        data = state["page"]["content"]["standings"]
        headers = data["groups"]["headers"]
        groups  = data["groups"]["groups"]
    except KeyError as exc:
        raise RuntimeError(f"Could not find standings data: {exc}") from exc

    col_keys = list(headers.keys())
    col_abbr = [headers[k]["a"] for k in col_keys]

    print(f"Standings: {data.get('leagueName', league)}")
    print(f"{url}\n")

    for group in groups:
        print(group.get("name", ""))
        print("-" * 60)
        # header row
        print(f"{'#':>3}  {'Team':<28} " + "  ".join(f"{a:>4}" for a in col_abbr[:8]))
        print("-" * 60)
        for i, entry in enumerate(group.get("standings", []), 1):
            team  = entry["team"]["shortDisplayName"]
            stats = entry.get("stats", [])
            note  = entry.get("note", {}).get("description", "")
            row   = "  ".join(f"{(stats[j] if j < len(stats) else ''):>4}" for j in range(8))
            note_str = f"  [{note}]" if note else ""
            print(f"{i:>3}  {team:<28} {row}{note_str}")
        print()


def fetch_html_url(url):
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    request = Request(url, headers={
        "User-Agent": "espn-results-cli/0.1 (+local personal script)",
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8"), url
    except HTTPError as exc:
        raise RuntimeError(f"ESPN returned HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc.reason}") from exc


def search_espn(query, result_type="team"):
    import urllib.parse
    url = SEARCH_API_URL.format(query=urllib.parse.quote(query), type=result_type)
    req = Request(url, headers={"User-Agent": "espn-results-cli/0.1", "Accept": "application/json"})
    try:
        return json.loads(urlopen(req, timeout=20).read()).get("items", [])
    except Exception as exc:
        raise RuntimeError(f"Search failed: {exc}") from exc


LEAGUE_COUNTRY = {
    "eng": "gb", "esp": "es", "ger": "de", "ita": "it", "fra": "fr",
    "por": "pt", "ned": "nl", "bel": "be", "sco": "gb", "tur": "tr",
    "arg": "ar", "bra": "br", "chi": "cl", "col": "co", "per": "pe",
    "uru": "uy", "mex": "mx", "usa": "us",
}

# OSM uses official stadium names, not club names — map well-known divergences
STADIUM_ALIASES = {
    "boca juniors":   "La Bombonera",
    "river plate":    "Estadio Monumental",
    "bayern münchen": "Allianz Arena",
    "fc barcelona":   "Camp Nou",
    "barcelona":      "Camp Nou",
    "real madrid":    "Santiago Bernabéu",
    "juventus":       "Allianz Stadium",
    "ac milan":       "San Siro",
    "inter":          "San Siro",
    "atletico madrid":"Estadio Metropolitano",
    "borussia dortmund": "Signal Iduna Park",
    "manchester united": "Old Trafford",
    "manchester city":   "Etihad Stadium",
    "arsenal":           "Emirates Stadium",
    "chelsea":           "Stamford Bridge",
    "liverpool":         "Anfield",
    "tottenham hotspur": "Tottenham Hotspur Stadium",
}


def get_team_location(team_name, league_slug=""):
    """Query Nominatim (OpenStreetMap) for a football club's stadium coordinates."""
    import urllib.parse, time as _time

    cc = LEAGUE_COUNTRY.get(league_slug.split(".")[0])

    def nominatim(query):
        params = {"q": query, "format": "json", "limit": 10, "addressdetails": 1}
        if cc:
            params["countrycodes"] = cc
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
        req = Request(url, headers={"User-Agent": "espn-results-cli/0.1"})
        try:
            return json.loads(urlopen(req, timeout=10).read())
        except Exception:
            return []

    def best(results):
        for r in results:
            if any(t in r.get("type", "") for t in ("stadium", "sports", "ground", "pitch", "construction")):
                return r
        return results[0] if results else None

    # check alias first
    alias = STADIUM_ALIASES.get(team_name.lower())
    if alias:
        r = best(nominatim(alias))
        if r:
            return r
        _time.sleep(0.5)

    for query in [f"{team_name} stadium", f"{team_name} estadio", f"{team_name} football ground"]:
        r = best(nominatim(query))
        if r:
            return r
        _time.sleep(0.5)

    return None


def find_team_tier(team_query):
    items = search_espn(team_query, "team")
    if not items:
        print(f"No team found for '{team_query}'.")
        return

    LEAGUE_NAMES = {
        "eng.1": "Premier League (1st tier)",  "eng.2": "Championship (2nd tier)",
        "eng.3": "League One (3rd tier)",       "eng.4": "League Two (4th tier)",
        "esp.1": "La Liga (1st tier)",          "esp.2": "La Liga 2 (2nd tier)",
        "ger.1": "Bundesliga (1st tier)",       "ger.2": "2. Bundesliga (2nd tier)",
        "ita.1": "Serie A (1st tier)",          "ita.2": "Serie B (2nd tier)",
        "fra.1": "Ligue 1 (1st tier)",          "fra.2": "Ligue 2 (2nd tier)",
        "arg.1": "Primera División Argentina",  "chi.1": "Primera División Chile",
        "col.1": "Primera A Colombia",          "per.1": "Liga 1 Perú",
        "UEFA.Champions_League": "UEFA Champions League",
        "UEFA.Europa_League": "UEFA Europa League",
    }

    team = items[0]
    slug = team.get("defaultLeagueSlug", "")
    league = LEAGUE_NAMES.get(slug, slug or "Unknown")
    print(f"{team['displayName']}  →  {league}")

    loc = get_team_location(team["displayName"], slug)
    if loc:
        addr = loc.get("address", {})
        city    = (addr.get("city") or addr.get("town") or addr.get("municipality")
                   or addr.get("county") or addr.get("state", ""))
        country = addr.get("country", "")
        lat, lon = loc["lat"], loc["lon"]
        place   = loc["display_name"].split(",")[0]
        print(f"  Stadium  : {place}")
        print(f"  Location : {city}, {country}")
        print(f"  Coords   : {lat}, {lon}")
        print(f"  Maps     : https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15")
        print(f"  GMaps    : https://www.google.com/maps?q={lat},{lon}")
    else:
        print("  Location : not found")


FALLBACK_LEAGUES = {
    "eng": ["eng.1", "eng.2", "eng.league_cup", "eng.fa_cup"],
    "esp": ["esp.1", "esp.2", "esp.copa_del_rey"],
    "ger": ["ger.1", "ger.2", "ger.dfb_pokal"],
    "ita": ["ita.1", "ita.2", "ita.coppa_italia"],
    "fra": ["fra.1", "fra.2", "fra.coupe_de_france"],
    "UEFA": ["UEFA.Champions_League", "UEFA.Europa_League", "UEFA.Europa_Conference_League"],
}


import boto3
from decimal import Decimal

_ddb = boto3.resource("dynamodb", region_name="us-east-1")
_cache_table = _ddb.Table("espn_cache")
CACHE_TTL_SECONDS = 3600  # 1 hour


def fetch_json(url):
    import time
    try:
        item = _cache_table.get_item(Key={"cache_key": url}).get("Item")
        if item and int(item["expires_at"]) > int(time.time()):
            return json.loads(item["data"])
    except Exception:
        pass

    req = Request(url, headers={"User-Agent": "espn-results-cli/0.1", "Accept": "application/json"})
    try:
        data = json.loads(urlopen(req, timeout=20).read())
    except Exception as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc}") from exc

    try:
        _cache_table.put_item(Item={
            "cache_key": url,
            "data": json.dumps(data),
            "expires_at": int(time.time()) + CACHE_TTL_SECONDS,
        })
    except Exception:
        pass

    return data


def fetch_team_standing(team_id, league_slug):
    """Return (position, points, gamesPlayed) for a team in their league standings."""
    base = ".".join(league_slug.split(".")[:2])
    try:
        data = fetch_json(STANDINGS_API_URL.format(league=base))
        entries = data.get("children", [{}])[0].get("standings", {}).get("entries", [])
        for pos, entry in enumerate(entries, 1):
            if str(entry.get("team", {}).get("id")) == str(team_id):
                stats = {s["name"]: s["displayValue"] for s in entry.get("stats", [])}
                return pos, stats.get("points", "?"), stats.get("gamesPlayed", "?")
    except Exception:
        pass
    return None, None, None


def fetch_next_match(team_id, league_slug):
    """Return a string describing the team's next fixture."""
    try:
        data = fetch_json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_slug}/teams/{team_id}")
        ne = data.get("team", {}).get("nextEvent", [])
        if not ne:
            return None
        comp = ne[0]["competitions"][0]
        date_str = ne[0].get("date", "")
        league_name = ne[0].get("league", {}).get("name", "")
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c["homeAway"] == "home"), competitors[0])
        away = next((c for c in competitors if c["homeAway"] == "away"), competitors[-1])
        # parse date
        try:
            from datetime import timezone
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
            dt_local = dt.astimezone(DISPLAY_TIMEZONE)
            date_fmt = dt_local.strftime("%a %d %b %Y, %H:%M")
        except Exception:
            date_fmt = date_str
        opponent_label = f"{home['team']['displayName']} vs {away['team']['displayName']}"
        return f"{opponent_label}  —  {date_fmt}" + (f"  ({league_name})" if league_name else "")
    except Exception:
        return None
    """Return (position, points, gamesPlayed) for a team in their league standings."""
    # cups have no standings — use the team's default league (first segment pair e.g. eng.1)
    base = ".".join(league_slug.split(".")[:2])
    try:
        data = fetch_json(STANDINGS_API_URL.format(league=base))
        entries = data.get("children", [{}])[0].get("standings", {}).get("entries", [])
        for pos, entry in enumerate(entries, 1):
            if str(entry.get("team", {}).get("id")) == str(team_id):
                stats = {s["name"]: s["displayValue"] for s in entry.get("stats", [])}
                return pos, stats.get("points", "?"), stats.get("gamesPlayed", "?")
    except Exception:
        pass
    return None, None, None


def fetch_coach(team_display_name):
    """Return (name, nationality) for the current head coach via Wikipedia."""
    import urllib.parse

    def wiki_summary(name):
        try:
            return fetch_json("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(name))
        except Exception:
            return {}

    def extract_nationality(description):
        """Return first word only if it looks like a nationality, not a disambiguation."""
        if not description or "Topics referred to" in description or "may refer" in description:
            return None
        _non_demonyms = {"Football", "Soccer", "Association", "Professional", "Former", "Head", "Coach", "Manager"}
        word = description.split()[0]
        # reject if it's not a plausible demonym (all alpha, title-case, reasonable length)
        if word.isalpha() and word[0].isupper() and 3 <= len(word) <= 20 and word not in _non_demonyms:
            return word
        return None

    try:
        search_url = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={}&srlimit=1&format=json".format(
            urllib.parse.quote(team_display_name + " football club"))
        results = fetch_json(search_url)
        hits = results.get("query", {}).get("search", [])
        if not hits:
            return None, None
        title = hits[0]["title"].replace(" ", "_")
        content_url = "https://en.wikipedia.org/w/api.php?action=query&titles={}&prop=revisions&rvprop=content&rvsection=0&format=json".format(
            urllib.parse.quote(title))
        data = fetch_json(content_url)
        content = list(data["query"]["pages"].values())[0]["revisions"][0]["*"]
        m = re.search(r"manager\s*=\s*\[\[([^\]]+)\]\]", content, re.IGNORECASE)
        if not m:
            return None, None
        manager_name = m.group(1).split("|")[-1]

        # try direct summary first
        wiki = wiki_summary(manager_name)
        nationality = extract_nationality(wiki.get("description", ""))

        # if disambiguation, retry with "footballer" or "football manager"
        if nationality is None:
            for suffix in ["football manager", "footballer"]:
                wiki = wiki_summary(f"{manager_name} ({suffix})")
                nationality = extract_nationality(wiki.get("description", ""))
                if nationality:
                    break

        # last resort: search API
        if nationality is None:
            sr = fetch_json("https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={}&srlimit=1&format=json".format(
                urllib.parse.quote(manager_name + " football manager")))
            sr_hits = sr.get("query", {}).get("search", [])
            if sr_hits:
                wiki = wiki_summary(sr_hits[0]["title"])
                nationality = extract_nationality(wiki.get("description", ""))

        return manager_name, nationality
    except Exception:
        return None, None


_athlete_cache = {}

def fetch_athlete_info(athlete_id, slug):
    """Fetch age and nationality for a player. Cached to avoid duplicate requests."""
    if athlete_id in _athlete_cache:
        return _athlete_cache[athlete_id]

    url = PLAYER_BIO_URL.format(id=athlete_id, slug=slug)
    try:
        html, _ = fetch_html_url(url)
        state = extract_state(html)
        ath = state["page"]["content"]["player"]["plyrHdr"]["ath"]
        dob_raw = ath.get("dobRaw") or ath.get("dob", "")
        age = None
        if dob_raw:
            try:
                for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
                    try:
                        dob = datetime.strptime(dob_raw[:10], fmt)
                        # reject implausible dates (e.g. MM/DD misread as DD/MM)
                        if fmt == "%d/%m/%Y" and int(dob_raw.split("/")[0]) > 12:
                            pass  # day > 12 means it can only be DD/MM
                        elif fmt == "%m/%d/%Y" and int(dob_raw.split("/")[0]) > 12:
                            continue  # month > 12 is invalid, skip
                        today = datetime.now()
                        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                        if 10 <= age <= 50:  # sanity check
                            break
                        age = None
                    except ValueError:
                        continue
            except Exception:
                pass
        nationality = ath.get("ctz", "")
        result = (age, nationality)
    except Exception:
        result = (None, "")

    _athlete_cache[athlete_id] = result
    return result


def find_lineup(team_query, date):
    """Find today's match for a team and print both lineups."""
    items = search_espn(team_query, "team")
    if not items:
        print(f"No team found for '{team_query}'.")
        return

    team = items[0]
    team_id = str(team["id"])
    team_name = team["displayName"]
    league_slug = team.get("defaultLeagueSlug", "eng.1")

    url = SCOREBOARD_API_URL.format(league=league_slug, date=date)
    data = fetch_json(url)
    events = data.get("events", [])

    match = None
    for event in events:
        for comp in event.get("competitions", []):
            for competitor in comp.get("competitors", []):
                if str(competitor.get("id")) == team_id or \
                   normalize_text(competitor.get("team", {}).get("displayName", "")) == normalize_text(team_name):
                    match = (event, comp)
                    break

    if not match:
        prefix = league_slug.split(".")[0]
        for fallback in FALLBACK_LEAGUES.get(prefix, []):
            if fallback == league_slug:
                continue
            try:
                fdata = fetch_json(SCOREBOARD_API_URL.format(league=fallback, date=date))
                for event in fdata.get("events", []):
                    for comp in event.get("competitions", []):
                        for competitor in comp.get("competitors", []):
                            if str(competitor.get("id")) == team_id or \
                               normalize_text(competitor.get("team", {}).get("displayName", "")) == normalize_text(team_name):
                                match = (event, comp)
                                league_slug = fallback
                                break
                        if match:
                            break
                    if match:
                        break
            except Exception:
                continue
            if match:
                break

    if not match:
        print(f"No match found for '{team_name}' on {date}.")
        return

    event, comp = match
    state = comp.get("status", {}).get("type", {}).get("description", "Unknown")
    event_id = event["id"]

    summary = fetch_json(LINEUP_API_URL.format(league=league_slug, event_id=event_id))

    competitors = comp.get("competitors", [])
    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[-1])

    # venue
    venue = comp.get("venue") or summary.get("gameInfo", {}).get("venue", {})
    venue_name = venue.get("fullName", "")
    venue_city = (venue.get("address") or {}).get("city", "")
    venue_str  = ", ".join(filter(None, [venue_name, venue_city]))

    print(f"{away.get('team',{}).get('displayName','Away')} {away.get('score','')} - {home.get('score','')} {home.get('team',{}).get('displayName','Home')}  [{state}]")
    if venue_str:
        print(f"Venue: {venue_str}")

    # league standing + next match for each side
    team_standing = {}
    team_next = {}
    for c in competitors:
        tid   = c.get("team", {}).get("id", "")
        tname = c.get("team", {}).get("displayName", "")
        # resolve default league: use resolved league_slug for queried team, search ESPN for opponent
        if tname == team_name:
            tleague = league_slug
        else:
            try:
                items = search_espn(tname, "team")
                tleague = items[0].get("defaultLeagueSlug", league_slug) if items else league_slug
            except Exception:
                tleague = league_slug
        pos, pts, gp = fetch_team_standing(tid, tleague)
        if pos:
            team_standing[tname] = f"{pos}th  ({pts} pts, {gp} played)"
        nxt = fetch_next_match(tid, tleague)
        if nxt:
            team_next[tname] = nxt
    print()

    rosters = summary.get("rosters", [])
    if not rosters or all(len(r.get("roster", [])) == 0 for r in rosters):
        print("Lineup data not available yet (match may not have started).")
        return

    for roster in rosters:
        side_name = roster.get("team", {}).get("displayName", "Team")
        formation = roster.get("formation", "") if isinstance(roster.get("formation"), str) else (roster.get("formation") or {}).get("name", "")

        entries  = roster.get("roster", [])
        starters = [e for e in entries if e.get("starter")]
        bench    = [e for e in entries if not e.get("starter")]

        # fetch age+nationality for all players
        player_info = {}
        for e in entries:
            ath  = e.get("athlete", {})
            aid  = ath.get("id", "")
            slug = re.sub(r"[^a-z0-9]+", "-", ath.get("displayName", "").lower()).strip("-")
            player_info[aid] = fetch_athlete_info(aid, slug)

        # avg age of starters
        starter_ages = [player_info[e["athlete"]["id"]][0] for e in starters if player_info.get(e["athlete"]["id"], (None,))[0]]
        avg_age = round(sum(starter_ages) / len(starter_ages), 1) if starter_ages else None

        # coach
        coach_name, coach_nat = fetch_coach(side_name)

        header = f"{side_name}" + (f"  [{formation}]" if formation else "")
        print(header)
        print("-" * len(header))
        if side_name in team_standing:
            print(f"League position: {team_standing[side_name]}")
        if side_name in team_next:
            print(f"Next match:      {team_next[side_name]}")
        if coach_name:
            coach_str = f"{coach_name}" + (f"  ({coach_nat})" if coach_nat else "")
            print(f"Manager: {coach_str}")
        if avg_age:
            print(f"Avg age (XI): {avg_age}")
        print()

        print("Starting XI:")
        for e in starters:
            ath   = e.get("athlete", {})
            name  = ath.get("displayName", "Unknown")
            pos   = (e.get("position") or {}).get("abbreviation", "")
            jersey = ath.get("jersey", "")
            flag  = " ↓" if e.get("subbedOut") else (" ↑" if e.get("subbedIn") else "")
            age, nat = player_info.get(ath.get("id", ""), (None, ""))
            extra = "  " + "  ".join(filter(None, [f"{age}y" if age else None, nat]))
            print(f"  {jersey:>2}  {pos:<3}  {name}{flag}{extra}")

        if bench:
            print("Bench:")
            for e in bench:
                ath   = e.get("athlete", {})
                name  = ath.get("displayName", "Unknown")
                pos   = (e.get("position") or {}).get("abbreviation", "")
                jersey = ath.get("jersey", "")
                flag  = " ↑" if e.get("subbedIn") else ""
                age, nat = player_info.get(ath.get("id", ""), (None, ""))
                extra = "  " + "  ".join(filter(None, [f"{age}y" if age else None, nat]))
                print(f"  {jersey:>2}  {pos:<3}  {name}{flag}{extra}")
        print()


def find_player(player_query):
    items = search_espn(player_query, "player")
    if not items:
        print(f"No player found for '{player_query}'.")
        return

    player = items[0]
    pid    = player["id"]
    slug   = re.sub(r"[^a-z0-9]+", "-", player["displayName"].lower()).strip("-")
    league = (player.get("leagueRelationships") or [{}])[0]
    league_name = league.get("displayName", player.get("league", ""))

    # fetch bio page to get current club + career
    url = PLAYER_BIO_URL.format(id=pid, slug=slug)
    html, _ = fetch_html_url(url)
    state = extract_state(html)
    pdata = state["page"]["content"]["player"]
    hdr   = pdata.get("plyrHdr", {}).get("ath", {})
    hist  = pdata.get("hist", [])

    current_club = hdr.get("tm") or player.get("teamName", "N/A")
    print(f"{player['displayName']}")
    print(f"  Current club : {current_club}")
    print(f"  League       : {league_name}")
    print(f"  Position     : {hdr.get('pos', '')}")
    print(f"  Nationality  : {hdr.get('ctz', '')}")
    print()

    if hist:
        print("Career (clubs):")
        print("-" * 40)
        for entry in hist:
            name = entry.get("nm", "")
            apps = entry.get("num", "")
            link = entry.get("href", "")
            apps_str = f"  ({apps} apps)" if apps else ""
            print(f"  {name}{apps_str}")
            if link:
                print(f"    {link}")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Show ESPN Uruguay soccer results, standings, team tier or player info."
    )
    parser.add_argument(
        "date", nargs="?", type=normalize_date, default=normalize_date(None),
        help="Date to fetch, as YYYYMMDD or YYYY-MM-DD. Defaults to today.",
    )
    parser.add_argument("-l", "--league",
        help="Filter by league (results) or league slug/name (standings).")
    parser.add_argument("-s", "--standings", action="store_true",
        help="Show league standings. Requires -l.")
    parser.add_argument("-t", "--team",
        help="Find which tier/league a club currently plays in.")
    parser.add_argument("-p", "--player",
        help="Find current club and full career history for a player.")
    parser.add_argument("--lineup",
        help="Show lineups for a team's match today (or on the given date). E.g. --lineup 'Arsenal'")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.lineup:
            find_lineup(args.lineup, args.date)
        elif args.team:
            find_team_tier(args.team)
        elif args.player:
            find_player(args.player)
        elif args.standings:
            if not args.league:
                print("error: --standings requires -l <league>", file=sys.stderr)
                return 1
            slug = LEAGUE_SLUGS.get(args.league.lower(), args.league)
            fetch_standings(slug)
        else:
            html, source_url = fetch_html(args.date)
            state = extract_state(html)
            scoreboard = get_scoreboard(state)
            print_scoreboard(scoreboard, args.date, source_url, args.league)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
