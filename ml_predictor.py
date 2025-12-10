# ml_predictor.py
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from collections import deque

class EnergyPredictor:
    def __init__(self, window_size=50):
        # Features: [Time_of_Day, Total_Load, Load_Trend]
        self.history_x = deque(maxlen=window_size) 
        self.history_y = deque(maxlen=window_size)
        
        # A lightweight model (Random Forest) is robust against noise
        self.model = RandomForestRegressor(n_estimators=20, max_depth=8)
        self.is_ready = False
        self.last_load = 0 # To calculate trend

    def add_data(self, time_step, total_load, actual_power):
        # Calculate Trend (Are we filling up or draining?)
        trend = total_load - self.last_load
        self.last_load = total_load

        # Feed the 3 features: Time, How Full We Are, and Speed of Change
        self.history_x.append([time_step, total_load, trend]) 
        self.history_y.append(actual_power)

        # Quick start (train after 5 ticks)
        if len(self.history_x) >= 5:
            self.train_model()
            self.is_ready = True

    def train_model(self):
        try:
            X = np.array(self.history_x)
            y = np.array(self.history_y)
            self.model.fit(X, y)
        except: pass

    def predict_next(self, next_time_step, current_total_load):
        if not self.is_ready:
            return 0.0
        
        # Assume the 'Trend' stays roughly the same for the next split second
        # This is a 'Naive Trend' assumption, which works well for short-term (t+1)
        current_trend = current_total_load - self.last_load
        estimated_future_load = current_total_load + current_trend

        features = [[next_time_step, estimated_future_load, current_trend]]
        
        try:
            prediction = self.model.predict(features)
            return prediction[0]
        except:
            return 0.0

    def check_anomaly(self, actual_power, predicted_power):
        if predicted_power == 0: return False
        diff = abs(actual_power - predicted_power)
        # 10% tolerance (Very strict because our new model is accurate)
        threshold = predicted_power * 0.10 
        return diff > threshold