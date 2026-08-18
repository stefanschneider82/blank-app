import os
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --- KONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Turnier Live-Manager",
    page_icon="🤾",
    layout="wide",
    initial_sidebar_state="expanded",
)

ADMIN_PIN = "1234"
LOGO_PATH = "logo.png"

# Verbindung zum Google Sheet initialisieren
conn = st.connection("gsheets", type=GSheetsConnection)

TURNIERE = [
    "Männliche E-Jugend",
    "Männliche D-Jugend",
    "Männliche C-Jugend",
    "Weibliche E-Jugend",
    "Weibliche D-Jugend",
    "Weibliche C-Jugend",
    "Damen",
]


# --- HELPER-FUNKTIONEN ---
def load_matches_from_sheet(worksheet_name: str) -> pd.DataFrame:
    """Lädt die Spieldaten eines Turniers direkt aus dem jeweiligen Tabellenblatt."""
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        # Relevante Spalten standardisieren
        expected_cols = ["zeit", "team1", "team2", "score1", "score2"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden von Blatt '{worksheet_name}': {e}")
        return pd.DataFrame(
            columns=["zeit", "team1", "team2", "score1", "score2"]
        )


def save_matches_to_sheet(worksheet_name: str, df: pd.DataFrame):
    """Speichert die aktualisierten Spielergebnisse zurück in das Google Sheet."""
    try:
        conn.update(worksheet=worksheet_name, data=df)
        st.cache_data.clear()
        st.toast("✅ Ergebnisse erfolgreich in Google Sheets gespeichert!")
    except Exception as e:
        st.error(f"Fehler beim Speichern in Google Sheets: {e}")


def calculate_standings(df_matches: pd.DataFrame) -> pd.DataFrame:
    """Berechnet die Tabelle ausschließlich anhand tatsächlich gespielter Partien."""
    if df_matches.empty:
        return pd.DataFrame()

    # Alle Teams erfassen
    teams = set(df_matches["team1"].dropna()).union(
        set(df_matches["team2"].dropna())
    )
    # Entferne evtl. organisatorische Zeilen (Begrüßung, Auswertung etc.)
    teams = {
        t
        for t in teams
        if str(t).strip() and not str(t).startswith("Eröffnung")
    }

    stats = {
        team: {
            "Spiele": 0,
            "S": 0,
            "U": 0,
            "N": 0,
            "Tore": 0,
            "Gegentore": 0,
            "Tordifferenz": 0,
            "Punkte": 0,
        }
        for team in teams
    }

    for _, row in df_matches.iterrows():
        t1, t2 = row.get("team1"), row.get("team2")
        s1, s2 = row.get("score1"), row.get("score2")

        # Nur auswerten, wenn beide Teams existieren und gültige Tore eingetragen sind
        if t1 in stats and t2 in stats:
            if (
                pd.notnull(s1)
                and pd.notnull(s2)
                and str(s1).strip() != ""
                and str(s2).strip() != ""
            ):
                try:
                    s1 = int(float(s1))
                    s2 = int(float(s2))

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
                except (ValueError, TypeError):
                    continue

    for team in stats:
        stats[team]["Tordifferenz"] = (
            stats[team]["Tore"] - stats[team]["Gegentore"]
        )

    res_df = pd.DataFrame.from_dict(stats, orient="index")
    if res_df.empty:
        return res_df

    res_df = res_df.reset_index().rename(columns={"index": "Mannschaft"})
    res_df["Tore : Gegentore"] = res_df.apply(
        lambda r: f"{r['Tore']}:{r['Gegentore']}", axis=1
    )

    # Sortierung: 1. Punkte, 2. Tordifferenz, 3. Erzielte Tore
    res_df = res_df.sort_values(
        by=["Punkte", "Tordifferenz", "Tore"], ascending=[False, False, False]
    ).reset_index(drop=True)
    res_df.index += 1
    res_df.index.name = "Rang"

    return res_df[
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


# --- SIDEBAR & NAVIGATION ---
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown(
            """
            <div style="text-align: center; padding: 12px; background: #0E1117; border: 1px solid #262730; border-radius: 8px; margin-bottom: 15px;">
                <h3 style="margin:0;">🤾 Hallencup</h3>
                <span style="font-size: 12px; color: #888;">Live-Turnierplan</span>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("### Navigation")
    modus = st.radio(
        "Bereich wählen:",
        ["🏆 Live-Tabelle & Spielplan", "✏️ Ergebniseingabe (Kampfgericht)"],
    )

    turnier_sel = st.selectbox("Turnier / Spielklasse:", TURNIERE)

    st.divider()

    # PIN-geschützte Logo-Verwaltung
    with st.expander("🔒 Vereinslogo anpassen"):
        logo_pin = st.text_input(
            "PIN eingeben", type="password", key="logo_pin"
        )
        if logo_pin == ADMIN_PIN:
            uploaded_file = st.file_uploader(
                "Neues Logo (PNG/JPG)",
                type=["png", "jpg", "jpeg"],
                key="logo_upload",
            )
            if uploaded_file is not None:
                with open(LOGO_PATH, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Logo gespeichert!")
                st.rerun()
        elif logo_pin:
            st.error("PIN ungültig.")

# --- TITELBEREICH ---
header_col1, header_col2 = st.columns([1, 6])
with header_col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=90)
    else:
        st.markdown("## 🤾")
with header_col2:
    st.title(turnier_sel)
    st.caption("Echtzeit-Synchronisierung über Google Sheets")

st.divider()

# Daten für gewähltes Turnier laden
df_matches = load_matches_from_sheet(turnier_sel)

# --- BEREICH 1: LIVE TABELLE & SPIELPLAN (ZUSCHAUER) ---
if modus == "🏆 Live-Tabelle & Spielplan":
    tab_tabelle, tab_spiele = st.tabs(
        ["📊 Aktuelle Tabelle", "📅 Spielplan & Ergebnisse"]
    )

    with tab_tabelle:
        standings = calculate_standings(df_matches)
        if not standings.empty:
            st.dataframe(
                standings,
                use_container_width=True,
                column_config={
                    "Tordifferenz": st.column_config.NumberColumn(
                        "Tordifferenz", format="%+d"
                    )
                },
            )
        else:
            st.info("Noch keine Partien oder Ergebnisse vorhanden.")

    with tab_spiele:
        if not df_matches.empty:
            disp_matches = df_matches.copy()
            disp_matches["Ergebnis"] = disp_matches.apply(
                lambda r: f"{int(float(r['score1']))} : {int(float(r['score2']))}"
                if pd.notnull(r.get("score1"))
                and pd.notnull(r.get("score2"))
                and str(r.get("score1")).strip() != ""
                and str(r.get("score2")).strip() != ""
                else "- : -",
                axis=1,
            )

            cols = [
                c
                for c in ["zeit", "team1", "team2", "Ergebnis"]
                if c in disp_matches.columns
            ]
            st.dataframe(
                disp_matches[cols].rename(
                    columns={
                        "zeit": "Uhrzeit",
                        "team1": "Heim",
                        "team2": "Gast",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    if st.button("🔄 Daten neu laden"):
        st.cache_data.clear()
        st.rerun()

# --- BEREICH 2: ERGEBNISEINGABE (KAMPFGERICHT / ADMIN) ---
elif modus == "✏️ Ergebniseingabe (Kampfgericht)":
    st.subheader("Ergebnisverwaltung")
    pin = st.text_input(
        "Autorisierungs-PIN eingeben:", type="password", placeholder="PIN..."
    )

    if pin == ADMIN_PIN:
        st.success("Autorisiert als Kampfgericht.")
        st.write(
            "Aktiviere **Gespielt** nur bei beendeten Partien und trage den Endstand ein."
        )

        if not df_matches.empty:
            edit_df = df_matches.copy()

            with st.form("score_form"):
                # Nur Zeilen mit gültigen Paarungen rendern
                valid_indices = [
                    idx
                    for idx, row in edit_df.iterrows()
                    if pd.notnull(row.get("team1"))
                    and pd.notnull(row.get("team2"))
                    and str(row.get("team1")).strip() != ""
                    and str(row.get("team2")).strip() != ""
                ]

                for idx in valid_indices:
                    row = edit_df.loc[idx]
                    c_played, c_time, c_pair, c_s1, c_sep, c_s2 = st.columns(
                        [1.2, 2, 4, 1.5, 0.4, 1.5]
                    )

                    has_score = (
                        pd.notnull(row.get("score1"))
                        and pd.notnull(row.get("score2"))
                        and str(row.get("score1")).strip() != ""
                        and str(row.get("score2")).strip() != ""
                    )

                    played = c_played.checkbox(
                        "Gespielt", value=has_score, key=f"p_{idx}"
                    )
                    c_time.write(f"**{row.get('zeit', '')}**")
                    c_pair.write(
                        f"{row.get('team1', '')} – {row.get('team2', '')}"
                    )

                    s1_init = (
                        int(float(row["score1"]))
                        if has_score
                        else 0
                    )
                    s2_init = (
                        int(float(row["score2"]))
                        if has_score
                        else 0
                    )

                    s1_val = c_s1.number_input(
                        "Tore Heim",
                        min_value=0,
                        value=s1_init,
                        key=f"s1_{idx}",
                        label_visibility="collapsed",
                    )
                    c_sep.write(":")
                    s2_val = c_s2.number_input(
                        "Tore Gast",
                        min_value=0,
                        value=s2_init,
                        key=f"s2_{idx}",
                        label_visibility="collapsed",
                    )

                    st.divider()

                submitted = st.form_submit_button(
                    "💾 Änderungen in Google Sheet speichern"
                )

                if submitted:
                    changed = False
                    for idx in valid_indices:
                        is_p = st.session_state[f"p_{idx}"]
                        if is_p:
                            new_s1 = int(st.session_state[f"s1_{idx}"])
                            new_s2 = int(st.session_state[f"s2_{idx}"])
                            # Prüfe auf Wertänderung
                            if (
                                edit_df.at[idx, "score1"] != new_s1
                                or edit_df.at[idx, "score2"] != new_s2
                            ):
                                edit_df.at[idx, "score1"] = new_s1
                                edit_df.at[idx, "score2"] = new_s2
                                changed = True
                        else:
                            # Nicht gespielt -> Werte leeren
                            if (
                                pd.notnull(edit_df.at[idx, "score1"])
                                or pd.notnull(edit_df.at[idx, "score2"])
                            ):
                                edit_df.at[idx, "score1"] = None
                                edit_df.at[idx, "score2"] = None
                                changed = True

                    if changed:
                        save_matches_to_sheet(turnier_sel, edit_df)
                        st.rerun()
                    else:
                        st.info("Keine Änderungen vorhanden.")

    elif pin:
        st.error("PIN fehlerhaft. Zugriff verweigert.")

