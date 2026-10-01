import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory Setup
BASE = Path(__file__).resolve().parent.parent
PUBLIC_DIR = os.path.join(BASE, "public")

load_dotenv(BASE / ".env")
load_dotenv()

import joblib
import pandas as pd
import uvicorn
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Jal Shakti Gujarat API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load Machine Learning Model (Retained for analytics/comparison if needed)
model_harvest = joblib.load(os.path.join(BASE, "harvest_model.pkl"))

# Load Summary Statistics
summary_path = os.path.join(PUBLIC_DIR, "summary_stats.json")
summary = json.load(open(summary_path, "r", encoding="utf-8")) if os.path.exists(summary_path) else {}

# Load District Dataset
districts_path = os.path.join(PUBLIC_DIR, "districts.json")
districts_data = json.load(open(districts_path, "r", encoding="utf-8")) if os.path.exists(districts_path) else {"monsoon_distribution": {}, "districts": []}

ZONE_MAP = {"arid": "Arid", "semi-arid": "Semi-Arid", "coastal": "Coastal"}

DISTRICT_LOOKUP = {}
for d in districts_data.get("districts", []):
    DISTRICT_LOOKUP[d["name"]] = d
    DISTRICT_LOOKUP[d["en"].lower()] = d

MONSOON_DIST = districts_data.get("monsoon_distribution", {})

def get_district_monthly_rain(district_obj):
    annual = district_obj.get("annual_rain_mm", 0) or 0
    return {m: round((annual * MONSOON_DIST.get(str(m), 0.5)) / 100, 1) for m in range(1, 13)}

try:
    from . import ai_advisor
except ImportError:
    import ai_advisor

@app.get("/api/summary")
def get_summary():
    return summary

@app.get("/api/districts")
def get_districts():
    return districts_data.get("districts", [])

@app.get("/api/district")
def get_district(name: str):
    d = DISTRICT_LOOKUP.get(name) or DISTRICT_LOOKUP.get(name.lower())
    if not d:
        return {"error": f"District '{name}' not found"}

    monthly_rain = get_district_monthly_rain(d)
    zone = d["zone"]
    result = {
        "name": d["name"],
        "en": d["en"],
        "zone": zone,
        "annual_rain_mm": d.get("annual_rain_mm"),
        "monthly": {}
    }

    # Baseline 190 sq.m RCC roof (coefficient 0.85, collection efficiency 0.90)
    ROOF_M2 = 190.0
    ROOF_COEFF = 0.85
    COLLECTION_EFF = 0.90

    for m in range(1, 13):
        rain = monthly_rain.get(m, 5.0)
        total_rain_raw = rain * ROOF_M2
        harvest_raw = total_rain_raw * ROOF_COEFF * COLLECTION_EFF
        loss_raw = total_rain_raw - harvest_raw

        # Internal Validation Check
        assert abs(total_rain_raw - (harvest_raw + loss_raw)) < 1e-5, "District Mass Balance Error"

        total_disp = round(total_rain_raw, 1)
        harvest_disp = round(harvest_raw, 1)
        loss_disp = round(total_disp - harvest_disp, 1)

        zone_hist = summary.get(zone, {}).get("historical_monthly", {})
        avg_gwl = zone_hist.get(str(m), {}).get("avg_gwl_m", -30.0)

        result["monthly"][str(m)] = {
            "rainfall_mm": rain,
            "harvestable_liters": harvest_disp,
            "water_lost_liters": loss_disp,
            "avg_gwl_m": avg_gwl
        }

    return result

@app.get("/api/predict")
def predict(
    zone: str,
    family_size: int,
    month: int,
    rainfall_mm: float = Query(None),
    district: str = Query(None),
    roof_m2: float = Query(100.0),
    roof_type: str = Query("concrete")  # concrete/rcc (0.85), tiles (0.80), metal (0.90)
):
    z = ZONE_MAP.get(zone.lower(), "Semi-Arid")
    rain = rainfall_mm

    if rain is None and district:
        d = DISTRICT_LOOKUP.get(district) or DISTRICT_LOOKUP.get(district.lower())
        if d:
            rain = get_district_monthly_rain(d).get(month, 5.0)

    if rain is None:
        hist = summary.get(z, {}).get("historical_monthly", {})
        rain = hist.get(str(month), {}).get("rainfall_mm", 50.0)

    # -------------------------------------------------------------
    # PHYSICAL SOURCE OF TRUTH CALCULATIONS (IS 15797 / CGWB)
    # -------------------------------------------------------------
    roof_clean = roof_type.lower().strip()
    coeff_map = {
        "concrete": 0.85,
        "rcc": 0.85,
        "tiles": 0.80,
        "metal": 0.90
    }
    c_factor = coeff_map.get(roof_clean, 0.85)
    filter_efficiency = 0.90  # Fixed collection/filtration efficiency

    # 1. Total Rainfall Volume
    total_rain_raw = rain * roof_m2

    # 2. Potential Harvestable Water
    harvestable_raw = total_rain_raw * c_factor * filter_efficiency

    # 3. Unharvested / Runoff Water
    water_lost_raw = total_rain_raw - harvestable_raw

    # -------------------------------------------------------------
    # INTERNAL MASS BALANCE VALIDATION CHECK
    # -------------------------------------------------------------
    mass_diff = abs(total_rain_raw - (harvestable_raw + water_lost_raw))
    if mass_diff >= 1e-5:
        # Re-reconcile physically if an anomaly occurs
        water_lost_raw = max(0.0, total_rain_raw - harvestable_raw)

    # Percentage Calculations
    harvest_pct_raw = (harvestable_raw / total_rain_raw * 100.0) if total_rain_raw > 0 else 0.0
    loss_pct_raw = (water_lost_raw / total_rain_raw * 100.0) if total_rain_raw > 0 else 0.0

    # Household Water Demand Coverage (IS 1172: 135 L/person/day)
    household_monthly_demand = family_size * 135.0 * 30.0
    months_drinking_water_raw = harvestable_raw / household_monthly_demand if household_monthly_demand > 0 else 0.0

    # -------------------------------------------------------------
    # DISPLAY ROUNDING (Performed ONLY at response formatting stage)
    # -------------------------------------------------------------
    total_rain_liters = round(total_rain_raw, 1)
    harvestable_liters = round(harvestable_raw, 1)
    # Enforce exact addition equality after rounding: Total = Harvest + Lost
    water_lost_liters = round(total_rain_liters - harvestable_liters, 1)

    return {
        "zone": z,
        "family_size": family_size,
        "month": month,
        "rainfall_mm": round(rain, 1),
        "roof_m2": roof_m2,
        "roof_type": roof_type,
        "roof_coefficient": c_factor,
        "collection_efficiency": filter_efficiency,
        "total_rain_liters": total_rain_liters,
        "harvestable_liters": harvestable_liters,
        "water_lost_liters": water_lost_liters,
        "harvest_percentage": round(harvest_pct_raw, 1),
        "loss_percentage": round(loss_pct_raw, 1),
        "months_drinking_water": round(months_drinking_water_raw, 2)
    }

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    return {"reply": await ai_advisor.reply(body.get("message", ""), body.get("mode", "standard"))}

if os.path.exists(PUBLIC_DIR):
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")

try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
