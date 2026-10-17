"""Everything to do with the model: loading it and making a prediction.

You can test this file on its own, without the web app:
    python prediction.py
"""
from pathlib import Path

import numpy as np
import joblib
import pandas as pd

MODEL_FILE = Path(__file__).parent / "model.keras"
PREPROCESSOR_FILE = Path(__file__).parent / "nsclc_preprocessor.joblib"

# The model expects its 8 inputs in exactly this order (the column order of
# the training data). These are also the column names in the database.
FEATURES = [
    'leeft',
    'gesl',
    'tumsoort',
    'diag_basis',
    'morf',
    'gedrag',
    'diffgrad',
    'stadium',
    'chemo',
    'target',
    'rt',
    'SCLC'
]


def load_model():
    """Load your trained model from model.keras."""
    import keras  # imported here so the rest of this file works without TensorFlow

    return keras.models.load_model(str(MODEL_FILE), compile=False)

def load_preprocessor():
    return joblib.load(PREPROCESSOR_FILE)

preprocessor = load_preprocessor()

def preprocess(x, preprocessor=preprocessor):
    """Apply the same transformations used during training."""
    df = pd.DataFrame(x, columns=FEATURES)
    return preprocessor.transform(df)


def make_input(patient, preprocessor=preprocessor, stadium=None):
    """Turn a patient (a dict with the FEATURES as keys) into the model's input.

    If Stadium is given, it replaces the patient's stored value
    for this prediction only (nothing is written to the database).
    """
    values = dict(patient)
    if stadium is not None:
        values["stadium"] = stadium
    name = values.get("display_name", "this patient")
    for feature in FEATURES:
        if feature not in values:
            raise ValueError(f"No value called '{feature}' for {name}. "
                             "Do FEATURES and the database columns have the same names?")
        if values[feature] is None:
            raise ValueError(f"{name} has no value for '{feature}' (it is empty in the database). "
                             "The model needs a number for every input.")
    raw = np.array([[float(values[feature]) for feature in FEATURES]])
    return preprocess(raw, preprocessor)


def check_model(model, X):
    """Check that the model fits this app. Returns a problem description, or None if OK.

    X holds example inputs made with make_input, one row per patient.
    """
    try:
        out = np.asarray(model.predict(X, verbose=0))
    except Exception as error:
        n = len(FEATURES)
        return (f"The model could not make a prediction from {n} input values. "
                f"Does it expect exactly {n} inputs, one for each name in FEATURES? (Error: {error})")
    if out.shape != (len(X), 1):
        return (f"The model should return one number per patient, i.e. an output of shape "
                f"({len(X)}, 1) for {len(X)} patients, but it returned shape {out.shape}.")
    if not np.all((out >= 0) & (out <= 1)):
        return ("The model returned values outside the range 0 to 1, "
                "so its output cannot be read as a probability.")
    return None


def get_prediction(model, patient, preprocessor=preprocessor, stadium=None):
    x = make_input(patient, preprocessor, stadium)
    return float(model.predict(x, verbose=0)[0, 0])


if __name__ == "__main__":
    # Checkpoint: the five patients from database.sql.
    examples = [dict(zip(FEATURES, values)) for values in [
        [53, 1, 302310, 7, 8073, 2, 2, 6, 1, 0, 0, 0],   # Patient 1
        [24, 1, 302310, 2, 8243, 3, 1, 4, 2, 1, 0, 0],
        [44, 2, 302310, 7, 8243, 3, 2, 7, 2, 2, 0, 1],
        [29, 2, 302310, 7, 8250, 3, 1, 9, 0, 0, 2, 0]
    ]]
    model = load_model()
    problem = check_model(model, np.vstack([make_input(p, preprocessor) for p in examples]))
    if problem:
        raise SystemExit("Problem with model.keras: " + problem)
    susan = examples[0]
    print("Model input: ", make_input(susan, preprocessor))
    print("Prediction:  ", round(get_prediction(model, susan, preprocessor), 3))
    print("With Stadium = 5:", round(get_prediction(model, susan, preprocessor, stadium=5), 3))
