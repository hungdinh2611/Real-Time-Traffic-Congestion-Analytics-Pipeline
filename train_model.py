import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib

# ─── 1) Load all Bronze Parquet files ───────────────────────────
folder = Path('data/bronze_py')
files = list(folder.glob('*.parquet'))
print(f"Found {len(files)} parquet files.")
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

# ─── 2) Basic cleaning & timestamp feature ─────────────────────
# Convert UNIX seconds to real datetime
df['dt'] = pd.to_datetime(df['timestamp'], unit='s')

# Sort by sensor & time so lag features make sense
df = df.sort_values(['sensor', 'dt'])

# ─── 3) Feature engineering ─────────────────────────────────────
# Rolling average of last 3 readings per sensor
df['speed_mean_3'] = (
    df.groupby('sensor')['speed']
      .rolling(window=3, min_periods=1)
      .mean()
      .reset_index(0, drop=True)
)

# Speed of the previous reading
df['speed_lag1'] = df.groupby('sensor')['speed'].shift(1)

# Target = next reading’s speed
df['speed_next'] = df.groupby('sensor')['speed'].shift(-1)

# Drop rows with any missing values now
df = df.dropna()

# One-hot encode the sensor ID (roadA, roadB, etc.)
df = pd.get_dummies(df, columns=['sensor'])

# ─── 4) Prepare training & test sets ───────────────────────────
# Feature columns start with 'speed_' or 'sensor_'
feature_cols = [
    "speed_mean_3",
    "speed_lag1",
] + [c for c in df.columns if c.startswith("sensor_")]
X = df[feature_cols]
y = df["speed_next"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Training on {len(X_train)} rows, testing on {len(X_test)} rows.")

# ─── 5) Train a simple Random Forest ───────────────────────────
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ─── 6) Evaluate ───────────────────────────────────────────────
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
print(f"Mean Absolute Error on test set: {mae:.2f}")

# ─── 7) Save the model ─────────────────────────────────────────
model_path = 'model.joblib'
joblib.dump(model, model_path)
print(f"Saved trained model to {model_path}")
