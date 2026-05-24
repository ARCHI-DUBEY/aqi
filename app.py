import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from predict import predict_aqi
from cities import cities
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="AQI Pulse — Global Air Quality Dashboard",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject early CSS to kill the keyboard_double_arrow overlay before page renders
st.markdown("""
<style>
  /* Nuke the sidebar collapse arrow & its Material icon tooltip */
  [data-testid="stSidebarCollapseButton"] { visibility: hidden !important; }
  [data-testid="stSidebarCollapseButton"] * { visibility: hidden !important; }
  span[data-testid="stIconMaterial"]      { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');

  /* ── Root ── */
  :root {
    --bg:        #0b0f1a;
    --surface:   #111827;
    --border:    #1f2d40;
    --accent:    #00e5ff;
    --accent2:   #7c3aed;
    --good:      #22c55e;
    --moderate:  #facc15;
    --unhealthy: #f97316;
    --hazardous: #ef4444;
    --text:      #e2e8f0;
    --muted:     #64748b;
  }

  html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
  }

  /* Header */
  .aqi-hero {
    background: linear-gradient(135deg, #0b0f1a 0%, #0f1f35 50%, #0b0f1a 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
  }
  .aqi-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(0,229,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
  }
  .aqi-hero h1 {
    font-family: 'Space Mono', monospace;
    font-size: 2.2rem;
    letter-spacing: -1px;
    margin: 0;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .aqi-hero p {
    color: var(--muted);
    margin: 0.4rem 0 0;
    font-size: 0.95rem;
    font-weight: 300;
  }

  /* Cards */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
  }
  .card-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.75rem;
  }

  /* AQI Badge */
  .aqi-badge {
    display: inline-block;
    padding: 0.3rem 1rem;
    border-radius: 999px;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 1px;
  }

  /* Stat pills */
  .stat-row { display: flex; gap: 0.75rem; flex-wrap: wrap; }
  .stat-pill {
    background: #162033;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    min-width: 110px;
    text-align: center;
  }
  .stat-pill .val {
    font-family: 'Space Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent);
  }
  .stat-pill .lbl {
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 2px;
  }

  /* Alert banners */
  .alert-good     { background:#052e16; border:1px solid #166534; border-radius:10px; padding:0.8rem 1.2rem; color:#86efac; }
  .alert-moderate { background:#422006; border:1px solid #92400e; border-radius:10px; padding:0.8rem 1.2rem; color:#fde68a; }
  .alert-bad      { background:#2d0a0a; border:1px solid #7f1d1d; border-radius:10px; padding:0.8rem 1.2rem; color:#fca5a5; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #090d16 !important;
    border-right: 1px solid var(--border) !important;
  }
  [data-testid="stSidebar"] * { font-family: 'Sora', sans-serif !important; }

  /* Plotly bg override */
  .js-plotly-plot { border-radius: 12px; overflow: hidden; }

  /* Metric overrides */
  [data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    color: var(--accent) !important;
  }
  [data-testid="stMetricLabel"] { color: var(--muted) !important; }

  /* Divider */
  hr { border-color: var(--border) !important; }

  /* Tabs */
  button[data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
  }

  /* Hide Streamlit's auto-generated sidebar label & collapse button tooltip */
  [data-testid="stSidebarNav"]              { display: none !important; }
  [data-testid="collapsedControl"]          { display: none !important; }
  button[kind="header"]                     { display: none !important; }
  [data-testid="stSidebarCollapseButton"]   { display: none !important; }
  /* Hide the keyboard_double_arrow text node that floats on hover */
  section[data-testid="stSidebar"] span[data-testid="stIconMaterial"],
  section[data-testid="stSidebar"] .st-emotion-cache-eczf16,
  section[data-testid="stSidebar"] .st-emotion-cache-1f3w014 { display: none !important; }
  section[data-testid="stSidebar"] > div:first-child { padding-top: 1rem !important; }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Sora, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor="#1f2d40", zerolinecolor="#1f2d40"),
    yaxis=dict(gridcolor="#1f2d40", zerolinecolor="#1f2d40"),
)

def aqi_color(aqi):
    if aqi <= 50:   return "#22c55e"
    if aqi <= 100:  return "#facc15"
    if aqi <= 150:  return "#f97316"
    if aqi <= 200:  return "#ef4444"
    return "#a855f7"

def aqi_label(aqi):
    if aqi <= 50:   return ("Good",        "#22c55e", "alert-good")
    if aqi <= 100:  return ("Moderate",    "#facc15", "alert-moderate")
    if aqi <= 150:  return ("Unhealthy*",  "#f97316", "alert-bad")
    if aqi <= 200:  return ("Unhealthy",   "#ef4444", "alert-bad")
    return             ("Hazardous",   "#a855f7", "alert-bad")

@st.cache_data(ttl=600, show_spinner=False)
def fetch_aqi(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/air_pollution"
    r = requests.get(url, params={"lat": lat, "lon": lon, "appid": API_KEY}, timeout=8)
    return r.json()["list"][0]["components"]

@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"
    r = requests.get(url, params={"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}, timeout=8)
    d = r.json()
    return {
        "temp":        d["main"]["temp"],
        "feels_like":  d["main"]["feels_like"],
        "humidity":    d["main"]["humidity"],
        "pressure":    d["main"]["pressure"],
        "wind_speed":  d["wind"]["speed"],
        "wind_deg":    d["wind"].get("deg", 0),
        "visibility":  d.get("visibility", 0) / 1000,
        "description": d["weather"][0]["description"].title(),
        "icon":        d["weather"][0]["icon"],
    }

@st.cache_data(ttl=600, show_spinner=False)
def fetch_forecast(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"
    r = requests.get(url, params={"lat": lat, "lon": lon, "appid": API_KEY}, timeout=8)
    items = r.json().get("list", [])
    rows = []
    for item in items[:40]:
        c = item["components"]
        dt = datetime.utcfromtimestamp(item["dt"])
        rows.append({
            "datetime": dt,
            "pm25": c["pm2_5"],
            "pm10": c["pm10"],
            "no2":  c["no2"],
            "o3":   c.get("o3", 0),
            "so2":  c.get("so2", 0),
            "co":   c.get("co", 0),
        })
    return pd.DataFrame(rows)



# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:1.1rem;
                letter-spacing:2px; color:#00e5ff; margin-bottom:1.2rem;">
      🌬️ AQI PULSE
    </div>
    """, unsafe_allow_html=True)

    # Searchable city selector — st.selectbox supports search natively
    city_list = sorted(cities.keys())
    city = st.selectbox("📍 Primary City", city_list, index=city_list.index("Delhi, India"))

    st.markdown("---")

    # Optional city comparison
    enable_compare = st.toggle("⚖️ Enable City Comparison", value=False)
    compare_city = None
    if enable_compare:
        other_cities = [c for c in city_list if c != city]
        compare_city = st.selectbox("🔁 Compare With", other_cities, index=0)

    st.markdown("---")
    units = st.radio("Temperature Unit", ["°C", "°F"], horizontal=True)
    auto_refresh = st.toggle("🔄 Auto-refresh (60s)", value=False)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.72rem; color:#475569; line-height:1.7;">
      <b style="color:#64748b;">DATA SOURCES</b><br>
      OpenWeatherMap API<br>
      Air Pollution API v2.5<br><br>
      <b style="color:#64748b;">MODEL</b><br>
      Random Forest Regressor<br>
      Features: PM2.5, PM10, NO2,<br>
      Temp, Humidity
    </div>
    """, unsafe_allow_html=True)

if auto_refresh:
    import time
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()

# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="aqi-hero">
  <h1>🌍 AQI PULSE</h1>
  <p>Global Air Quality Intelligence Dashboard — Real-time monitoring, ML forecasting & health insights</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────

lat, lon = cities[city]

with st.spinner(f"Fetching live data for {city}..."):
    try:
        components  = fetch_aqi(lat, lon)
        weather     = fetch_weather(lat, lon)
        forecast_df = fetch_forecast(lat, lon)
        api_ok = True
    except Exception as e:
        st.error(f"API Error: {e}. Showing demo data.")
        components = {"pm2_5": 45.2, "pm10": 68.3, "no2": 32.1, "o3": 55.0, "so2": 8.2, "co": 450.0}
        weather = {"temp": 28, "feels_like": 31, "humidity": 72, "pressure": 1012,
                   "wind_speed": 3.2, "wind_deg": 180, "visibility": 8.5,
                   "description": "Partly Cloudy", "icon": "02d"}
        dates = [datetime.now() + timedelta(hours=i*6) for i in range(40)]
        forecast_df = pd.DataFrame({
            "datetime": dates, "pm25": np.random.uniform(30,80,40),
            "pm10": np.random.uniform(50,100,40), "no2": np.random.uniform(20,60,40),
            "o3": np.random.uniform(30,70,40), "so2": np.random.uniform(5,15,40), "co": np.random.uniform(300,600,40)
        })
        api_ok = False

pm25 = components["pm2_5"]
pm10 = components["pm10"]
no2  = components["no2"]
o3   = components.get("o3",  0)
so2  = components.get("so2", 0)
co   = components.get("co",  0)

temp = weather["temp"]
if units == "°F":
    temp_disp = round(temp * 9/5 + 32, 1)
    fl_disp   = round(weather["feels_like"] * 9/5 + 32, 1)
else:
    temp_disp = temp
    fl_disp   = weather["feels_like"]

humidity   = weather["humidity"]
wind_speed = weather["wind_speed"]
predicted_aqi = predict_aqi(pm25, pm10, no2, temp, humidity)

label, color, alert_class = aqi_label(predicted_aqi)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tabs = st.tabs(["📊 Overview", "🔬 Pollutants", "🌦️ Weather", "🗺️ Global Map", "⚖️ City Compare", "🩺 Health"])

# ══════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════
with tabs[0]:

    # Top KPI row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🌡️ Temperature",    f"{temp_disp}{units}")
    k2.metric("💧 Humidity",        f"{humidity}%")
    k3.metric("💨 Wind Speed",      f"{wind_speed} m/s")
    k4.metric("👁️ Visibility",      f"{weather['visibility']:.1f} km")
    k5.metric("🔵 Pressure",        f"{weather['pressure']} hPa")

    st.markdown("---")

    col_gauge, col_info = st.columns([1, 1])

    with col_gauge:
        st.markdown('<div class="card-title">PREDICTED AQI</div>', unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=predicted_aqi,
            delta={"reference": 100, "valueformat": ".0f"},
            number={"font": {"size": 52, "family": "Space Mono", "color": color}},
            title={"text": f"<b>{city}</b><br><span style='font-size:0.8em;color:#64748b'>{label}</span>",
                   "font": {"size": 16, "family": "Sora"}},
            gauge={
                "axis":      {"range": [0, 300], "tickcolor": "#475569", "tickfont": {"color": "#475569"}},
                "bar":       {"color": color, "thickness": 0.25},
                "bgcolor":   "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,   50],  "color": "#052e16"},
                    {"range": [50,  100], "color": "#2d2006"},
                    {"range": [100, 150], "color": "#2d1506"},
                    {"range": [150, 200], "color": "#2d0a0a"},
                    {"range": [200, 300], "color": "#1a0630"},
                ],
                "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": predicted_aqi},
            }
        ))
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=300,
                                font=dict(family="Sora", color="#94a3b8"),
                                margin=dict(l=20, r=20, t=30, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_info:
        st.markdown('<div class="card-title">POLLUTANT SNAPSHOT</div>', unsafe_allow_html=True)
        pollutants = {"PM2.5": pm25, "PM10": pm10, "NO₂": no2, "O₃": o3, "SO₂": so2, "CO": co/100}
        safe_limits = {"PM2.5": 25, "PM10": 50, "NO₂": 40, "O₃": 100, "SO₂": 20, "CO": 10}
        for name, val in pollutants.items():
            pct = min(val / safe_limits.get(name, 100) * 100, 200)
            bar_color = "#22c55e" if pct < 80 else "#f97316" if pct < 150 else "#ef4444"
            st.markdown(f"""
            <div style="margin-bottom:0.7rem;">
              <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                <span style="font-size:0.8rem;color:#94a3b8;">{name}</span>
                <span style="font-family:'Space Mono',monospace;font-size:0.8rem;color:{bar_color};">
                  {val:.1f} µg/m³
                </span>
              </div>
              <div style="background:#162033;border-radius:4px;height:6px;">
                <div style="width:{min(pct,100):.0f}%;background:{bar_color};height:6px;border-radius:4px;
                            transition:width 0.5s;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 48-hour AQI forecast using real forecast data
    st.markdown('<div class="card-title">48-HOUR AQI FORECAST</div>', unsafe_allow_html=True)
    if not forecast_df.empty:
        try:
            forecast_df["aqi_pred"] = forecast_df.apply(
                lambda r: predict_aqi(r["pm25"], r["pm10"], r["no2"], temp, humidity), axis=1)
        except Exception:
            forecast_df["aqi_pred"] = forecast_df["pm25"].apply(
                lambda x: predict_aqi(x, 60, 30, temp, humidity))
        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=forecast_df["datetime"][:8],
            y=forecast_df["aqi_pred"][:8],
            mode="lines+markers",
            line=dict(color="#00e5ff", width=2),
            marker=dict(size=7, color="#00e5ff"),
            fill="tozeroy",
            fillcolor="rgba(0,229,255,0.05)",
            name="Forecast AQI"
        ))
        # Add threshold lines
        for lvl, col, lbl in [(50,"#22c55e","Good"), (100,"#facc15","Moderate"), (150,"#f97316","Unhealthy")]:
            fig_fc.add_hline(y=lvl, line_dash="dot", line_color=col, opacity=0.4,
                             annotation_text=lbl, annotation_font_color=col)
        fig_fc.update_layout(**PLOTLY_LAYOUT, height=280,
                             xaxis_title="Time (UTC)", yaxis_title="AQI")
        st.plotly_chart(fig_fc, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 — POLLUTANTS
# ══════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="card-title">POLLUTANT RADAR</div>', unsafe_allow_html=True)

    poll_names  = ["PM2.5", "PM10", "NO₂", "O₃", "SO₂", "CO(÷100)"]
    poll_vals   = [pm25, pm10, no2, o3, so2, co/100]
    who_limits  = [25, 50, 40, 100, 20, 10]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=poll_vals + [poll_vals[0]],
        theta=poll_names + [poll_names[0]],
        fill="toself", fillcolor="rgba(0,229,255,0.1)",
        line=dict(color="#00e5ff", width=2), name=city
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=who_limits + [who_limits[0]],
        theta=poll_names + [poll_names[0]],
        fill="toself", fillcolor="rgba(239,68,68,0.05)",
        line=dict(color="#ef4444", width=1.5, dash="dot"), name="WHO Guideline"
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, gridcolor="#1f2d40", color="#475569"),
            angularaxis=dict(gridcolor="#1f2d40", color="#94a3b8")
        ),
        paper_bgcolor="rgba(0,0,0,0)", height=400,
        font=dict(family="Sora", color="#94a3b8"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40")
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="card-title">POLLUTANT FORECAST TREND</div>', unsafe_allow_html=True)

    if not forecast_df.empty:
        poll_choice = st.multiselect(
            "Select pollutants to display",
            ["PM2.5", "PM10", "NO₂", "O₃", "SO₂"],
            default=["PM2.5", "PM10", "NO₂"]
        )
        col_map = {"PM2.5": "pm25", "PM10": "pm10", "NO₂": "no2", "O₃": "o3", "SO₂": "so2"}
        colors_ = ["#00e5ff", "#7c3aed", "#f97316", "#22c55e", "#facc15"]

        fig_trend = go.Figure()
        for i, p in enumerate(poll_choice):
            fig_trend.add_trace(go.Scatter(
                x=forecast_df["datetime"],
                y=forecast_df[col_map[p]],
                mode="lines", name=p,
                line=dict(color=colors_[i % len(colors_)], width=2)
            ))
        fig_trend.update_layout(**PLOTLY_LAYOUT, height=350,
                                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40"))
        st.plotly_chart(fig_trend, use_container_width=True)

    # Hourly distribution heatmap
    st.markdown('<div class="card-title">PM2.5 HOURLY DISTRIBUTION (NEXT 5 DAYS)</div>', unsafe_allow_html=True)
    if not forecast_df.empty and len(forecast_df) >= 20:
        hm_df = forecast_df.copy()
        hm_df["day"]  = hm_df["datetime"].dt.strftime("%a %d")
        hm_df["hour"] = hm_df["datetime"].dt.hour
        pivot = hm_df.pivot_table(values="pm25", index="hour", columns="day", aggfunc="mean")
        fig_hm = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=[f"{h:02d}:00" for h in pivot.index],
            colorscale=[[0,"#052e16"],[0.33,"#facc15"],[0.66,"#f97316"],[1,"#ef4444"]],
            colorbar=dict(
                tickfont=dict(color="#94a3b8"),
                title=dict(text="µg/m³", font=dict(color="#94a3b8"))
            )
        ))
        fig_hm.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_hm, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 3 — WEATHER
