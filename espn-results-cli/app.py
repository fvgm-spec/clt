import re
import requests
import streamlit as st

API = "https://v114kxt4i7.execute-api.us-east-1.amazonaws.com/"

st.set_page_config(page_title="ESPN Results", page_icon="⚽", layout="centered")
st.title("⚽ ESPN Results")


def call(params):
    try:
        r = requests.get(API, params=params, timeout=30)
        data = r.json()
        return data.get("result") or data.get("error", "No response")
    except Exception as e:
        return f"Error: {e}"


# ── Renderers ─────────────────────────────────────────────────────────────────

def render_results(text):
    league = None
    for line in text.splitlines():
        if not line.strip() or line.startswith("ESPN") or line.startswith("http") or line.startswith("Want"):
            continue
        if re.match(r"^-+$", line):
            continue
        # league header
        if not re.match(r"^\d", line) and not line.startswith(" "):
            league = line.strip()
            st.subheader(f"🏆 {league}")
            continue
        # match line: "6:30 PM CET  Lecce 0 - 0 Frosinone  [...]"
        m = re.match(r"^(\S+\s+\S+\s+\S+)\s{2,}(.+?)\s{2,}\[(.+)\]$", line.strip())
        if m:
            time, matchup, detail = m.group(1), m.group(2), m.group(3)
            parts = detail.split("|")
            status = parts[-1].strip() if parts else detail
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{matchup}**")
                c2.markdown(f"`{status}`")
                st.caption(f"🕐 {time}")


def render_lineup(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # match header: "Lecce 0 - 0 Frosinone  [Full Time]"
        m = re.match(r"^(.+?\d+\s*-\s*\d+.+?)\s+\[(.+)\]$", line)
        if m and i == 0:
            st.subheader(f"⚽ {m.group(1)}")
            st.caption(f"Status: {m.group(2)}")
            i += 1; continue

        if line.startswith("Venue:"):
            st.caption(f"📍 {line.replace('Venue:', '').strip()}")
            i += 1; continue

        # team section header: "Fortuna Sittard  [5-4-1]"
        m = re.match(r"^([A-Z].+?)\s+\[(.+)\]$", line)
        if m and not line.startswith(" "):
            st.divider()
            st.markdown(f"### {m.group(1)}  `{m.group(2)}`")
            i += 1; continue

        if re.match(r"^-+$", line):
            i += 1; continue

        for prefix, icon in [("League position:", "📊"), ("Next match:", "📅"), ("Manager:", "👤"), ("Avg age", "🎂")]:
            if line.startswith(prefix):
                st.caption(f"{icon} {line.strip()}")
                break

        if line.strip() == "Starting XI:":
            st.markdown("**Starting XI**")
            i += 1
            rows = []
            while i < len(lines) and lines[i].strip() and lines[i].strip() != "Bench:":
                p = lines[i].strip()
                rows.append(p)
                i += 1
            for p in rows:
                parts = p.split()
                if len(parts) >= 2:
                    pos = parts[0]
                    rest = " ".join(parts[1:])
                    st.markdown(f"&nbsp;&nbsp;`{pos}` {rest}", unsafe_allow_html=True)
            continue

        if line.strip() == "Bench:":
            st.markdown("**Bench**")
            i += 1
            while i < len(lines) and lines[i].strip():
                p = lines[i].strip().replace("SUB  ", "").replace("SUB ", "")
                st.markdown(f"&nbsp;&nbsp;↳ {p}", unsafe_allow_html=True)
                i += 1
            continue

        i += 1


def render_standings(text):
    lines = text.splitlines()
    header_done = False
    rows = []
    for line in lines:
        if not line.strip() or line.startswith("Standings") or line.startswith("http"):
            continue
        if re.match(r"^-+$", line):
            continue
        # season header
        if re.match(r"^\d{4}-\d{4}", line):
            st.subheader(f"🏆 {line.strip()}")
            continue
        # column header line
        if not header_done and re.match(r"^\s+#\s+Team", line):
            header_done = True
            continue
        # data row: "   1  Manchester City   10   8  +15   24 ..."
        m = re.match(r"^\s*(\d+)\s{2,}(.+?)\s{2,}(.+)$", line)
        if m:
            rows.append((m.group(1), m.group(2).strip(), m.group(3).strip()))

    if rows:
        cols = st.columns([1, 4, 3])
        cols[0].markdown("**#**")
        cols[1].markdown("**Team**")
        cols[2].markdown("**Stats**")
        for rank, team, stats in rows:
            cols = st.columns([1, 4, 3])
            cols[0].write(rank)
            cols[1].write(team)
            cols[2].write(stats)


def render_plain(text):
    """Fallback: render as clean markdown instead of code block."""
    st.markdown(f"```\n{text}\n```")


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Results", "Lineup", "Standings", "Player", "Team"])

with tab1:
    col1, col2 = st.columns(2)
    date   = col1.text_input("Date (YYYYMMDD or YYYY-MM-DD)", placeholder="leave blank for today")
    league = col2.text_input("League filter", placeholder="premier league, laliga …")
    if st.button("Fetch results"):
        with st.spinner("Fetching…"):
            out = call({"action": "results", "date": date or "", "league": league or ""})
        render_results(out)

with tab2:
    col1, col2 = st.columns(2)
    team  = col1.text_input("Team name", placeholder="Liverpool, Juventus …")
    date2 = col2.text_input("Date (optional)", placeholder="leave blank for today", key="d2")
    if st.button("Fetch lineup"):
        if not team:
            st.warning("Enter a team name.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "lineup", "team": team, "date": date2 or ""})
            render_lineup(out)

with tab3:
    league_s = st.text_input("League", placeholder="premier league, laliga, eng.1 …")
    if st.button("Fetch standings"):
        if not league_s:
            st.warning("Enter a league.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "standings", "league": league_s})
            render_standings(out)

with tab4:
    player = st.text_input("Player lookup", placeholder="Harry Kane, Messi …")
    if st.button("Search player"):
        if not player:
            st.warning("Enter a player name.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "player", "name": player})
            render_plain(out)

with tab5:
    team_t = st.text_input("Team tier lookup", placeholder="Leicester City …")
    if st.button("Search team"):
        if not team_t:
            st.warning("Enter a team name.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "team", "name": team_t})
            render_plain(out)
