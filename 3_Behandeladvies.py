
import sqlite3
from contextlib import closing
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Behandeladvies | Longkanker CDSS",
    page_icon="🫁",
    layout="wide",
)

if st.button(
    "Terug naar Homepagina",
    use_container_width=True,
):
    st.switch_page("Home.py")

DB_FILE = Path(__file__).resolve().parent.parent / "ehr.db"

# Load data

def load_patients():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, display_name, leeft, chemo, target, rt
            FROM patient
            ORDER BY display_name
            """
        ).fetchall()

    return {row["id"]: dict(row) for row in rows}


patients = load_patients()

if not patients:
    st.error("Er zijn geen patiënten gevonden in de database.")
    st.stop()

# Select patient

# Home.py kan de ID van de geselecteerde patiënt meegeven.
incoming_patient_id = st.session_state.pop(
    "treatment_patient_id", None
)

patient_ids = list(patients.keys())

default_index = None
if incoming_patient_id in patient_ids:
    default_index = patient_ids.index(incoming_patient_id)

st.title("Behandeladvies")
st.caption("Longkanker Clinical Decision Support Demo")

selected_patient_id = st.selectbox(
    "Selecteer een patiënt",
    options=patient_ids,
    index=default_index,
    format_func=lambda patient_id: (
        f'{patients[patient_id]["display_name"]} '
        f'(ID: {patient_id})'
    ),
    placeholder="Kies een patiënt...",
    key="treatment_patient_select",
)

if selected_patient_id is None:
    st.info("Selecteer een patiënt om het behandeladvies te bekijken.")
    st.stop()

patient = patients[selected_patient_id]

st.divider()

# Patientinfo

st.subheader("Patiëntgegevens")

st.subheader(f'Patiëntnaam: **{patient["display_name"]}**' )
col1, col2, col3, col4 = st.columns(4)

col1.metric("Leeftijd", f'{patient["leeft"]} jaar')
col2.metric("Chemotherapie", patient["chemo"])
col3.metric("Radiotherapie", patient["rt"])
col4.metric("Targettherapie", patient["target"])

therapy_labels = {
    0: "Nee",
    1: "Ja, alleen prechirurgisch",
    2: "Ja, alleen postchirurgisch",
    3: "Ja, pre en postchirurgisch",
    4: "Ja, geen chirurgie",
}

# Give information about labels
st.caption(
    "Behandelcodes: "
    + " | ".join(
        f"{code} = {label}"
        for code, label in therapy_labels.items()
    )
)

st.divider()

# Treatment options

st.subheader("Mogelijke behandelopties")

therapy_fields = [
    ("Chemotherapie", "chemo"),
    ("Targettherapie", "target"),
    ("Radiotherapie", "rt"),
]

for therapy_name, field in therapy_fields:
    value = patient[field]
    label = therapy_labels.get(value, f"Onbekende code ({value})")

    with st.container(border=True):
        st.markdown(f"**{therapy_name}**")
        st.write(f"Huidige registratie: {label}")

        if value == 0:
            st.info(
                f"{therapy_name} is niet als als toegediend aangegeven. "
                "\nDeze behandeling kan als mogelijke optie worden "
                "beoordeeld door het behandelteam."
            )
        else:
            st.error(
                f"{therapy_name} is als toegediend geregistreerd. "
                "\nMet deze reden wordt er niet aangeraden om opnieuw met deze behandeling te starten"
            )

st.caption(
    "LET OP! Op basis van de informatie in de database is niet zeker te zeggen of de behandeling is afgerond. "
    "Overleg het (her)behandelen van de patiënt met de behandelend arts."
)

st.divider()

# Check if surgery is an option according to medical guideline

st.subheader("Beoordeling van chirurgiemogelijkheden")

surgery_eligible_by_history = all(
    patient[field] in (0, 4)
    for field in ("chemo", "target", "rt")
)

if not surgery_eligible_by_history:
    st.warning(
        "Chirurgie wordt op basis van de patiëntkenmerken niet overwogen in deze demo, omdat er al eerdere chirurgie is geregistreerd."
    )
    st.stop()

st.info(
    "Op basis van de patiëntkenmerken en de richtlijn kan chirurgie verder worden overwogen."
)

age = patient["leeft"]

if age > 80:
    st.error(
        "Leeftijdswaarschuwing: boven de 80 jaar is er volgens de "
        "richtlijn een sterk verhoogd overlijdensrisico bij "
        "chirurgie. Dit vereist individuele beoordeling."
    )

elif age > 70:
    st.warning(
        "Leeftijdswaarschuwing: boven de 70 jaar is er volgens de "
        "richtlijn een verhoogd overlijdensrisico bij chirurgie."
    )

# Extra informaton requirements for patients younger than 70 years of age

if age <= 70:
    st.subheader("Longfunctie en inspanningsvermogen")

    st.write(
        "Vul de aanvullende metingen in. Deze gegevens kunnen niet direct uit de database worden opgehaald."
    )

    col1, col2 = st.columns(2)

    with col1:
        fev1 = st.number_input(
            "FEV1 (% voorspeld)",
            min_value=0.0,
            max_value=200.0,
            value=None,
            step=1.0,
            placeholder="Percentage invoeren",
            help="FEV1 als percentage van de voorspelde waarde.",
        )

        tlco = st.number_input(
            "TLCO (% voorspeld)",
            min_value=0.0,
            max_value=200.0,
            value=None,
            step=1.0,
            placeholder="Percentage invoeren",
            help="Gebruik TLCO",
        )

        unexpected_dyspnea = st.checkbox(
            "Onverwachte dyspnoe d'effort aanwezig"
        )

    with col2:
        vo2_lobectomy = st.number_input(
            "VO2max lobectomie (ml/kg/min)",
            min_value=0.0,
            value=None,
            step=0.1,
            placeholder="Waarde invoeren",
        )

        vo2_pneumonectomy = st.number_input(
            "VO2max pneumonectomie (ml/kg/min)",
            min_value=0.0,
            value=None,
            step=0.1,
            placeholder="Waarde invoeren",
        )

        vo2_postoperative = st.number_input(
            "VO2max postoperatief (ml/kg/min)",
            min_value=0.0,
            value=None,
            step=0.1,
            placeholder="Waarde invoeren",
        )

    st.divider()
    st.subheader("Indicatieve chirurgische risicoclassificatie")

    all_values_entered = all(
        value is not None
        for value in (
            fev1,
            tlco,
            vo2_lobectomy,
            vo2_pneumonectomy,
            vo2_postoperative,
        )
    )

    if not all_values_entered:
        st.info(
            "Vul alle gevraagde meetwaarden in om door te gaan"
        )
    else:
        risk = None
        explanation = None

        # Regels worden in de opgegeven volgorde toegepast.
        if (
            fev1 > 80
            and tlco > 80
            and not unexpected_dyspnea
        ):
            risk = "Normaal risico"
            explanation = (
                "FEV1 en TLCO zijn beide hoger dan 80% en er is "
                "geen onverwachte dyspnoe d'effort."
            )

        elif (
            fev1 > 40
            and tlco > 40
            and not unexpected_dyspnea
        ):
            risk = "Normaal risico"
            explanation = (
                "FEV1 en TLCO zijn beide hoger dan 40% en er is "
                "geen onverwachte dyspnoe d'effort."
            )

        elif fev1 > 40 and tlco > 40:
            risk = "Verhoogd risico"
            explanation = (
                "FEV1 en TLCO zijn beide hoger dan 40%, maar er is "
                "wel onverwachte dyspnoe d'effort."
            )

        elif (
            vo2_lobectomy > 15
            and vo2_pneumonectomy > 20
        ):
            risk = "Normaal risico"
            explanation = (
                "VO2max is hoger dan 15 bij lobectomie en hoger "
                "dan 20 bij pneumonectomie."
            )

        elif vo2_postoperative > 10:
            risk = "Matig verhoogd risico"
            explanation = (
                "VO2max postoperatief is hoger dan 10 ml/kg/min."
            )

        else:
            risk = "Sterk verhoogd risico"
            explanation = (
                "VO2max postoperatief is niet hoger dan "
                "10 ml/kg/min."
            )

        st.markdown(f"### {risk}")
        st.write(explanation)

        st.caption(
            "Deze classificatie is opgesteld op basis van de gebruikersinvoer en de richtlijn met betrekking tot (in)operabiliteit bij NSCLC-patiënten"
        )

else:
    st.write(
        "Deze demo kan de chirurgierisico's voor deze patiënt niet berekenen."
    )

