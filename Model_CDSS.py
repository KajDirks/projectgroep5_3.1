from narwhals import Int64
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    average_precision_score,
    roc_auc_score,
    recall_score,
    f1_score
)
import tensorflow as tf
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping

# Read data
df = pd.read_csv('iknl_long_syntheticdata.csv', sep=';')

# Trim column names to remove leading/trailing whitespace
df.columns = df.columns.str.strip()

# Take only important columns for prediction
FEATURES = [
    'leeft',
    'gesl',
    'vit_stat',
    'vit_stat_int',
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
df = df[FEATURES]

# Only use patients with Non Small Cell Lung Cancer (tumsoort = 302310)
nsclc = df.loc[df["tumsoort"] == 302310].copy()

# Check if tumsoort contains only 302310
print(nsclc['tumsoort'].unique())

# Create target variable
nsclc['target_value'] = pd.Series(
    pd.NA,
    index = nsclc.index,
    dtype = "Int64"
)

# Check target column
print(nsclc['target_value'].unique())

# Died within 5 years (1826 days) = 1
nsclc.loc[
    (nsclc["vit_stat"] == 0) &
    (nsclc["vit_stat_int"] <= 1826),
    "target_value"
] = 1

# Didn't die
nsclc.loc[
    (nsclc['vit_stat'] == 1),
    'target_value'
] = 0

# Died, but after longer than 5 years = 0
nsclc.loc[
    (nsclc['vit_stat'] == 0) &
    (nsclc['vit_stat_int'] > 1826),
    'target_value'
] = 0

# Check new values
print('Unique values in target_value: \n')
print(nsclc['target_value'].unique())
print(nsclc.describe())

# Set target
y = nsclc['target_value'].astype(int)

# Set feature types
# Numeric features
num_feat = ['leeft']

# Categorical features
cat_feat = [
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

# Set X data
X = nsclc[num_feat + cat_feat].copy()

# Split Train/Test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# Numeric transformer: impute missing values and scale
numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]
)

# Categorical transformer: impute missing values and encode
categorical_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, num_feat),
        ("cat", categorical_transformer, cat_feat),
    ]
)

# Preprocess the train and test data explicitly before passing to Keras
X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# --- KERAS MODEL ---
model = Sequential(
    [
        Dense(
            32, activation="relu", input_shape=(X_train_processed.shape[1],)
        ),
        Dense(16, activation="relu"),
        Dense(
            1, activation="sigmoid"
        ),  # 1 output node with sigmoid for binary classification
    ]
)

# Compile the model
model.compile(
    optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
)

# Early stopping
early_stopping = EarlyStopping(
    monitor="val_loss", patience=5, restore_best_weights=True
)

# Train the model
history = model.fit(
    X_train_processed,
    y_train,
    epochs=200,
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stopping],
    verbose=1,
)

# Save the trained model as a .keras file for your assignment
model.save("nsclc_mlp_model.keras")

# --- EVALUATION ---
# model.predict returns probabilities; flatten array to 1D
y_prob = model.predict(X_test_processed).ravel()
# Convert probabilities to binary predictions (threshold = 0.5)
y_pred = (y_prob >= 0.5).astype(int)

print("Verdeling testset:")
print(y_test.value_counts().sort_index())

print("\nConfusion matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassificatierapport:")
print(
    classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=[
            "Geen overlijden binnen 5 jaar",
            "Overlijden binnen 5 jaar",
        ],
        zero_division=0,
    )
)

print("ROC-AUC:", round(roc_auc_score(y_test, y_prob), 4))
print("Average precision:", round(average_precision_score(y_test, y_prob), 4))

model.save("model.keras")