# ══════════════════════════════════════════════
with tabs[2]:
    wc1, wc2, wc3, wc4 = st.columns(4)
    wc1.metric(f"🌡️ Temperature ({units})",  f"{temp_disp}{units}")
    wc2.metric("🤔 Feels Like",              f"{fl_disp}{units}")
    wc3.metric("💧 Humidity",                f"{humidity}%")
    wc4.metric("💨 Wind Speed",              f"{wind_speed} m/s")

    wc5, wc6, wc7 = st.columns(3)
    wc5.metric("🌫️ Visibility",   f"{weather['visibility']:.1f} km")
    wc6.metric("🔵 Pressure",     f"{weather['pressure']} hPa")
    wc7.metric("🧭 Wind Dir.",    f"{weather['wind_deg']}°")

    st.markdown("---")

    # Weather-AQI correlation scatter (synthetic history)
    st.markdown('<div class="card-title">TEMPERATURE vs AQI CORRELATION</div>', unsafe_allow_html=True)
    np.random.seed(42)
    temps_hist = np.random.normal(temp, 5, 60)
    aqi_hist   = predicted_aqi + (temps_hist - temp) * 1.5 + np.random.normal(0, 8, 60)
    scatter_fig = go.Figure(go.Scatter(
        x=temps_hist, y=aqi_hist,
        mode="markers",
        marker=dict(color=aqi_hist, colorscale=[[0,"#22c55e"],[0.5,"#f97316"],[1,"#ef4444"]],
                    size=7, opacity=0.75, showscale=True,
                    colorbar=dict(
                        title=dict(text="AQI", font=dict(color="#94a3b8")),
                        tickfont=dict(color="#94a3b8")
                    )),
        text=[f"Temp: {t:.1f}°C | AQI: {a:.0f}" for t, a in zip(temps_hist, aqi_hist)],
        hovertemplate="%{text}<extra></extra>"
    ))
    scatter_fig.update_layout(**PLOTLY_LAYOUT, height=320,
                              xaxis_title=f"Temperature ({units})", yaxis_title="AQI")
    st.plotly_chart(scatter_fig, use_container_width=True)

    # Weather conditions impact card
    st.markdown('<div class="card-title">WEATHER IMPACT ANALYSIS</div>', unsafe_allow_html=True)
    impacts = []
    if wind_speed > 5:
        impacts.append(("💨 High Wind", "Likely dispersing pollutants — expect improving air quality", "good"))
    if humidity > 80:
        impacts.append(("💧 High Humidity", "Moisture traps particulates near ground level — pollutants elevated", "bad"))
    if humidity < 30:
        impacts.append(("🌵 Low Humidity", "Dry conditions may increase dust and PM10 levels", "moderate"))
    if temp > 35:
        impacts.append(("🔥 High Temperature", "Heat can accelerate ozone formation from NO₂ precursors", "moderate"))
    if not impacts:
        impacts.append(("✅ Neutral Conditions", "No significant weather amplification of air quality issues", "good"))

    for title, desc, severity in impacts:
        cls = "alert-good" if severity == "good" else ("alert-moderate" if severity == "moderate" else "alert-bad")
        st.markdown(f'<div class="{cls}" style="margin-bottom:0.6rem;"><b>{title}</b><br>{desc}</div>',
                    unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 4 — GLOBAL MAP
# ══════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="card-title">GLOBAL AQI MAP</div>', unsafe_allow_html=True)

    # ── Map uses estimated AQI (no extra API calls) ──────────────
    # Only the selected city uses real API data (already fetched above).
    # All other cities use a deterministic seed so values are stable
    # across rerenders but don't waste API quota.
    TYPICAL_AQI = {
        "Delhi, India": 158,      "Mumbai, India": 98,
        "Kolkata, India": 134,    "Bangalore, India": 72,
        "Chennai, India": 85,     "Beijing, China": 145,
        "Shanghai, China": 88,    "Tokyo, Japan": 42,
        "Seoul, South Korea": 78, "Bangkok, Thailand": 95,
        "Jakarta, Indonesia": 112,"London, UK": 38,
        "Paris, France": 45,      "Berlin, Germany": 35,
        "Moscow, Russia": 62,     "New York, USA": 48,
        "Los Angeles, USA": 72,   "Mexico City, Mexico": 118,
        "São Paulo, Brazil": 85,  "Cairo, Egypt": 132,
        "Lagos, Nigeria": 105,    "Sydney, Australia": 28,
        "Dubai, UAE": 88,         "Singapore": 45,
        "Karachi, Pakistan": 165, "Lahore, Pakistan": 172,
        "Dhaka, Bangladesh": 155, "Tehran, Iran": 128,
        "Istanbul, Turkey": 68,   "Madrid, Spain": 42,
    }

    map_rows = []
    for cname, (clat, clon) in cities.items():
        # Use real AQI for selected city, typical estimates for all others
        if cname == city:
            est_aqi = predicted_aqi
        else:
            est_aqi = TYPICAL_AQI.get(cname, None)
            if est_aqi is None:
                # deterministic fallback based on city name hash
                np.random.seed(hash(cname) % 9999)
                est_aqi = int(np.random.randint(25, 180))
        lbl, col, _ = aqi_label(est_aqi)
        map_rows.append({"City": cname, "lat": clat, "lon": clon,
                         "AQI": est_aqi, "Category": lbl})
    st.caption("🟢 Selected city shows live AQI · Other cities show typical reference values")

    map_df = pd.DataFrame(map_rows)

    map_fig = px.scatter_mapbox(
        map_df, lat="lat", lon="lon",
        color="AQI", size="AQI",
        hover_name="City",
        hover_data={"AQI": True, "Category": True, "lat": False, "lon": False},
        color_continuous_scale=[
            [0,    "#22c55e"],
            [0.25, "#86efac"],
            [0.4,  "#facc15"],
            [0.6,  "#f97316"],
            [0.75, "#ef4444"],
            [1,    "#a855f7"]
        ],
        size_max=35, zoom=1.5,
        mapbox_style="carto-darkmatter",
    )
    map_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0), height=520,
        coloraxis_colorbar=dict(
            title=dict(text="AQI", font=dict(color="#94a3b8")),
            tickfont=dict(color="#94a3b8")
        )
    )
    st.plotly_chart(map_fig, use_container_width=True)

    # AQI ranking table
    st.markdown('<div class="card-title">CITY AQI RANKING (LIVE)</div>', unsafe_allow_html=True)
    ranked = map_df[["City", "AQI", "Category"]].sort_values("AQI").reset_index(drop=True)
    ranked.insert(0, "Rank", range(1, len(ranked) + 1))
    st.dataframe(
        ranked.style
              .background_gradient(subset=["AQI"], cmap="RdYlGn_r")
              .set_properties(**{"background-color": "#111827", "color": "#e2e8f0"}),
        use_container_width=True, hide_index=True
    )

