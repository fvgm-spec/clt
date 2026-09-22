# spoty — Spotify Top Tracks CLI

Command line tool to list and play your most played Spotify tracks locally via spotifyd.

## First-time setup

### 1. Authenticate spotifyd (once)

```bash
~/felix/misc_projects/spotify/spotifyd authenticate --cache-path ~/.cache/spotifyd
```

This opens a browser, you log in with your Spotify account, and credentials are cached at `~/.cache/spotifyd`. You only need to do this once.

### 2. Authenticate the API client (once)

```bash
python3 ~/felix/misc_projects/spotify/spoty.py
```

On first run this opens a browser for OAuth. After approving, the token is saved to `.token.json` and reused automatically on all future runs.

---

## Usage

```bash
# List your top 10 tracks (last 6 months)
python3 ~/felix/misc_projects/spotify/spoty.py

# List + play full tracks
python3 ~/felix/misc_projects/spotify/spoty.py --play

# Top 20, all-time, with playback
python3 ~/felix/misc_projects/spotify/spoty.py --play --limit 20 --range long_term

# Last 4 weeks
python3 ~/felix/misc_projects/spotify/spoty.py --play --range short_term
```

### Search & play a specific track

Pass any free-text query as a positional argument — partial song name, partial artist name, or both:

```bash
# partial song name
python3 ~/felix/misc_projects/spotify/spoty.py "cochise"

# partial artist name
python3 ~/felix/misc_projects/spotify/spoty.py "audioslave"

# mixed artist + track
python3 ~/felix/misc_projects/spotify/spoty.py "rusty soundgarden"

# search + play immediately
python3 ~/felix/misc_projects/spotify/spoty.py "cochise" --play

# search top 3 results + play
python3 ~/felix/misc_projects/spotify/spoty.py "garbage" --limit 3 --play

# search + shuffle results + play
python3 ~/felix/misc_projects/spotify/spoty.py "soundgarden" --limit 5 --play --shuffle
```

### Filter top tracks by artist

```bash
# only show/play your top tracks from a specific artist
python3 ~/felix/misc_projects/spotify/spoty.py --artist "audioslave" --play

# combine with shuffle and range
python3 ~/felix/misc_projects/spotify/spoty.py --artist "depeche" --range long_term --shuffle --play
```

### Autoplay / continuous playback

When the last track in your queue finishes, Spotify automatically continues playing related music. No extra flags needed — it kicks in on its own at the end of every queue.

### Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `query` | any text | — | Search by song, artist, or both (optional) |
| `--play` | — | off | Play tracks via spotifyd |
| `--shuffle` | — | off | Randomize playback order |
| `--artist` | partial name | — | Filter your top tracks by artist (partial match, ignored when using search query) |
| `--limit` | 1–50 | 10 | Number of tracks to fetch/search |
| `--range` | `short_term` `medium_term` `long_term` | `medium_term` | `short_term`=last 4 weeks, `medium_term`=last 6 months, `long_term`=all time (ignored when using search query) |

### Controls during playback

- `Ctrl+C` — skip to next track
- `Ctrl+C` twice — quit

---

## Files

| File | Description |
|------|-------------|
| `spoty.py` | Main CLI script |
| `spotifyd` | Local spotifyd binary (v0.4.2) |
| `.env` | Spotify app credentials (Client ID / Secret) |
| `.token.json` | Cached OAuth token (auto-managed) |
| `~/.config/spotifyd/spotifyd.conf` | spotifyd config (audio backend, device name) |
| `~/.cache/spotifyd` | spotifyd cached credentials |
