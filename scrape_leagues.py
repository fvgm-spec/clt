#!/usr/bin/env python3
"""
ESPN league scraper — discovers all leagues from espn.com.uy/futbol
and stores them in DynamoDB under pk=league#<slug>, sk=meta.

Usage:
    python3 scrape_leagues.py [--region us-east-1]
"""
import argparse
import json
import re
import time
import urllib.request
from datetime import datetime, timezone

import boto3

TABLE   = "espn_data"
REGION  = "us-east-1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Friendly names for known slugs (supplement what ESPN returns)
SLUG_NAMES = {
    "arg.1": "Argentine Primera División", "arg.2": "Argentine Primera B Nacional",
    "bol.1": "Bolivian Liga Profesional",  "bra.1": "Brazilian Série A",
    "chi.1": "Chilean Primera División",   "chn.1": "Chinese Super League",
    "col.1": "Colombian Primera A",        "crc.1": "Costa Rican Primera División",
    "ecu.1": "Ecuadorian Serie A",         "eng.1": "English Premier League",
    "eng.2": "English Championship",       "esp.1": "Spanish La Liga",
    "esp.2": "Spanish Segunda División",   "fra.1": "French Ligue 1",
    "fra.2": "French Ligue 2",             "ger.1": "German Bundesliga",
    "ger.2": "German 2. Bundesliga",       "gre.1": "Greek Super League",
    "gua.1": "Guatemalan Liga Nacional",   "hon.1": "Honduran Liga Nacional",
    "ita.1": "Italian Serie A",            "ita.2": "Italian Serie B",
    "jpn.1": "Japanese J1 League",         "ksa.1": "Saudi Pro League",
    "mex.1": "Mexican Liga MX",            "mex.2": "Mexican Liga de Expansión",
    "ned.1": "Dutch Eredivisie",           "par.1": "Paraguayan División Profesional",
    "per.1": "Peruvian Liga 1",            "por.1": "Portuguese Primeira Liga",
    "rus.1": "Russian Premier League",     "slv.1": "Salvadoran Primera División",
    "tur.1": "Turkish Süper Lig",          "uru.1": "Uruguayan Primera División",
    "uru.2": "Uruguayan Segunda División", "usa.1": "MLS",
    "ven.1": "Venezuelan Primera División",
    # cups / continental
    "UEFA.CL": "UEFA Champions League",    "UEFA.EL": "UEFA Europa League",
    "UEFA.CONF": "UEFA Europa Conference League",
    "CONMEBOL.LIBERTADORES": "CONMEBOL Libertadores",
    "CONMEBOL.SUDAMERICANA": "CONMEBOL Sudamericana",
}

COUNTRY_MAP = {
    "arg": "Argentina", "bol": "Bolivia",  "bra": "Brazil",   "chi": "Chile",
    "chn": "China",     "col": "Colombia", "crc": "Costa Rica","ecu": "Ecuador",
    "eng": "England",   "esp": "Spain",    "fra": "France",    "ger": "Germany",
    "gre": "Greece",    "gua": "Guatemala","hon": "Honduras",  "ita": "Italy",
    "jpn": "Japan",     "ksa": "Saudi Arabia","mex": "Mexico", "ned": "Netherlands",
    "par": "Paraguay",  "per": "Peru",     "por": "Portugal",  "rus": "Russia",
    "slv": "El Salvador","tur": "Turkey",  "uru": "Uruguay",   "usa": "USA",
    "ven": "Venezuela", "UEFA": "Europe",  "CONMEBOL": "South America",
}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return json.loads(urllib.request.urlopen(req, timeout=15).read())


def discover_slugs():
    """Scrape espn.com.uy/futbol to find all league slugs."""
    req = urllib.request.Request("https://www.espn.com.uy/futbol/resultados", headers=HEADERS)
    html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
    slugs = sorted(set(re.findall(r'/futbol/[^"]+/_/liga/([a-zA-Z]{2,10}\.[a-zA-Z0-9]+)', html)))
    return slugs


def enrich_from_api(slug):
    """Fetch league name/id from ESPN standings API."""
    try:
        data = fetch(f"https://site.web.api.espn.com/apis/v2/sports/soccer/{slug}/standings")
        return {"espn_id": data.get("id", ""), "espn_name": data.get("name", ""),
                "abbreviation": data.get("abbreviation", "")}
    except Exception:
        return {}


def ensure_table(ddb):
    try:
        ddb.describe_table(TableName=TABLE)
    except ddb.exceptions.ResourceNotFoundException:
        print(f"Creating DynamoDB table '{TABLE}'...")
        ddb.create_table(
            TableName=TABLE,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        ddb.get_waiter("table_exists").wait(TableName=TABLE)
        print("  Table ready.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default=REGION)
    args = parser.parse_args()

    ddb = boto3.client("dynamodb", region_name=args.region)
    ensure_table(ddb)

    print("Discovering league slugs from espn.com.uy...")
    slugs = discover_slugs()
    print(f"  Found {len(slugs)} slugs: {slugs}")

    now = datetime.now(timezone.utc).isoformat()
    written = 0

    for slug in slugs:
        country_code = slug.split(".")[0]
        country = COUNTRY_MAP.get(country_code, country_code.upper())
        tier = slug.split(".")[-1] if "." in slug else "1"
        name = SLUG_NAMES.get(slug, "")

        api_data = enrich_from_api(slug)
        if not name and api_data.get("espn_name"):
            name = api_data["espn_name"]
        if not name:
            name = slug

        item = {
            "pk":           {"S": f"league#{slug}"},
            "sk":           {"S": "meta"},
            "slug":         {"S": slug},
            "name":         {"S": name},
            "country":      {"S": country},
            "tier":         {"S": tier},
            "updated_at":   {"S": now},
        }
        if api_data.get("espn_id"):
            item["espn_id"] = {"S": api_data["espn_id"]}
        if api_data.get("abbreviation"):
            item["abbreviation"] = {"S": api_data["abbreviation"]}

        ddb.put_item(TableName=TABLE, Item=item)
        print(f"  ✓ {slug:25s}  {name}")
        written += 1
        time.sleep(0.1)  # be polite

    print(f"\nDone. {written} leagues written to '{TABLE}'.")


if __name__ == "__main__":
    main()
