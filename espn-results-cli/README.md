# ESPN Results CLI

Minimal command line scraper for ESPN Uruguay soccer results.

```bash
./espn_results.py
./espn_results.py 20260916
./espn_results.py 2026-09-16
./espn_results.py 20260916 --league "Carabao Cup"
./espn_results.py 20260916 -l "liga europa uefa"
```

The script fetches:

```text
https://www.espn.com.uy/futbol/resultados/_/fecha/YYYYMMDD
```

It extracts the embedded `window['__espnfitt__']` object and prints games grouped by league. Use `--league` or `-l` to filter the output to one competition. Each game row includes the kickoff time, venue, city, and country when ESPN exposes those fields. When you run without `--league`, the footer prints the available league names you can pass back into `-l`.
