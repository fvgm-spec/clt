# ESPN Results CLI

Minimal command line scraper for ESPN Uruguay soccer results and league standings.

## Results / Fixtures

Fetch results or upcoming fixtures for a given day:

```bash
# today
python3 espn_results.py

# specific date
python3 espn_results.py 20261027
python3 espn_results.py 2026-10-27

# filter by league
python3 espn_results.py 2026-10-27 -l "premier league"
python3 espn_results.py 2026-10-27 -l "champions"
python3 espn_results.py 2026-10-27 -l "libertadores"
```

Fetches from:
```
https://www.espn.com.uy/futbol/resultados/_/fecha/YYYYMMDD
```

Each game row includes kickoff time (Europe/Madrid timezone), score, venue, city and country. Running without `-l` prints all available league names at the footer so you can pick one to filter by.

## Standings

Fetch the current league table positions with `-s` / `--standings` and `-l` for the league:

```bash
python3 espn_results.py -s -l "premier league"
python3 espn_results.py -s -l "laliga"
python3 espn_results.py -s -l "champions"
python3 espn_results.py -s -l "libertadores"

# or pass the ESPN league slug directly
python3 espn_results.py -s -l "eng.1"
python3 espn_results.py -s -l "esp.1"
python3 espn_results.py -s -l "chi.1"
```

Fetches from:
```
https://www.espn.com.uy/futbol/posiciones/_/liga/{league}
```

Output columns: `J` (played) · `G` (wins) · `E` (draws) · `P` (losses) · `GF` (goals for) · `GC` (goals against) · `DIF` (goal difference) · `PTS` (points). Qualification zones (Champions League, Europa League, Relegation) are shown inline per team.

### Supported league shortcuts

| Shortcut | League |
|---|---|
| `premier`, `premier league` | English Premier League |
| `championship` | English Championship |
| `laliga`, `la liga` | Spanish La Liga |
| `bundesliga` | German Bundesliga |
| `serie a` | Italian Serie A |
| `ligue 1` | French Ligue 1 |
| `champions`, `champions league` | UEFA Champions League |
| `europa` | UEFA Europa League |
| `conference` | UEFA Europa Conference League |
| `libertadores` | CONMEBOL Libertadores |
| `sudamericana` | CONMEBOL Sudamericana |
| `primera chile` | Chilean Primera División |
| `primera colombia` | Colombian Primera A |
| `primera peru` | Peruvian Liga 1 |
| `primera argentina` | Argentine Primera División |

Any other ESPN league slug (e.g. `ger.2`, `por.1`, `mex.1`) can be passed directly to `-l`.

## Team Tier & Stadium Location

Find which tier/league a club currently plays in, plus its stadium location (coordinates + maps links):

```bash
python3 espn_results.py -t "leicester city"
python3 espn_results.py -t "boca juniors"
python3 espn_results.py -t "barcelona"
python3 espn_results.py -t "bayern munich"
```

Sample output:
```
Leicester City  →  Championship (2nd tier)
  Stadium  : King Power Stadium
  Location : Leicester, United Kingdom
  Coords   : 52.6203970, -1.1423352
  Maps     : https://www.openstreetmap.org/?mlat=52.6203970&mlon=-1.1423352&zoom=15
  GMaps    : https://www.google.com/maps?q=52.6203970,-1.1423352
```

Location data is sourced from **OpenStreetMap Nominatim** — no API key required.

## Player Lookup

Find a player's current club and full career history:

```bash
python3 espn_results.py -p "harry kane"
python3 espn_results.py -p "messi"
python3 espn_results.py -p "vinicius"
```

Sample output:
```
Harry Kane
  Current club : Bayern Munich
  League       : German Bundesliga
  Position     : Atacante
  Nationality  : Inglaterra

Career (clubs):
----------------------------------------
  Bayern Munich  (4 apps)
  Tottenham Hotspur  (13 apps)
  Norwich City  (1 apps)
  Leicester City  (1 apps)
  Millwall  (1 apps)
  Leyton Orient  (1 apps)
```



```
Standings: Liga Premier
https://www.espn.com.uy/futbol/posiciones/_/liga/eng.1

Premiership de Inglaterra 2026/2
------------------------------------------------------------
  #  Team                            J     P   DIF   PTS    GC    GF     E     G
------------------------------------------------------------
  1  Manchester City                 8     1   +11    21     9    20     0     7  [Champions League]
  2  Arsenal                         8     1    +8    21     5    13     0     7  [Champions League]
  3  Brighton & Hove Albion          8     2   +16    16     7    23     1     5  [Champions League]
  ...
 18  Nottingham Forest               8     4    -4     6    10     6     3     1  [Relegation]
 19  Coventry City                   8     6    -9     6    15     6     0     2  [Relegation]
 20  Sunderland                      8     5    -8     5    14     6     2     1  [Relegation]
```
