import requests
import streamlit as st

API = "https://v114kxt4i7.execute-api.us-east-1.amazonaws.com/"


def call(params):
    try:
        r = requests.get(API, params=params, timeout=30, verify=False)
        data = r.json()
        return data.get("result") or data.get("error", "No response")
    except Exception as e:
        return f"Error: {e}"


st.set_page_config(page_title="ESPN Results", page_icon="⚽", layout="centered")
st.title("⚽ ESPN Results")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Results", "Lineup", "Standings", "Player", "Team"])

with tab1:
    col1, col2 = st.columns(2)
    date   = col1.text_input("Date (YYYYMMDD or YYYY-MM-DD)", placeholder="leave blank for today")
    league = col2.text_input("League filter", placeholder="premier league, laliga …")
    if st.button("Fetch results"):
        with st.spinner("Fetching…"):
            out = call({"action": "results", "date": date or "", "league": league or ""})
        st.code(out, language=None)

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
            st.code(out, language=None)

with tab3:
    league_s = st.text_input("League", placeholder="premier league, laliga, eng.1 …")
    if st.button("Fetch standings"):
        if not league_s:
            st.warning("Enter a league.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "standings", "league": league_s})
            st.code(out, language=None)

with tab4:
    player = st.text_input("Player lookup", placeholder="Harry Kane, Messi …")
    if st.button("Search player"):
        if not player:
            st.warning("Enter a player name.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "player", "name": player})
            st.code(out, language=None)

with tab5:
    team_t = st.text_input("Team tier lookup", placeholder="Leicester City …")
    if st.button("Search team"):
        if not team_t:
            st.warning("Enter a team name.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "team", "name": team_t})
            st.code(out, language=None)
