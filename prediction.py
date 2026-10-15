"""Everything to do with the model: loading it and making a prediction.

You can test this file on its own, without the web app:
    python prediction.py
"""
from pathlib import Path

import numpy as np

MODEL_FILE = Path(__file__).parent / "model.keras"

# The model expects its 8 inputs in exactly this order (the column order of
# the training data). These are also the column names in the database.
FEATURES = [
    'Leeftijd',
    'Geslacht',
    'Vitale_status_interval',
    'Tumorsoort',
    'Diagnose_basis',
    'Morfologie',
    'Gedrag',
    'Differentiatiegraad',
    'Stadium',
    'Chemotherapie',
    'Targettherapie',
    'Radiotherapie',
    'SCLC'
]


def load_model():
    """Load your trained model from model.keras."""
    import keras  # imported here so the rest of this file works without TensorFlow

    return keras.models.load_model(str(MODEL_FILE), compile=False)


def preprocess(x):
    """Transform the raw input values the same way as during training.

    x is an array with one row of raw values (in FEATURES order) per patient.
    By default nothing happens. If your model was trained on transformed inputs
    (scaled, encoded, ...) and that step is NOT inside the model itself, do it here.
    Everything in this app goes through this function, so the app and your
    checks always see the same inputs.
    """
    return x


def make_input(patient, stadium=None):
    """Turn a patient (a dict with the FEATURES as keys) into the model's input.

    If Stadium is given, it replaces the patient's stored value
    for this prediction only (nothing is written to the database).
    """
    values = dict(patient)
    if stadium is not None:
        values["Stadium"] = stadium
    name = values.get("display_name", "this patient")
    for feature in FEATURES:
        if feature not in values:
            raise ValueError(f"No value called '{feature}' for {name}. "
                             "Do FEATURES and the database columns have the same names?")
        if values[feature] is None:
            raise ValueError(f"{name} has no value for '{feature}' (it is empty in the database). "
                             "The model needs a number for every input.")
    raw = np.array([[float(values[feature]) for feature in FEATURES]])
    return preprocess(raw)


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


def get_prediction(model, patient, stadium=None):
    """Return the model's output for one patient: a number between 0 and 1."""
    x = make_input(patient, stadium)
    return float(model.predict(x, verbose=0)[0, 0])


if __name__ == "__main__":
    # Checkpoint: the five patients from database.sql.
    examples = [dict(zip(FEATURES, values)) for values in [
        [53, 1, 586, 302310, 7, 8073, 2, 2, 6, 1, 0, 0, 0],   # Patient 1
        [24, 1, 1012, 302310, 2, 8243, 3, 1, 4, 2, 1, 0, 0],
        [44, 2, 230, 302310, 7, 8243, 3, 2, 7, 2, 2, 0, 1],
        [29, 2, 724, 302310, 7, 8250, 3, 1, 9, 0, 0, 2, 0]
    ]]
    model = load_model()
    problem = check_model(model, np.vstack([make_input(p) for p in examples]))
    if problem:
        raise SystemExit("Problem with model.keras: " + problem)
    susan = examples[0]
    print("Model input: ", make_input(susan))
    print("Prediction:  ", round(get_prediction(model, susan), 3))
    print("With Stadium = 5:", round(get_prediction(model, susan, stadium=5), 3))
