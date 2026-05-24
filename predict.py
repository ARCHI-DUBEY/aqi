import joblib
import numpy as np

model = joblib.load("aqi_model.pkl")

# ── US EPA PM2.5 → AQI breakpoints (used as a sanity anchor) ─
def _pm25_to_aqi(pm):
    breakpoints = [
        (0,    12.0,   0,   50),
        (12.1, 35.4,  51,  100),
        (35.5, 55.4, 101,  150),
        (55.5, 150.4,151,  200),
        (150.5,250.4,201,  300),
        (250.5,500.4,301,  500),
    ]
    for lo, hi, alo, ahi in breakpoints:
        if pm <= hi:
            return ((ahi - alo) / (hi - lo)) * (pm - lo) + alo
    return 500


def predict_aqi(pm25, pm10, no2, temp, humidity):
    """
    Predict AQI using the trained Random Forest model.
    Result is blended with the EPA PM2.5 formula (80/20 split)
    so that even if the model drifts, PM2.5 — the dominant
    pollutant — keeps the output grounded.
    """
    features = np.array([[pm25, pm10, no2, temp, humidity]])

    ml_pred  = model.predict(features)[0]
    epa_pred = _pm25_to_aqi(pm25)

    # 80% ML model, 20% EPA formula anchor
    blended = 0.80 * ml_pred + 0.20 * epa_pred

    return round(float(np.clip(blended, 0, 500)), 2)