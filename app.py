"""A toy clinical decision support app.

Run:  streamlit run app.py

How Streamlit works, in one sentence: every time the user clicks or types
something, Streamlit runs this whole script again from top to bottom and
redraws the page. Things that must survive between runs (like a value the
user typed) are kept in st.session_state.

This is a technical demo. It is NOT meant to be used for clinical decisions.
"""
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
import streamlit as st

import prediction

DB_FILE = Path(__file__).parent / "ehr.db"

st.set_page_config(page_title="Longkanker CDSS Demo", page_icon="🫁", layout="wide")
st.title("Longkanker Clinical Decision Support Demo")
st.caption("Technische demo, niet bedoeld voor echte klinische beslissingen.")

# --- 1. Check that the files we need are there ------------------------------
if not DB_FILE.exists():
    st.error("ehr.db not found. Run `python setup_database.py` first (see the README).")
    st.stop()
if not prediction.MODEL_FILE.exists():
    st.error("model.keras not found. Train your model and save it as model.keras "
             "in the same folder as app.py (see the README).")
    st.stop()


# --- 2. Load the model (once) and the patients (on every run) ---------------
@st.cache_resource(max_entries=1)  # load the model only once, not on every click...
def get_model(file_modified_time):  # ...but again whenever model.keras is replaced
    return prediction.load_model()


def load_patients():
    """Read all patients from the database, as {id: {column: value}}."""
    with closing(sqlite3.connect(DB_FILE)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM patient ORDER BY id").fetchall()
    return {row["id"]: dict(row) for row in rows}


patients = load_patients()
if not patients:
    st.warning("The database has no patients. Check database.sql and run setup_database.py.")
    st.stop()

try:
    model = get_model(prediction.MODEL_FILE.stat().st_mtime)
except ImportError as error:
    st.error("TensorFlow is not installed in the Python environment that runs this app. "
             "Activate your virtual environment and run `pip install -r requirements.txt`. "
             f"(Error: {error})")
    st.stop()
except Exception as error:
    st.error("model.keras exists but could not be loaded. Was it saved with "
             "`model.save('model.keras')`, using the same TensorFlow version as in "
             f"requirements.txt? See Troubleshooting in the README. (Error: {error})")
    st.stop()

try:
    all_inputs = np.vstack([prediction.make_input(p) for p in patients.values()])
except ValueError as error:
    st.error(f"Problem with the patient data: {error}")
    st.stop()

problem = prediction.check_model(model, all_inputs)
if problem:
    st.error("Your model does not fit this app yet. " + problem)
    st.stop()

# The blood pressure typed in by the user. None = use the value from the database.
st.session_state.setdefault("userstage", None)


def forget_userstage():
    st.session_state.userstage = None


# --- 3. The page -------------------------------------------------------------
st.subheader("Patients")
patient_id = st.radio(
    "Select a patient",
    options=list(patients),
    format_func=lambda pid: patients[pid]["display_name"],
    on_change=forget_userstage,  # a new patient starts without a typed-in value
)
current_patient = patients[patient_id]

results = st.container()  # filled in below, but shown here, above the form

with st.form("stage_form", clear_on_submit=True):
    new_stage = st.number_input(
        "If desired, enter a new stage value (1-8) here",
        min_value=1, max_value=8, value=None, step=1,
        help="Leave empty and press Submit to go back to the value in the database.",
    )
    if st.form_submit_button("Submit"):
        st.session_state.userstage = new_stage  # used for this prediction only, not saved

with results:
    userstage = st.session_state.userstage
    p = prediction.get_prediction(model, current_patient, userstage)

    st.markdown(f"**Current patient:** {current_patient['display_name']}")
    st.markdown(f"**User-entered stage:** {userstage if userstage is not None else 'none'}")
    st.metric("Prediction", f"{p:.2f}")
    st.caption("The model's output, between 0 and 1. Higher means the model thinks "
               "diabetes is more likely. It is not a calibrated risk.")

    with st.expander("What the model receives"):
        x = prediction.make_input(current_patient, userstage)[0]
        st.table({"input": prediction.FEATURES, "value": [float(v) for v in x]})
