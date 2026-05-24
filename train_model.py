import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

np.random.seed(42)
n = 1000

# ── Realistic pollutant ranges ──────────────────────────────
pm25     = np.random.uniform(5, 300, n)
pm10     = pm25 * np.random.uniform(1.3, 2.0, n)
no2      = np.random.uniform(5, 150, n)
temp     = np.random.uniform(10, 45, n)
humidity = np.random.uniform(20, 95, n)

# ── US EPA PM2.5 → AQI breakpoint formula ───────────────────
def pm25_to_aqi(pm):
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

aqi = np.array([pm25_to_aqi(p) for p in pm25])

# ── Add realistic influence from other pollutants ────────────
# NO2 contributes especially at high concentrations
aqi += np.where(no2 > 80,  (no2 - 80) * 0.3,  no2 * 0.08)
# High humidity traps particulates
aqi += np.where(humidity > 70, (humidity - 70) * 0.4, 0)
# High temp accelerates ozone/NO2 reactions
aqi += np.where(temp > 35, (temp - 35) * 0.5, 0)
# Small random noise to simulate real-world variance
aqi += np.random.normal(0, 4, n)
aqi  = np.clip(aqi, 0, 500)

# ── Build DataFrame ──────────────────────────────────────────
df = pd.DataFrame({
    "pm25":     pm25,
    "pm10":     pm10,
    "no2":      no2,
    "temp":     temp,
    "humidity": humidity,
    "aqi":      aqi
})

X = df[["pm25", "pm10", "no2", "temp", "humidity"]]
y = df["aqi"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── Train model ───────────────────────────────────────────────
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=12,
    min_samples_split=4,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────
preds = model.predict(X_test)
mae   = mean_absolute_error(y_test, preds)
r2    = r2_score(y_test, preds)
print(f"MAE  : {mae:.2f} AQI points")
print(f"R²   : {r2:.4f}")

# ── Save ──────────────────────────────────────────────────────
joblib.dump(model, "aqi_model.pkl")
print("Model trained and saved → aqi_model.pkl")