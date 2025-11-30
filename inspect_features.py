import joblib

model = joblib.load("model.joblib")
print("FEATURES:", list(model.feature_names_in_))
