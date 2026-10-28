import io
import sys
import contextlib
import streamlit as st

sys.path.insert(0, ".")
import espn_results as espn

st.set_page_config(page_title="ESPN Results", page_icon="⚽", layout="centered")
st.title("⚽ ESPN Results")


def capture(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            fn(*args)
        except Exception as e:
            return f"Error: {e}"
    return buf.getvalue()


tab1, tab2, tab3, tab4, tab5 = st.tabs(["Results", "Lineup", "Standings", "Player", "Team"])

# ── Results ──────────────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([2, 2])
    date  = col1.text_input("Date (YYYYMMDD or YYYY-MM-DD)", placeholder="leave blank for today")
    league = col2.text_input("League filter", placeholder="premier league, laliga …")
    if st.button("Fetch results"):
        with st.spinner("Fetching…"):
            html, source_url = espn.fetch_html(date or None)
            state = espn.extract_state(html)
            scoreboard = espn.get_scoreboard(state)
            out = capture(espn.print_scoreboard, scoreboard, date or None, source_url, league or None)
        st.code(out, language=None)

# ── Lineup ───────────────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns([2, 2])
    team = col1.text_input("Team name", placeholder="Liverpool, Juventus …")
    date2 = col2.text_input("Date (optional)", placeholder="leave blank for today", key="lineup_date")
    if st.button("Fetch lineup"):
        if not team:
            st.warning("Enter a team name.")
        else:
            with st.spinner("Fetching…"):
                out = capture(espn.find_lineup, team, date2 or None)
            st.code(out, language=None)

# ── Standings ────────────────────────────────────────────────────────────────
with tab3:
    league_s = st.text_input("League", placeholder="premier league, laliga, eng.1 …")
    if st.button("Fetch standings"):
        if not league_s:
            st.warning("Enter a league.")
        else:
            with st.spinner("Fetching…"):
                slug = espn.LEAGUE_SLUGS.get(league_s.lower(), league_s)
                out = capture(espn.fetch_standings, slug)
            st.code(out, language=None)

# ── Player ───────────────────────────────────────────────────────────────────
with tab4:
    player = st.text_input("Player lookup", placeholder="Harry Kane, Messi …")
    if st.button("Search player"):
        if not player:
            st.warning("Enter a player name.")
        else:
            with st.spinner("Fetching…"):
                out = capture(espn.find_player, player)
            st.code(out, language=None)

# ── Team tier ─────────────────────────────────────────────────────────────────
with tab5:
    team_t = st.text_input("Team tier lookup", placeholder="Leicester City …")
    if st.button("Search team"):
        if not team_t:
            st.warning("Enter a team name.")
        else:
            with st.spinner("Fetching…"):
                out = capture(espn.find_team_tier, team_t)
            st.code(out, language=None)
