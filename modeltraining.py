import pandas as pd
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score

url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"

# Define the features and target variable
FEATURES = [
    "pregnancies",
    "glucose",
    "blood_pressure",
    "skin_thickness",
    "insulin",
    "bmi",
    "diabetes_pedigree_function",
    "age",
]

data = pd.read_csv(url, header=None, names=FEATURES + ["outcome"])

# Split the data into features and target variable
X = data[FEATURES].values.astype("float32")
y = data["outcome"].values.astype("float32")

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# 4. Normalize inputs INSIDE the model
normalizer = tf.keras.layers.Normalization(axis=-1)
normalizer.adapt(X_train)

# 5. Build the neural network
model = tf.keras.Sequential([
    tf.keras.Input(shape=(8,)),
    normalizer,
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(8, activation="relu"),
    tf.keras.layers.Dense(1, activation="sigmoid"),
])

# 6. Configure training
model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        tf.keras.metrics.AUC(name="auc"),
    ],
)

# 7. Train the model
early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=15,
    restore_best_weights=True,
)

model.fit(
    X_train,
    y_train,
    epochs=200,
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stopping],
    verbose=1,
)

# 8. Evaluate on data not used for training
probabilities = model.predict(X_test, verbose=0).ravel()
predictions = (probabilities >= 0.5).astype(int)

print("Test accuracy:", accuracy_score(y_test, predictions))
print("Test ROC AUC:", roc_auc_score(y_test, probabilities))

# 9. Save the model, including its normalization layer
model.save("model.keras")
print("Saved model.keras")