# app.py
import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime
from collections import OrderedDict

# --------------------------
# CONFIG
# --------------------------
API_KEY = "d8ea3a5dd6967b3d0e80d2e43dc4160a"  # <-- replace with your key
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

st.set_page_config(page_title="Weather App", page_icon="☀️", layout="centered")

# --------------------------
# Helpers
# --------------------------
def get_background_style(condition: str):
    c = (condition or "").lower()
    if "clear" in c:
        return "linear-gradient(to bottom, #87CEEB, #ffffff)"  # sunny
    if "cloud" in c:
        return "linear-gradient(to bottom, #d3d3d3, #ffffff)"  # cloudy
    if any(k in c for k in ("rain", "drizzle", "thunderstorm")):
        return "linear-gradient(to bottom, #5f6a6a, #dfe6e9)"  # rainy
    if "snow" in c:
        return "linear-gradient(to bottom, #cce7ff, #ffffff)"  # snow
    if any(k in c for k in ("mist", "fog", "haze")):
        return "linear-gradient(to bottom, #bdc3c7, #ffffff)"  # fog
    return "linear-gradient(to bottom, #E3F2FD, #FFFFFF)"  # default

# --------------------------
# Global page background (applies to whole Streamlit page)
# --------------------------
st.markdown(
    """
    <style>
        .stApp {
            transition: background 0.6s ease;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------
# Header & Input
# --------------------------
st.markdown("<h1 style='text-align:center; color:#4285F4; font-family:Arial;'>🌤️ Weather</h1>", unsafe_allow_html=True)
city = st.text_input("Enter City Name", placeholder="e.g. London, New York, Delhi")

if not city:
    st.info("Type a city name above and press Enter.")
else:
    try:
        # Fetch current weather
        params = {"q": city, "appid": API_KEY, "units": "metric"}
        current_res = requests.get(CURRENT_URL, params=params, timeout=10).json()

        if str(current_res.get("cod")) != "200":
            # show message (no HTML injection here)
            st.error(f"City not found: {city} — API message: {current_res.get('message')}")
        else:
            # Extract current weather info
            temp = round(current_res["main"]["temp"])
            feels_like = round(current_res["main"]["feels_like"])
            condition = current_res["weather"][0]["description"].title()
            humidity = current_res["main"]["humidity"]
            wind = current_res["wind"]["speed"]
            icon = current_res["weather"][0]["icon"]
            country = current_res["sys"]["country"]
            dt = datetime.fromtimestamp(current_res["dt"]).strftime("%A, %I:%M %p")

            # Set page background depending on current condition
            bg_style = get_background_style(condition)
            # apply background to .stApp (the whole page)
            st.markdown(
                f"""
                <style>
                    .stApp {{
                        background: {bg_style};
                        transition: background 0.6s ease;
                    }}
                </style>
                """,
                unsafe_allow_html=True,
            )

            # Fetch forecast (3-hourly)
            forecast_res = requests.get(FORECAST_URL, params=params, timeout=10).json()
            forecast_list = forecast_res.get("list", [])

            # Build daily aggregated min/max & representative icon/condition (use date string as key)
            daily_data = OrderedDict()
            for entry in forecast_list:
                date_obj = datetime.fromtimestamp(entry["dt"])
                date_key = date_obj.strftime("%Y-%m-%d")
                day_name = date_obj.strftime("%a")
                temp_val = entry["main"]["temp"]
                cond = entry["weather"][0]["description"].title()
                ic = entry["weather"][0]["icon"]

                if date_key not in daily_data:
                    daily_data[date_key] = {
                        "day": day_name,
                        "temps": [],
                        "conds": [],
                        "icons": []
                    }
                daily_data[date_key]["temps"].append(temp_val)
                daily_data[date_key]["conds"].append(cond)
                daily_data[date_key]["icons"].append(ic)

            # Build HTML content (will render inside an iframe via components.html)
            html_parts = []
            html_parts.append("""
            <!doctype html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                body{font-family:Arial, sans-serif; margin:0; padding:20px; background:transparent;}
                .container{max-width:900px; margin:0 auto;}
                .card { background:#f8f9fa; border-radius:16px; padding:18px; box-shadow:0 6px 20px rgba(0,0,0,0.08); }
                .center { text-align:center; }
                .current-temp { font-size:48px; margin:6px 0;}
                .small { color: #555; font-size:14px; margin:4px 0;}
                .row { display:flex; gap:12px; align-items:center; justify-content:center; margin-top:12px; }
                .stat { text-align:center; min-width:100px; }
                .hourly { display:flex; gap:12px; overflow-x:auto; padding:12px 6px; margin-top:18px; }
                .hour-card { min-width:100px; background:#ffffff; padding:12px; border-radius:12px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.06);}
                .daily { display:flex; gap:14px; justify-content:center; flex-wrap:wrap; margin-top:20px; }
                .day-card { background:#ffffff; width:140px; padding:14px; border-radius:12px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.06); }
                /* scrollbar nice */
                .hourly::-webkit-scrollbar { height:8px; }
                .hourly::-webkit-scrollbar-track { background:transparent; }
                .hourly::-webkit-scrollbar-thumb { background:#cfd8e3; border-radius:6px; }
            </style>
            </head>
            <body>
            <div class="container">
            """)

            # Current weather card html
            curr_html = f"""
            <div class="card center">
                <div style="display:flex;justify-content:center;align-items:center;gap:18px;flex-wrap:wrap;">
                    <div>
                        <img src="http://openweathermap.org/img/wn/{icon}@2x.png" width="96" alt="icon">
                    </div>
                    <div style="text-align:left;">
                        <div style="font-weight:700; font-size:18px;">{city.title()}, {country}</div>
                        <div class="small">{dt}</div>
                        <div class="current-temp">{temp}°C</div>
                        <div class="small">Feels like {feels_like}°C • {condition}</div>
                    </div>
                </div>
                <div class="row" style="margin-top:14px;">
                    <div class="stat"><div style="font-weight:700;">💧 {humidity}%</div><div class="small">Humidity</div></div>
                    <div class="stat"><div style="font-weight:700;">💨 {wind} m/s</div><div class="small">Wind</div></div>
                </div>
            </div>
            """
            html_parts.append(curr_html)

            # Hourly forecast (take next up to 16 entries ≈ 48 hours)
            html_parts.append('<h3 style="text-align:center; margin-top:22px; color:#333;">Hourly Forecast</h3>')
            html_parts.append('<div class="hourly">')
            for entry in forecast_list[:16]:
                date_obj = datetime.fromtimestamp(entry["dt"])
                date_txt = date_obj.strftime("%a")
                time_txt = date_obj.strftime("%I %p")
                t = round(entry["main"]["temp"])
                feels = round(entry["main"]["feels_like"])
                ic = entry["weather"][0]["icon"]
                cond = entry["weather"][0]["description"].title()

                hour_card = f"""
                <div class="hour-card">
                    <div style="font-weight:700;">{date_txt}</div>
                    <div class="small">{time_txt}</div>
                    <img src="http://openweathermap.org/img/wn/{ic}.png" width="48" alt="icon">
                    <div style="font-weight:700; margin-top:6px;">{t}°C</div>
                    <div class="small">Feels {feels}°C</div>
                    <div class="small">{cond}</div>
                </div>
                """
                html_parts.append(hour_card)
            html_parts.append('</div>')  # close hourly

            # Daily forecast (aggregate min/max and choose most common icon/cond)
            html_parts.append('<h3 style="text-align:center; margin-top:28px; color:#333;">5-Day Forecast</h3>')
            html_parts.append('<div class="daily">')
            count = 0
            for date_key, info in daily_data.items():
                if count >= 5:
                    break
                temps = info["temps"]
                min_t = round(min(temps))
                max_t = round(max(temps))
                # most common condition & icon
                cond = max(set(info["conds"]), key=info["conds"].count)
                ic = max(set(info["icons"]), key=info["icons"].count)
                day_name = info["day"]

                day_card = f"""
                <div class="day-card">
                    <div style="font-weight:700;">{day_name}</div>
                    <img src="http://openweathermap.org/img/wn/{ic}.png" width="60" alt="icon">
                    <div class="small" style="margin-top:6px;">{cond}</div>
                    <div style="font-weight:700; margin-top:6px;">{max_t}° / {min_t}°C</div>
                </div>
                """
                html_parts.append(day_card)
                count += 1
            html_parts.append('</div>')  # close daily

            # finish html
            html_parts.append("</div></body></html>")
            final_html = "\n".join(html_parts)

            # Render the HTML block inside an iframe (ensures HTML actually renders,
            # avoids streamlit printing raw HTML as text). Height tuned to content.
            components.html(final_html, height=760, scrolling=True)

    except Exception as e:
        st.error("⚠️ Error fetching weather data.")
        st.write(str(e))
