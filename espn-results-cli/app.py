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
    rows = []
    for line in lines:
        if not line.strip() or line.startswith("Standings") or line.startswith("http"):
            continue
        if re.match(r"^-+$", line):
            continue
        if re.match(r"^\d{4}", line):
            st.subheader(f"🏆 {line.strip()}")
            continue
        if re.match(r"^\s+#\s+Team", line):
            continue
        m = re.match(r"^\s*(\d+)\s{2,}(.+?)\s{2,}(\d+)\s+(\d+)\s+([+-]?\d+)\s+(\d+).*?(?:\[(.+)\])?$", line)
        if m:
            rows.append({"#": int(m.group(1)), "Team": m.group(2).strip(),
                         "J": m.group(3), "P": m.group(4), "DIF": m.group(5),
                         "PTS": m.group(6), "Zone": (m.group(7) or "").strip()})

    if not rows:
        st.code(text); return

    ZONE_COLORS = {"champions": "#1a6b3c", "europa": "#1a4a8a", "conference": "#2d6b8a",
                   "relegation": "#8a1a1a", "promotion": "#1a6b3c"}

    st.markdown("""<style>
    .st-row{display:flex;align-items:center;padding:6px 4px;border-bottom:1px solid #2a2a2a;font-size:14px}
    .st-rank{width:32px;font-weight:bold;color:#aaa}.st-team{flex:1;font-weight:500}
    .st-stat{width:40px;text-align:center;color:#ccc}.st-pts{width:40px;text-align:center;font-weight:bold;color:#fff}
    .st-zone{width:12px;border-radius:2px;height:20px;margin-right:8px}.st-hdr{color:#666;font-size:12px}
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="st-row st-hdr"><div class="st-zone"></div><div class="st-rank">#</div><div class="st-team">Team</div><div class="st-stat">J</div><div class="st-stat">P</div><div class="st-stat">DIF</div><div class="st-pts">PTS</div></div>', unsafe_allow_html=True)

    for r in rows:
        zl = r["Zone"].lower()
        color = next((v for k, v in ZONE_COLORS.items() if k in zl), "transparent")
        dif_color = "#4caf50" if r["DIF"].startswith("+") else ("#f44336" if r["DIF"].startswith("-") else "#ccc")
        st.markdown(
            f'<div class="st-row" title="{r["Zone"]}">'
            f'<div class="st-zone" style="background:{color}"></div>'
            f'<div class="st-rank">{r["#"]}</div><div class="st-team">{r["Team"]}</div>'
            f'<div class="st-stat">{r["J"]}</div><div class="st-stat">{r["P"]}</div>'
            f'<div class="st-stat" style="color:{dif_color}">{r["DIF"]}</div>'
            f'<div class="st-pts">{r["PTS"]}</div></div>', unsafe_allow_html=True)

    shown, legend_parts = set(), []
    for r in rows:
        z = r["Zone"]
        if z and z not in shown:
            shown.add(z)
            color = next((v for k, v in ZONE_COLORS.items() if k in z.lower()), "#555")
            legend_parts.append(f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:12px;color:#aaa"><span style="width:10px;height:10px;border-radius:2px;background:{color};display:inline-block"></span>{z}</span>')
    if legend_parts:
        st.markdown("<br>" + "".join(legend_parts), unsafe_allow_html=True)


def render_player(text):
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        st.info("No data."); return

    # extract hidden espn_id and headshot lines
    espn_id = None
    headshot = None
    clean = []
    for l in lines:
        if l.startswith("espn_id:"):
            espn_id = l.split(":", 1)[1].strip()
        elif l.startswith("headshot:"):
            headshot = l.split(":", 1)[1].strip()
        else:
            clean.append(l)
    lines = clean

    info, career, in_career = {}, [], False
    for line in lines[1:]:
        if line.strip().startswith("Career"):
            in_career = True; continue
        if re.match(r"^-+$", line.strip()):
            continue
        if in_career:
            m = re.match(r"^\s+(.+?)\s+\((\d+) apps?\)", line)
            if m:
                career.append((m.group(1).strip(), m.group(2)))
        else:
            m = re.match(r"^\s+(.+?)\s*:\s*(.+)$", line)
            if m:
                info[m.group(1).strip()] = m.group(2).strip()

    ICONS = {"Current club": "🏟️", "League": "🏆", "Position": "⚽", "Nationality": "🌍"}

    if headshot:
        col_img, col_info = st.columns([1, 3])
        col_img.image(headshot, width=160)
        col_info.markdown(f"## {lines[0].strip()}")
        metric_cols = col_info.columns(2)
    else:
        st.markdown(f"## {lines[0].strip()}")
        metric_cols = st.columns(2)

    for i, (k, v) in enumerate(info.items()):
        metric_cols[i % 2].metric(label=f"{ICONS.get(k, '•')} {k}", value=v)

    if career:
        st.markdown("---\n**Career**")
        for club, apps in career:
            st.markdown(f"&nbsp;&nbsp;🔹 **{club}** — {apps} apps", unsafe_allow_html=True)


def render_team(text):
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        st.info("No data."); return

    m = re.match(r"^(.+?)\s+→\s+(.+)$", lines[0])
    if m:
        st.markdown(f"## 🏟️ {m.group(1).strip()}")
        st.markdown(f"**{m.group(2).strip()}**")
    else:
        st.markdown(f"## 🏟️ {lines[0]}")

    ICONS = {"Stadium": "🏟️", "Location": "📍", "Coords": "🗺️", "Maps": "🗺️", "GMaps": "📌"}
    for line in lines[1:]:
        m = re.match(r"^\s+(.+?)\s*:\s*(.+)$", line)
        if not m:
            continue
        k, v = m.group(1).strip(), m.group(2).strip()
        icon = ICONS.get(k, "•")
        if k == "Maps":
            st.markdown(f"{icon} [OpenStreetMap]({v})")
        elif k == "GMaps":
            st.markdown(f"{icon} [Google Maps]({v})")
        elif k == "Coords":
            st.caption(f"{icon} {v}")
        else:
            st.markdown(f"{icon} **{k}:** {v}")


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
            render_player(out)

with tab5:
    team_t = st.text_input("Team tier lookup", placeholder="Leicester City …")
    if st.button("Search team"):
        if not team_t:
            st.warning("Enter a team name.")
        else:
            with st.spinner("Fetching…"):
                out = call({"action": "team", "name": team_t})
            render_team(out)
