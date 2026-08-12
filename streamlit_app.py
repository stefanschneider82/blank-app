import os
import sqlite3
import pandas as pd
import streamlit as st

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="Turnier Live-Manager",
    page_icon="🤾",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "turnier_data.db"
DEFAULT_PIN = "1234"  # PIN für Schiedsrichter / Kampfgericht

# --- DATABASE INITIALIZATION & SEEDING ---
INITIAL_DATA = {
    "Männliche E-Jugend": [
        ("09:45–10:00 Uhr", "Hohe Geest", "TuRa Meldorf"),
        ("10:05–10:20 Uhr", "HSG KreMü I", "HSG KreMü II"),
        ("10:25–10:40 Uhr", "Hohe Geest", "HSG KreMü I"),
        ("10:45–11:00 Uhr", "TuRa Meldorf", "HSG KreMü II"),
        ("11:05–11:20 Uhr", "Hohe Geest", "HSG KreMü II"),
        ("11:25–11:40 Uhr", "TuRa Meldorf", "HSG KreMü I"),
    ],
    "Männliche D-Jugend": [
        ("12:45–13:06 Uhr", "Hohe Geest", "HSG Tills Löwen"),
        ("13:10–13:31 Uhr", "TuRa Meldorf", "KreMü 1"),
        ("13:35–13:56 Uhr", "Hohe Geest", "KreMü 2"),
        ("14:00–14:21 Uhr", "HSG Tills Löwen", "TuRa Meldorf"),
        ("14:25–14:46 Uhr", "KreMü 1", "KreMü 2"),
        ("14:50–15:11 Uhr", "Hohe Geest", "TuRa Meldorf"),
        ("15:15–15:36 Uhr", "HSG Tills Löwen", "KreMü 1"),
        ("15:40–16:01 Uhr", "TuRa Meldorf", "KreMü 2"),
        ("16:05–16:26 Uhr", "Hohe Geest", "KreMü 1"),
        ("16:30–16:51 Uhr", "HSG Tills Löwen", "KreMü 2"),
    ],
    "Männliche C-Jugend": [
        ("10:15–10:46 Uhr", "HSG Hohe Geest", "Haie"),
        ("10:50–11:21 Uhr", "Haie", "TSV Vineta Audorf"),
        ("11:25–11:56 Uhr", "TSV Vineta Audorf", "HSG Hohe Geest"),
    ],
    "Weibliche E-Jugend": [
        ("09:15–09:30 Uhr", "Hohe Geest", "TuRa Meldorf I"),
        ("09:35–09:50 Uhr", "TuRa Meldorf II", "Rellinger TV"),
        ("09:55–10:10 Uhr", "Hohe Geest", "Eider Harde"),
        ("10:15–10:30 Uhr", "TuRa Meldorf I", "TuRa Meldorf II"),
        ("10:35–10:50 Uhr", "Rellinger TV", "Eider Harde"),
        ("10:55–11:10 Uhr", "Hohe Geest", "TuRa Meldorf II"),
        ("11:15–11:30 Uhr", "TuRa Meldorf I", "Rellinger TV"),
        ("11:35–11:50 Uhr", "TuRa Meldorf II", "Eider Harde"),
        ("11:55–12:10 Uhr", "Hohe Geest", "Rellinger TV"),
        ("12:15–12:30 Uhr", "TuRa Meldorf I", "Eider Harde"),
    ],
    "Weibliche D-Jugend": [
        ("13:15–13:36 Uhr", "Hohe Geest", "Vineta Audorf"),
        ("13:40–14:01 Uhr", "Lübecker Turnerschaft", "Rellinger TV"),
        ("14:05–14:26 Uhr", "Hohe Geest", "HSG KreMü"),
        ("14:30–14:51 Uhr", "Vineta Audorf", "Lübecker Turnerschaft"),
        ("14:55–15:16 Uhr", "Rellinger TV", "HSG KreMü"),
        ("15:20–15:41 Uhr", "Hohe Geest", "Lübecker Turnerschaft"),
        ("15:45–16:06 Uhr", "Vineta Audorf", "Rellinger TV"),
        ("16:10–16:31 Uhr", "Lübecker Turnerschaft", "HSG KreMü"),
        ("16:35–16:56 Uhr", "Hohe Geest", "Rellinger TV"),
        ("17:00–17:21 Uhr", "Vineta Audorf", "HSG KreMü"),
    ],
    "Weibliche C-Jugend": [
        ("13:15–13:35 Uhr", "Hohe Geest", "HSG Ohlau"),
        ("13:40–14:00 Uhr", "Rellinger TV", "TuRa Meldorf"),
        ("14:05–14:25 Uhr", "Hohe Geest", "MTV Heide"),
        ("14:30–14:50 Uhr", "HSG Ohlau", "Rellinger TV"),
        ("14:55–15:15 Uhr", "TuRa Meldorf", "MTV Heide"),
        ("15:20–15:40 Uhr", "Hohe Geest", "Rellinger TV"),
        ("15:45–16:05 Uhr", "HSG Ohlau", "TuRa Meldorf"),
        ("16:10–16:30 Uhr", "Rellinger TV", "MTV Heide"),
        ("16:35–16:55 Uhr", "Hohe Geest", "TuRa Meldorf"),
        ("17:00–17:20 Uhr", "HSG Ohlau", "MTV Heide"),
    ],
    "Damen": [
        ("10:00–10:20 Uhr", "TS Schenefeld", "HSG Südtondern"),
        ("10:25–10:45 Uhr", "LSC99", "HSG EPT"),
        ("10:50–11:10 Uhr", "Störtal Hummeln", "HSG Ohlau"),
        ("11:15–11:35 Uhr", "HSG Südtondern", "Lübeck"),
        ("11:40–12:00 Uhr", "TS Schenefeld", "HSG EPT"),
        ("12:05–12:25 Uhr", "LSC99", "HSG Ohlau"),
        ("12:30–12:50 Uhr", "Störtal Hummeln", "Lübeck"),
        ("12:55–13:15 Uhr", "HSG Südtondern", "HSG EPT"),
        ("13:20–13:40 Uhr", "TS Schenefeld", "HSG Ohlau"),
        ("13:45–14:05 Uhr", "LSC99", "Lübeck"),
        ("14:10–14:30 Uhr", "HSG Südtondern", "Störtal Hummeln"),
        ("14:35–14:55 Uhr", "HSG Ohlau", "HSG EPT"),
        ("15:00–15:20 Uhr", "TS Schenefeld", "Lübeck"),
        ("15:25–15:45 Uhr", "LSC99", "Störtal Hummeln"),
        ("15:50–16:10 Uhr", "HSG Südtondern", "HSG Ohlau"),
        ("16:15–16:35 Uhr", "Lübeck", "HSG EPT"),
        ("16:40–17:00 Uhr", "TS Schenefeld", "Störtal Hummeln"),
        ("17:05–17:25 Uhr", "HSG Südtondern", "LSC99"),
        ("17:30–17:50 Uhr", "HSG Ohlau", "Lübeck"),
        ("17:55–18:15 Uhr", "Störtal Hummeln", "HSG EPT"),
        ("18:20–18:40 Uhr", "TS Schenefeld", "LSC99"),
    ],
}


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turnier TEXT,
            zeit TEXT,
            team1 TEXT,
            team2 TEXT,
            score1 INTEGER,
            score2 INTEGER
        )
    """
    )

    # Initial-Befüllung, falls Tabelle leer ist
    c.execute("SELECT COUNT(*) FROM matches")
    if c.fetchone()[0] == 0:
        for turnier, matches in INITIAL_DATA.items():
            for zeit, t1, t2 in matches:
                c.execute(
                    "INSERT INTO matches (turnier, zeit, team1, team2) VALUES (?, ?, ?, ?)",
                    (turnier, zeit, t1, t2),
                )
        conn.commit()
    conn.close()


init_db()


# --- HELPER FUNCTIONS ---
def load_matches(turnier):
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM matches WHERE turnier = ? ORDER BY id ASC",
        conn,
        params=(turnier,),
    )
    conn.close()
    return df


def update_match_score(match_id, s1, s2):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE matches SET score1 = ?, score2 = ? WHERE id = ?",
        (s1, s2, match_id),
    )
    conn.commit()
    conn.close()


def calculate_table(matches_df):
    stats = {}

    # Alle Teams erfassen
    all_teams = set(matches_df["team1"]).union(set(matches_df["team2"]))
    for team in all_teams:
        stats[team] = {
            "Spiele": 0,
            "S": 0,
            "U": 0,
            "N": 0,
            "Tore": 0,
            "Gegentore": 0,
            "Tordifferenz": 0,
            "Punkte": 0,
        }

    # Spiele auswerten
    for _, row in matches_df.iterrows():
        s1, s2 = row["score1"], row["score2"]
        if pd.notnull(s1) and pd.notnull(s2):
            t1, t2 = row["team1"], row["team2"]
            s1, s2 = int(s1), int(s2)

            stats[t1]["Spiele"] += 1
            stats[t2]["Spiele"] += 1
            stats[t1]["Tore"] += s1
            stats[t1]["Gegentore"] += s2
            stats[t2]["Tore"] += s2
            stats[t2]["Gegentore"] += s1

            if s1 > s2:
                stats[t1]["S"] += 1
                stats[t1]["Punkte"] += 2
                stats[t2]["N"] += 1
            elif s2 > s1:
                stats[t2]["S"] += 1
                stats[t2]["Punkte"] += 2
                stats[t1]["N"] += 1
            else:
                stats[t1]["U"] += 1
                stats[t1]["Punkte"] += 1
                stats[t2]["U"] += 1
                stats[t2]["Punkte"] += 1

    for team in stats:
        stats[team]["Tordifferenz"] = (
            stats[team]["Tore"] - stats[team]["Gegentore"]
        )

    df = pd.DataFrame.from_dict(stats, orient="index")
    if df.empty:
        return df

    df = df.reset_index().rename(columns={"index": "Mannschaft"})

    # Formatierung Torverhältnis für hübsche Anzeige
    df["Tore : Gegentore"] = df.apply(
        lambda r: f"{r['Tore']}:{r['Gegentore']}", axis=1
    )

    # Sortierung: Punkte DESC, Tordifferenz DESC, Erzielte Tore DESC
    df = df.sort_values(
        by=["Punkte", "Tordifferenz", "Tore"], ascending=[False, False, False]
    ).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rang"

    return df[
        [
            "Mannschaft",
            "Spiele",
            "S",
            "U",
            "N",
            "Tore : Gegentore",
            "Tordifferenz",
            "Punkte",
        ]
    ]


# --- UI HEADER & LOGO INTEGRATION ---
logo_path = "logo.png"

# Sidebar Branding
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_column_width=True)
    else:
        # Platzhalter Logo / Header
        st.markdown(
            """
            <div style="text-align: center; padding: 15px; background: #1E88E5; color: white; border-radius: 10px; margin-bottom: 20px;">
                <h2 style="margin:0; font-size: 24px;">🤾 Hallencup</h2>
                <span style="font-size: 13px;">Live Turnier-Manager</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.title("Navigation")
    modus = st.radio(
        "Modus auswählen:",
        ["🏆 Live-Tabelle & Spielplan", "✏️ Ergebniseingabe (Schiedsrichter)"],
    )

    turnier_auswahl = st.selectbox(
        "Turnier / Altersklasse:", list(INITIAL_DATA.keys())
    )

    st.divider()

    # Logo Uploader im Admin Bereich der Sidebar
    with st.expander("🖼️ Vereins-Logo verwalten"):
        uploaded_logo = st.file_uploader(
            "Neues Logo hochladen (PNG/JPG)", type=["png", "jpg", "jpeg"]
        )
        if uploaded_logo is not None:
            with open(logo_path, "wb") as f:
                f.write(uploaded_logo.getbuffer())
            st.success("Logo aktualisiert! Bitte Seite neu laden.")
            st.rerun()