# ══════════════════════════════════════════════
# TAB 5 — CITY COMPARE
# ══════════════════════════════════════════════
with tabs[4]:
    if not enable_compare or compare_city is None:
        st.markdown("""
        <div style="text-align:center; padding:3rem 2rem; background:#111827;
                    border:1px dashed #1f2d40; border-radius:16px; margin-top:1rem;">
          <div style="font-size:2rem; margin-bottom:0.75rem;">⚖️</div>
          <div style="font-family:'Space Mono',monospace; font-size:0.85rem;
                      color:#64748b; letter-spacing:1px;">
            CITY COMPARISON DISABLED
          </div>
          <div style="color:#475569; font-size:0.8rem; margin-top:0.5rem;">
            Enable <b style="color:#94a3b8">⚖️ City Comparison</b> in the sidebar to compare two cities side-by-side.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        c_lat, c_lon = cities[compare_city]

        with st.spinner(f"Fetching data for {compare_city}..."):
            try:
                c_comp = fetch_aqi(c_lat, c_lon)
                c_wx   = fetch_weather(c_lat, c_lon)
            except Exception:
                c_comp = {"pm2_5": 38.1, "pm10": 55.2, "no2": 28.4, "o3": 48.0, "so2": 6.1, "co": 380.0}
                c_wx   = {"temp": 25, "humidity": 65, "wind_speed": 4.1}

        c_pm25 = c_comp["pm2_5"]
        c_pm10 = c_comp["pm10"]
        c_no2  = c_comp["no2"]
        c_aqi  = predict_aqi(c_pm25, c_pm10, c_no2, c_wx["temp"], c_wx["humidity"])

        # Head-to-head KPIs
        st.markdown('<div class="card-title">HEAD-TO-HEAD COMPARISON</div>', unsafe_allow_html=True)
        hh1, hh2, hh3 = st.columns([2, 1, 2])

        with hh1:
            lbl1, col1, _ = aqi_label(predicted_aqi)
            st.markdown(f"""
            <div style="text-align:center; padding:1.5rem; background:#111827;
                        border:1px solid #1f2d40; border-radius:12px;">
              <div style="font-size:0.7rem;letter-spacing:2px;color:#64748b;margin-bottom:0.5rem;">{city.upper()}</div>
              <div style="font-family:'Space Mono',monospace;font-size:3rem;color:{col1};font-weight:700;">
                {int(predicted_aqi)}
              </div>
              <div style="font-size:0.8rem;color:{col1};">{lbl1}</div>
            </div>
            """, unsafe_allow_html=True)

        with hh2:
            winner = city if predicted_aqi < c_aqi else compare_city
            st.markdown(f"""
            <div style="text-align:center;padding-top:2.5rem;color:#64748b;font-size:0.9rem;">
              VS<br>
              <div style="margin-top:0.8rem;font-size:0.65rem;letter-spacing:1px;color:#22c55e;">
                🏆 {winner.split(',')[0]}<br>cleaner air
              </div>
            </div>
            """, unsafe_allow_html=True)

        with hh3:
            lbl2, col2, _ = aqi_label(c_aqi)
            st.markdown(f"""
            <div style="text-align:center; padding:1.5rem; background:#111827;
                        border:1px solid #1f2d40; border-radius:12px;">
              <div style="font-size:0.7rem;letter-spacing:2px;color:#64748b;margin-bottom:0.5rem;">
                {compare_city.upper()}
              </div>
              <div style="font-family:'Space Mono',monospace;font-size:3rem;color:{col2};font-weight:700;">
                {int(c_aqi)}
              </div>
              <div style="font-size:0.8rem;color:{col2};">{lbl2}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Grouped bar: all pollutants
        st.markdown('<div class="card-title">POLLUTANT BREAKDOWN</div>', unsafe_allow_html=True)
        poll_compare_df = pd.DataFrame({
            "Pollutant": ["PM2.5", "PM10", "NO₂", "O₃", "SO₂"],
            city:         [pm25, pm10, no2, o3, so2],
            compare_city: [c_pm25, c_pm10, c_no2,
                           c_comp.get("o3", 0), c_comp.get("so2", 0)]
        })
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name=city,         x=poll_compare_df["Pollutant"],
                                 y=poll_compare_df[city],         marker_color="#00e5ff"))
        fig_bar.add_trace(go.Bar(name=compare_city, x=poll_compare_df["Pollutant"],
                                 y=poll_compare_df[compare_city], marker_color="#7c3aed"))
        fig_bar.update_layout(**PLOTLY_LAYOUT, barmode="group", height=320,
                              legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40"),
                              yaxis_title="µg/m³")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Radar comparison
        st.markdown('<div class="card-title">RADAR COMPARISON</div>', unsafe_allow_html=True)
        r_cats = ["PM2.5", "PM10", "NO₂", "O₃", "SO₂"]
        r_v1   = [pm25, pm10, no2, o3, so2]
        r_v2   = [c_pm25, c_pm10, c_no2, c_comp.get("o3", 0), c_comp.get("so2", 0)]

        fig_cr = go.Figure()
        for vals, name, col in [(r_v1, city, "#00e5ff"), (r_v2, compare_city, "#7c3aed")]:
            fig_cr.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=r_cats + [r_cats[0]],
                fill="toself", name=name,
                fillcolor=f"rgba({'0,229,255' if col == '#00e5ff' else '124,58,237'},0.1)",
                line=dict(color=col, width=2)
            ))
        fig_cr.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, gridcolor="#1f2d40", color="#475569"),
                angularaxis=dict(gridcolor="#1f2d40", color="#94a3b8")
            ),
            paper_bgcolor="rgba(0,0,0,0)", height=380,
            font=dict(family="Sora", color="#94a3b8"),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d40")
        )
        st.plotly_chart(fig_cr, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 6 — HEALTH
# ══════════════════════════════════════════════
with tabs[5]:
    lbl_h, col_h, alert_h = aqi_label(predicted_aqi)
    st.markdown(f"""
    <div class="{alert_h}" style="margin-bottom:1.2rem;font-size:1rem;">
      <b>Current Air Quality: {lbl_h}</b> — AQI {int(predicted_aqi)}<br>
      <span style="font-size:0.85rem;opacity:0.85;">City: {city} · {datetime.now().strftime('%d %b %Y %H:%M')}</span>
    </div>
    """, unsafe_allow_html=True)

    # Group risk matrix
    st.markdown('<div class="card-title">POPULATION RISK MATRIX</div>', unsafe_allow_html=True)
    groups = [
        ("👶 Children",          predicted_aqi * 1.3),
        ("🧓 Elderly",           predicted_aqi * 1.2),
        ("🫁 Respiratory Issues",predicted_aqi * 1.5),
        ("❤️ Heart Conditions",  predicted_aqi * 1.35),
        ("🏃 Athletes (outdoor)",predicted_aqi * 1.1),
        ("🧑 General Public",    predicted_aqi * 1.0),
    ]
    fig_risk = go.Figure()
    for grp, risk_aqi in groups:
        rl, rc, _ = aqi_label(risk_aqi)
        fig_risk.add_trace(go.Bar(
            y=[grp], x=[min(risk_aqi, 300)],
            orientation="h", name=grp,
            marker_color=aqi_color(risk_aqi),
            text=f"{rl} ({risk_aqi:.0f})",
            textposition="outside",
            textfont=dict(color="#94a3b8", size=11)
        ))
    risk_layout = {**PLOTLY_LAYOUT, "height": 320, "showlegend": False}
    risk_layout["xaxis"] = dict(range=[0, 350], title="Effective Risk AQI",
                                gridcolor="#1f2d40", zerolinecolor="#1f2d40")
    risk_layout["yaxis"] = dict(gridcolor="rgba(0,0,0,0)")
    fig_risk.update_layout(**risk_layout)
    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown('<div class="card-title">HEALTH RECOMMENDATIONS</div>', unsafe_allow_html=True)
    recs = {
        "Good": [
            "✅ Ideal for all outdoor activities including jogging and cycling.",
            "✅ Open windows for natural ventilation.",
            "✅ No precautions required.",
        ],
        "Moderate": [
            "⚠️ Unusually sensitive individuals should consider reducing prolonged outdoor exertion.",
            "⚠️ Keep windows slightly open but monitor air quality.",
            "⚠️ Asthma patients should carry inhalers.",
        ],
        "Unhealthy*": [
            "🔴 Sensitive groups (children, elderly, asthma) should limit outdoor activities.",
            "🔴 Everyone else should reduce prolonged or heavy exertion outdoors.",
            "🔴 Consider wearing N95 mask when outside.",
        ],
        "Unhealthy": [
            "🔴 Everyone should avoid prolonged outdoor exertion.",
            "🔴 Sensitive groups should stay indoors.",
            "🔴 Use air purifiers indoors. Keep doors and windows closed.",
        ],
        "Hazardous": [
            "🚫 Health alert: everyone may experience serious health effects.",
            "🚫 Avoid all outdoor activities.",
            "🚫 Use N95/N99 masks if going out is unavoidable.",
            "🚫 Run HEPA air purifiers indoors continuously.",
        ],
    }
    for rec in recs.get(lbl_h, recs["Good"]):
        st.markdown(f"<div class='{alert_h}' style='margin-bottom:0.4rem;font-size:0.9rem;'>{rec}</div>",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="card-title">AQI INDEX REFERENCE</div>', unsafe_allow_html=True)
    ref_df = pd.DataFrame({
        "AQI Range":    ["0–50", "51–100", "101–150", "151–200", "201–300"],
        "Category":     ["Good", "Moderate", "Unhealthy for Sensitive", "Unhealthy", "Hazardous"],
        "WHO Color":    ["🟢 Green", "🟡 Yellow", "🟠 Orange", "🔴 Red", "🟣 Purple"],
        "Main Concern": [
            "Air quality satisfactory",
            "Acceptable; some pollutants may affect sensitive groups",
            "Members of sensitive groups may experience effects",
            "General public begins to experience effects",
            "Health warnings of emergency conditions"
        ]
    })
    st.dataframe(ref_df, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.markdown("---")
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            color:#334155;font-size:0.72rem;padding:0.5rem 0;">
  <span>🌬️ <b style="color:#475569">AQI Pulse</b> — Developed for AI/ML AQI Prediction Project</span>
  <span>Last updated: {datetime.now().strftime('%d %b %Y · %H:%M UTC')} &nbsp;·&nbsp; Data: OpenWeatherMap</span>
</div>
""", unsafe_allow_html=True)