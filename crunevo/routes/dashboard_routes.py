from __future__ import annotations

import asyncio
import requests
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from crunevo.cache import weather_cache


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.get("/")
@login_required
def index():
    return render_template("dashboard/dashboard.html")


async def fetch_weather(lat: float, lon: float) -> dict | None:
    key = f"{lat:.2f},{lon:.2f}"
    cached = weather_cache.get(key)
    if cached:
        return cached

    api_key = current_app.config.get("OPENWEATHER_API_KEY")
    if not api_key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "es"}

    loop = asyncio.get_running_loop()

    def _do_request():
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()

    data = await loop.run_in_executor(None, _do_request)
    weather_cache.set(key, data)
    return data


@dashboard_bp.get("/weather")
@login_required
def weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify(error="missing coordinates"), 400

    data = asyncio.run(fetch_weather(lat, lon))
    if not data:
        return jsonify(error="unavailable"), 502

    weather = data.get("weather", [{}])[0]
    icon = weather.get("icon", "01d")
    return jsonify(
        city=data.get("name"),
        temp=data.get("main", {}).get("temp"),
        desc=weather.get("description"),
        icon=f"https://openweathermap.org/img/wn/{icon}@2x.png",
    )
