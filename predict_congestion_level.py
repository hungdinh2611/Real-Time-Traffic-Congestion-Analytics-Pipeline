import xgboost as xgb

loaded_model = xgb.Booster()

loaded_model.load_model("xgb_model.json")

import pandas as pd
import numpy as np

feature_columns = [
    'median', 'mean', 'std', 'weekday', 'is_weekend', 'is_night', 
    'hour_sin', 'hour_cos', 'min_sin', 'min_cos', 
    'sensor_roadA', 'sensor_roadB', 'sensor_roadC'
]

def predict_cong_level(sensor, speed, timestamp):
    
    ts = pd.to_datetime(timestamp, unit='s')
    
    hour = ts.hour
    minute = ts.minute
    weekday = ts.weekday() 
    
    is_weekend = 1 if weekday >= 5 else 0
    is_night = 1 if (hour >= 22 or hour <= 5) else 0
    
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)
    min_sin = np.sin(2 * np.pi * minute / 60)
    min_cos = np.cos(2 * np.pi * minute / 60)
    
    sensor_roadA = 1 if sensor == 'roadA' else 0
    sensor_roadB = 1 if sensor == 'roadB' else 0
    sensor_roadC = 1 if sensor == 'roadC' else 0

    current_stats = {
        'median': speed, 
        'mean': speed, 
        'std': speed,
        'weekday': weekday,       
        'is_weekend': is_weekend, 
        'is_night': is_night,
        'hour_sin': hour_sin, 
        'hour_cos': hour_cos,
        'min_sin': min_sin,  
        'min_cos': min_cos,
        'sensor_roadA': sensor_roadA,  
        'sensor_roadB': sensor_roadB,
        'sensor_roadC': sensor_roadC
    }

    new_data = pd.DataFrame([current_stats])[feature_columns]

    dnew = xgb.DMatrix(new_data)

    prediction = loaded_model.predict(dnew)
    return int(np.round(prediction[0]))