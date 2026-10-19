
"""Pagina voor het aanmaken van een nieuwe patiënt."""

import sqlite3
from contextlib import closing
from pathlib import Path

import streamlit as st
import prediction


# 1. Configuratie

DB_FILE = Path(__file__).resolve().parent.parent / "ehr.db"

st.set_page_config(
    page_title="Nieuwe patiënt | Longkanker CDSS",
    page_icon="🫁",
    layout="wide",
)

st.title("Nieuwe NSCLC patiënt toevoegen aan de database")
st.caption(
    "Vul hier de patiënt- en tumorkenmerken in"
)

# 2. Controleer database en kolommen

if not DB_FILE.exists():
    st.error("ehr.db is niet gevonden. Voer eerst setup_database.py uit.")
    st.stop()

EXPECTED_COLUMNS = ["id", "display_name"] + prediction.FEATURES

try:
    with closing(sqlite3.connect(DB_FILE)) as conn:
        rows = conn.execute("PRAGMA table_info(patient)").fetchall()

    if not rows:
        st.error("De tabel 'patient' bestaat niet in ehr.db.")
        st.stop()

    database_columns = {row[1] for row in rows}
    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in database_columns
    ]

    if missing_columns:
        st.error(
            "De database mist de volgende kolommen: "
            + ", ".join(missing_columns)
        )
        st.stop()

except sqlite3.Error as error:
    st.error(f"De database kon niet worden gecontroleerd: {error}")
    st.stop()


# 3. Keuzemogelijkheden

# De labels worden aan de gebruiker getoond.
# De bijbehorende numerieke codes worden opgeslagen in de database.
STADIUM_CODES = {
    "0": 0,
    "1A": 1,
    "1B": 2,
    "2A": 3,
    "2B": 4,
    "3A": 5,
    "3B": 6,
    "3C": 7,
    "4": 8,
    "M": 9,
}

GESLACHT_CODES = {
    "Man": 1,
    "Vrouw": 2,
}

BEHANDELING_CODES = [0, 1, 2, 3, 4]


# 4. Invoervelden

st.subheader("Algemene gegevens")

with st.form("new_patient_form"):

    display_name = st.text_input(
        "Naam van de patiënt",
        placeholder="Bijvoorbeeld: Ruud van der Weert",
    )

    st.divider()
    st.subheader("Patiëntkenmerken")

    # Geslacht: keuze uit Man of Vrouw.
    geslacht_label = st.selectbox(
        "Geslacht",
        options=list(GESLACHT_CODES.keys()),
        index=None,
        placeholder="Selecteer geslacht",
    )

    # Leeftijd.
    leeft = st.number_input(
        "Leeftijd",
        min_value=0,
        max_value=120,
        value=None,
        step=1,
        placeholder="Leeftijd in jaren",
    )

    # Diagnostische kenmerken
    st.subheader("Diagnostische kenmerken")

    diag_basis = st.number_input(
        "Diagnostische basis (diag_basis)",
        min_value=0,
        max_value=10_000_000,
        value=None,
        step=1,
    )

    morf = st.number_input(
        "Morfologie (morf)",
        min_value=0,
        max_value=10_000_000,
        value=None,
        step=1,
    )

    gedrag = st.number_input(
        "Gedrag (gedrag)",
        min_value=0,
        max_value=10_000_000,
        value=None,
        step=1,
    )

    diffgrad = st.number_input(
        "Differentiatiegraad (diffgrad)",
        min_value=0,
        max_value=10_000_000,
        value=None,
        step=1,
    )

    st.subheader("Tumorkenmerken")

    stadium_label = st.selectbox(
        "Stadium",
        options=list(STADIUM_CODES.keys()),
        index=None,
        placeholder="Selecteer stadium",
        help="Selecteer het stadium volgens de codering van jouw dataset.",
    )

    # Behandelingen
    st.subheader("Behandelkenmerken")

    chemo = st.selectbox(
        "Chemotherapie (chemo)",
        options=BEHANDELING_CODES,
        index=None,
        placeholder="Selecteer waarde",
    )

    target = st.selectbox(
        "Targeted therapy (target)",
        options=BEHANDELING_CODES,
        index=None,
        placeholder="Selecteer waarde",
    )

    rt = st.selectbox(
        "Radiotherapie (rt)",
        options=BEHANDELING_CODES,
        index=None,
        placeholder="Selecteer waarde",
    )

    st.divider()

    submitted = st.form_submit_button(
        "Patiënt opslaan",
        type="primary",
        use_container_width=True,
    )


# 5. Validatie en opslag

if submitted:
    errors = []

    if not display_name.strip():
        errors.append("Vul een naam in.")

    if geslacht_label is None:
        errors.append("Selecteer het geslacht.")

    if stadium_label is None:
        errors.append("Selecteer een stadium.")

    numeric_fields = {
        "leeft": leeft,
        "diag_basis": diag_basis,
        "morf": morf,
        "gedrag": gedrag,
        "diffgrad": diffgrad,
    }

    for field_name, value in numeric_fields.items():
        if value is None:
            errors.append(f"Vul een waarde in voor '{field_name}'.")

    for field_name, value in {
        "chemo": chemo,
        "target": target,
        "rt": rt,
    }.items():
        if value is None:
            errors.append(f"Selecteer een waarde voor '{field_name}'.")

    if errors:
        for error in errors:
            st.error(error)

    else:
        # Stel alle databasewaarden samen.
        patient_data = {
            "display_name": display_name.strip(),
            "leeft": int(leeft),
            "gesl": GESLACHT_CODES[geslacht_label],
            "tumsoort": 302310,
            "diag_basis": int(diag_basis),
            "morf": int(morf),
            "gedrag": int(gedrag),
            "diffgrad": int(diffgrad),
            "stadium": STADIUM_CODES[stadium_label],
            "chemo": int(chemo),
            "target": int(target),
            "rt": int(rt),
            "SCLC": 0,
        }

        # Gebruik exact de volgorde die prediction.py verwacht.
        columns = ["display_name"] + prediction.FEATURES

        quoted_columns = ", ".join(
            '"' + column.replace('"', '""') + '"'
            for column in columns
        )

        placeholders = ", ".join("?" for _ in columns)

        sql = (
            f"INSERT INTO patient ({quoted_columns}) "
            f"VALUES ({placeholders})"
        )

        parameters = [
            patient_data[column]
            for column in columns
        ]

        try:
            with closing(sqlite3.connect(DB_FILE)) as conn:
                cursor = conn.execute(sql, parameters)
                new_patient_id = cursor.lastrowid
                conn.commit()

            st.success(
                f"Patiënt '{display_name.strip()}' is succesvol opgeslagen. "
                f"Patiënt-ID: {new_patient_id}."
            )

            st.write("**Opgeslagen waarden ter controle**")

            st.table({
                "Kenmerk": columns,
                "Waarde": parameters,
            })

            st.info(
                "De patiënt is toegevoegd. Keer terug naar Home om te voorspellen voor deze patiënt."
            )

        except sqlite3.IntegrityError as error:
            st.error(
                "De patiënt kon niet worden opgeslagen vanwege een "
                f"error: {error}"
            )

        except sqlite3.Error as error:
            st.error(f"Opslaan in de database is mislukt: {error}")


# 6. Navigatie

st.divider()

if st.button(
    "Terug naar Homepagina",
    use_container_width=True,
):
    st.switch_page("Home.py")