# Main Title Header
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_column_width=True)
    else:
        st.markdown("### 🤾‍♂️")

with col_title:
    st.title(f"Turnier: {turnier_auswahl}")
    st.caption("Echtzeit-Aktualisierung für Tabellen, Ergebnisse und Tordifferenz")

st.divider()

# --- MODUS 1: ZUSCHAUER ANSICHT (LIVE TABELLE & SPIELPLAN) ---
if modus == "🏆 Live-Tabelle & Spielplan":
    matches_df = load_matches(turnier_auswahl)
    standings_df = calculate_table(matches_df)

    tab1, tab2 = st.tabs(["📊 Live-Tabelle", "📅 Spielplan & Ergebnisse"])

    with tab1:
        st.subheader("Aktuelle Tabelle")

        # Styling der Tabelle
        st.dataframe(
            standings_df,
            use_container_width=True,
            column_config={
                "Rang": st.column_config.NumberColumn("Rang", format="%d"),
                "Tordifferenz": st.column_config.NumberColumn(
                    "Tordifferenz", format="%+d"
                ),
            },
        )

        # Quick Stats Metrics
        st.caption(
            "💡 Sortierung: 1. Punkte -> 2. Tordifferenz -> 3. Erzielte Tore"
        )

    with tab2:
        st.subheader("Ansetzungen & Spielergebnisse")

        # Anzeige aufbereiten
        display_schedule = matches_df.copy()
        display_schedule["Ergebnis"] = display_schedule.apply(
            lambda r: f"{int(r['score1'])} : {int(r['score2'])}"
            if pd.notnull(r["score1"]) and pd.notnull(r["score2"])
            else "- : -",
            axis=1,
        )

        st.dataframe(
            display_schedule[["zeit", "team1", "team2", "Ergebnis"]].rename(
                columns={
                    "zeit": "Uhrzeit",
                    "team1": "Heimmannschaft",
                    "team2": "Gastmannschaft",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    if st.button("🔄 Ansicht Aktualisieren"):
        st.rerun()

# --- MODUS 2: AUTHORISIERTES ERGEBNISSE EINTRAGEN ---
elif modus == "✏️ Ergebniseingabe (Schiedsrichter)":
    st.subheader("Geschützter Bereich für Schiedsrichter & Kampfgericht")

    pin_input = st.text_input(
        "Bitte Autorisiere dich mit der PIN:",
        type="password",
        placeholder="PIN eingeben...",
    )

    if pin_input == DEFAULT_PIN:
        st.success("✅ Erfogreich autorisiert!")
        st.write(
            "Trage die Tore ein und klicke auf **Speichern**, um die Live-Tabelle sofort zu aktualisieren."
        )

        matches_df = load_matches(turnier_auswahl)

        with st.form("score_entry_form"):
            updated_count = 0
            for idx, row in matches_df.iterrows():
                col_zeit, col_match, col_s1, col_trenner, col_s2 = st.columns(
                    [2, 4, 2, 1, 2]
                )

                col_zeit.write(f"**{row['zeit']}**")
                col_match.write(f"{row['team1']} vs. {row['team2']}")

                val1 = int(row["score1"]) if pd.notnull(row["score1"]) else 0
                val2 = int(row["score2"]) if pd.notnull(row["score2"]) else 0

                s1 = col_s1.number_input(
                    f"Tore {row['team1']}",
                    min_value=0,
                    value=val1,
                    key=f"s1_{row['id']}",
                    label_visibility="collapsed",
                )
                col_trenner.write(":")
                s2 = col_s2.number_input(
                    f"Tore {row['team2']}",
                    min_value=0,
                    value=val2,
                    key=f"s2_{row['id']}",
                    label_visibility="collapsed",
                )

                st.divider()

            submitted = st.form_submit_button(
                "💾 Alle Ergebnisse Jetzt Speichern"
            )
            if submitted:
                for idx, row in matches_df.iterrows():
                    new_s1 = st.session_state[f"s1_{row['id']}"]
                    new_s2 = st.session_state[f"s2_{row['id']}"]
                    update_match_score(row["id"], new_s1, new_s2)
                st.toast("Alle Ergebnisse wurden erfolgreich gespeichert!")
                st.rerun()

    elif pin_input != "":
        st.error("❌ Falsche PIN. Zugriff verweigert.")
