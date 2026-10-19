
"""Pagina voor het verwijderen van een patiënt."""

import sqlite3
from contextlib import closing
from pathlib import Path

import streamlit as st


# 1. Configuratie

DB_FILE = Path(__file__).resolve().parent.parent / "ehr.db"

st.set_page_config(
    page_title="Patiënt verwijderen | Longkanker CDSS",
    page_icon="🫁",
    layout="wide",
)

st.title("Patiënt verwijderen")
st.caption("Via deze pagina verwijdert u een patiënt uit de database")

st.warning(
    "Let op: verwijderen is definitief. De patiëntgegevens kunnen na het verwijderen niet meer terug worden gehaald!"
)

if not DB_FILE.exists():
    st.error("ehr.db is niet gevonden.")
    st.stop()


# 2. Patiënten ophalen

def load_patients():
    """Lees de patiënt-ID's en namen uit de database."""
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, display_name FROM patient ORDER BY id"
        ).fetchall()

    return [dict(row) for row in rows]


try:
    patients = load_patients()
except sqlite3.Error as error:
    st.error(f"De patiënten konden niet worden geladen: {error}")
    st.stop()

if not patients:
    st.info("Er staan momenteel geen patiënten in de database.")
    if st.button("Terug naar patiëntenoverzicht"):
        st.switch_page("Home.py")
    st.stop()


# 3. Selecteer een patiënt

patient_options = {
    patient["id"]: patient["display_name"]
    for patient in patients
}

selected_id = st.selectbox(
    "Selecteer te verwijderen patiënt uit de lijst",
    options=list(patient_options.keys()),
    format_func=lambda patient_id: (
        f"{patient_options[patient_id]} (ID: {patient_id})"
    ),
)

selected_name = patient_options[selected_id]

st.markdown(f"**Geselecteerde patiënt:** {selected_name}")
st.markdown(f"**Patiënt-ID:** {selected_id}")


# 4. Sessiegegevens

# Zet de standaardwaarden voor de pagina
st.session_state.setdefault("delete_patient_id", None)
st.session_state.setdefault("delete_patient_name", None)
st.session_state.setdefault("delete_deceased", None)


def reset_delete_state(): # Zet standaardwaarden terug (leeg)
    st.session_state.delete_patient_id = None
    st.session_state.delete_patient_name = None
    st.session_state.delete_deceased = None


# 5. Eerste pop-up: overleden?

@st.dialog("Bevestiging 1 van 2")
def deceased_dialog(patient_id, patient_name):
    st.write(f"Is patiënt **{patient_name}** overleden?")
    st.warning("Let op! Dit is een demofunctionaliteit, overleden patiënten worden niet bijgehouden")

    deceased_answer = st.radio(
        "Selecteer uw antwoord",
        options=["Ja", "Nee"],
        index=None,
        key="deceased_answer",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Doorgaan", type="primary", use_container_width=True):
            if deceased_answer is None:
                st.warning("Selecteer eerst of de patiënt is overleden")
            else:
                st.session_state.delete_patient_id = patient_id
                st.session_state.delete_patient_name = patient_name
                st.session_state.delete_deceased = (
                    deceased_answer == "Ja"
                )
                st.rerun()

    with col2:
        if st.button("Annuleren", use_container_width=True):
            reset_delete_state()
            st.rerun()


# 6. Tweede pop-up: definitieve verwijdering

@st.dialog("Bevestiging 2 van 2")
def final_delete_dialog(patient_id, patient_name):
    st.error(
        f"Weet u zeker dat u patiënt **{patient_name}** wil verwijderen uit de database?"
        " De patiëntdata is na verwijderen niet meer terug te halen!"
    )

    st.write(
        "Als u bevestigt, wordt de patiënt definitief uit de database verwijderd."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Ja, definitief verwijderen",
            type="primary",
            use_container_width=True,
        ):
            try:
                with closing(sqlite3.connect(DB_FILE)) as conn:
                    cursor = conn.execute(
                        "DELETE FROM patient WHERE id = ?",
                        (patient_id,),
                    )
                    conn.commit()
                    deleted_rows = cursor.rowcount

                reset_delete_state()

                if deleted_rows == 1:
                    st.session_state["last_deleted_patient"] = patient_name
                    st.rerun()
                else:
                    st.error(
                        "De patiënt is niet gevonden in de database. "
                    )

            except sqlite3.Error as error:
                st.error(f"Verwijderen is mislukt: {error}")

    with col2:
        if st.button("Nee, annuleren", use_container_width=True):
            reset_delete_state()
            st.rerun()


# 7. Start het verwijderproces

if st.button(
    "Patiënt verwijderen",
    type="primary",
    use_container_width=True,
):
    st.session_state.delete_patient_id = selected_id
    st.session_state.delete_patient_name = selected_name
    st.session_state.delete_deceased = None

    deceased_dialog(selected_id, selected_name)


# Toon de tweede dialoog pas nadat de eerste vraag is beantwoord.
pending_id = st.session_state.delete_patient_id
pending_name = st.session_state.delete_patient_name
deceased = st.session_state.delete_deceased

if pending_id is not None and deceased is not None:
    # In deze demo verandert het antwoord niets aan de verwijderactie.
    final_delete_dialog(pending_id, pending_name)


# 8. Resultaat

if "last_deleted_patient" in st.session_state:
    deleted_name = st.session_state.pop("last_deleted_patient")
    st.success(f"Patiënt '{deleted_name}' is definitief verwijderd.")


# 9. Navigatie

st.divider()

if st.button("Terug naar patiëntenoverzicht"):
    st.switch_page("Home.py")
