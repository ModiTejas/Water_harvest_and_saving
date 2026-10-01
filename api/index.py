from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
PUBLIC_DIR = PROJECT_DIR / "public"

# Load local .env during development.
# On Vercel, environment variables come from Vercel itself.
load_dotenv(BASE_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Jal Shakti Gujarat API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATA LOADERS
# ============================================================

def load_json(path: Path, default: Any) -> Any:
    """
    Safely load a JSON file.

    If the file is missing or invalid, return the supplied
    default instead of crashing the entire Vercel function.
    """
    try:
        if not path.exists():
            return default

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return default


SUMMARY_STATS = load_json(
    PUBLIC_DIR / "summary_stats.json",
    {},
)

DISTRICTS_DATA = load_json(
    PUBLIC_DIR / "districts.json",
    {
        "monsoon_distribution": {},
        "districts": [],
    },
)


# ============================================================
# DISTRICT DATA
# ============================================================

ZONE_MAP = {
    "arid": "Arid",
    "semi-arid": "Semi-Arid",
    "coastal": "Coastal",
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def get_district_list() -> list[dict]:
    """
    Supports the existing districts.json structure.
    """
    if isinstance(DISTRICTS_DATA, dict):
        districts = DISTRICTS_DATA.get("districts", [])

        if isinstance(districts, list):
            return districts

    if isinstance(DISTRICTS_DATA, list):
        return DISTRICTS_DATA

    return []


DISTRICTS = get_district_list()


# Build lookup using both Gujarati and English names.
DISTRICT_LOOKUP: dict[str, dict] = {}

for district in DISTRICTS:
    if not isinstance(district, dict):
        continue

    gu_name = district.get("name")
    en_name = district.get("en")

    if gu_name:
        DISTRICT_LOOKUP[normalize_text(gu_name)] = district

    if en_name:
        DISTRICT_LOOKUP[normalize_text(en_name)] = district


MONSOON_DIST = (
    DISTRICTS_DATA.get("monsoon_distribution", {})
    if isinstance(DISTRICTS_DATA, dict)
    else {}
)


def find_district(name: str | None) -> dict | None:
    if not name:
        return None

    key = normalize_text(name)

    if key in DISTRICT_LOOKUP:
        return DISTRICT_LOOKUP[key]

    # Small fallback: compare without extra whitespace.
    compact_key = " ".join(key.split())

    for lookup_name, district in DISTRICT_LOOKUP.items():
        if " ".join(lookup_name.split()) == compact_key:
            return district

    return None


# ============================================================
# RAINFALL HELPERS
# ============================================================

def get_district_annual_rainfall(district: dict) -> float:
    """
    Accept several common field names so the API remains
    compatible with the existing districts.json data.
    """
    candidates = (
        district.get("annual_rain_mm"),
        district.get("rainfall_mm"),
        district.get("annual_rainfall"),
        district.get("rain_annual"),
        district.get("rain_total"),
    )

    for value in candidates:
        try:
            if value is not None:
                number = float(value)

                if number >= 0:
                    return number

        except (TypeError, ValueError):
            pass

    return 0.0


def get_district_zone(district: dict) -> str:
    zone = district.get("zone")

    if zone:
        zone_key = normalize_text(zone)

        if zone_key in ZONE_MAP:
            return ZONE_MAP[zone_key]

        return str(zone)

    return "Semi-Arid"


def get_district_monthly_rain(
    district: dict,
) -> dict[str, float]:
    """
    Convert annual rainfall into monthly rainfall using
    the existing monsoon distribution data.

    Expected distribution:
        month -> percentage

    Example:
        June -> 8
        July -> 25
        ...
    """

    annual_rain = get_district_annual_rainfall(district)

    # First try district-specific monthly distribution.
    distribution = (
        district.get("monsoon_distribution")
        or district.get("monthly_distribution")
        or district.get("rain_distribution")
    )

    # Otherwise use the global distribution.
    if not isinstance(distribution, dict):
        distribution = MONSOON_DIST

    result: dict[str, float] = {}

    for month, percentage in distribution.items():
        try:
            pct = float(percentage)
            result[str(month)] = annual_rain * pct / 100.0

        except (TypeError, ValueError):
            result[str(month)] = 0.0

    return result


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/api")
def api_home():
    return {
        "name": "Jal Shakti Gujarat API",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "api": "Jal Shakti Gujarat",
    }


# ============================================================
# SUMMARY
# ============================================================

@app.get("/api/summary")
def get_summary():
    return SUMMARY_STATS


# ============================================================
# DISTRICTS
# ============================================================

@app.get("/api/districts")
def get_districts():
    return DISTRICTS


# ============================================================
# SINGLE DISTRICT
# ============================================================

@app.get("/api/district")
def get_district(
    name: str = Query(..., min_length=1),
):
    district = find_district(name)

    if district is None:
        return {
            "error": "District not found",
            "name": name,
        }

    annual_rain = get_district_annual_rainfall(district)

    monthly_rain = get_district_monthly_rain(district)

    # Existing dashboard baseline.
    roof_m2 = 190.0

    # Roof runoff coefficient.
    roof_coefficient = 0.85

    # Collection efficiency.
    collection_efficiency = 0.90

    monthly = {}

    for month, rainfall_mm in monthly_rain.items():
        total_rain_liters = rainfall_mm * roof_m2

        harvestable_liters = (
            total_rain_liters
            * roof_coefficient
            * collection_efficiency
        )

        water_lost_liters = max(
            0.0,
            total_rain_liters - harvestable_liters,
        )

        monthly[month] = {
            "rainfall_mm": round(rainfall_mm, 2),
            "total_rain_liters": round(total_rain_liters, 2),
            "harvestable_liters": round(
                harvestable_liters,
                2,
            ),
            "water_lost_liters": round(
                water_lost_liters,
                2,
            ),
        }

    # Preserve any existing groundwater information.
    if "monthly" in district and isinstance(
        district["monthly"],
        dict,
    ):
        source_monthly = district["monthly"]

        for month, source_data in source_monthly.items():
            if month in monthly and isinstance(
                source_data,
                dict,
            ):
                if "avg_gwl_m" in source_data:
                    monthly[month]["avg_gwl_m"] = (
                        source_data["avg_gwl_m"]
                    )

    gwl_values = []

    for month_data in monthly.values():
        if "avg_gwl_m" in month_data:
            try:
                gwl_values.append(
                    float(month_data["avg_gwl_m"])
                )
            except (TypeError, ValueError):
                pass

    if gwl_values:
        avg_groundwater = sum(gwl_values) / len(gwl_values)
    else:
        avg_groundwater = district.get(
            "avg_gwl_m",
            district.get("gwls_mean"),
        )

        try:
            avg_groundwater = float(avg_groundwater)
        except (TypeError, ValueError):
            avg_groundwater = None

    total_rain_volume = annual_rain * roof_m2

    total_harvestable = (
        total_rain_volume
        * roof_coefficient
        * collection_efficiency
    )

    total_loss = max(
        0.0,
        total_rain_volume - total_harvestable,
    )

    # Mass balance check.
    assert abs(
        total_rain_volume
        - total_harvestable
        - total_loss
    ) < 0.01

    return {
        "name": district.get("name", name),
        "en": district.get("en"),
        "zone": get_district_zone(district),
        "annual_rain_mm": round(annual_rain, 2),
        "monthly": monthly,
        "harvestable_liters": round(
            total_harvestable,
            2,
        ),
        "water_lost_liters": round(
            total_loss,
            2,
        ),
        "avg_groundwater_level": (
            round(avg_groundwater, 2)
            if avg_groundwater is not None
            else None
        ),
        "roof_m2": roof_m2,
        "roof_coefficient": roof_coefficient,
        "collection_efficiency": collection_efficiency,
    }


# ============================================================
# PREDICTION / CALCULATOR
# ============================================================

ROOF_COEFFICIENTS = {
    "concrete": 0.85,
    "rcc": 0.85,
    "tiles": 0.80,
    "metal": 0.90,
}

COLLECTION_EFFICIENCY = 0.90

DAILY_WATER_NEED_PER_PERSON = 135.0

DAYS_PER_MONTH = 30


@app.get("/api/predict")
def predict(
    zone: str = Query(...),
    family_size: int = Query(..., ge=1),
    month: str = Query(...),
    rainfall_mm: float | None = Query(
        default=None,
        ge=0,
    ),
    district: str | None = Query(default=None),
    roof_m2: float = Query(
        default=100.0,
        gt=0,
    ),
    roof_type: str = Query(default="concrete"),
):
    """
    Rainwater harvesting calculator.

    This keeps the existing frontend contract.

    Inputs:
        zone
        family_size
        month
        rainfall_mm
        district
        roof_m2
        roof_type

    Outputs:
        total_rain_liters
        harvestable_liters
        water_lost_liters
        percentages
        household demand
        months of drinking-water coverage
    """

    roof_type_normalized = normalize_text(
        roof_type
    )

    if roof_type_normalized not in ROOF_COEFFICIENTS:
        roof_type_normalized = "concrete"

    roof_coefficient = ROOF_COEFFICIENTS[
        roof_type_normalized
    ]

    # --------------------------------------------------------
    # Rainfall source
    # --------------------------------------------------------

    selected_district = find_district(district)

    if rainfall_mm is not None:
        rain = float(rainfall_mm)

    elif selected_district is not None:
        monthly_rain = get_district_monthly_rain(
            selected_district
        )

        # Try exact month.
        if month in monthly_rain:
            rain = float(monthly_rain[month])

        else:
            # Case-insensitive month matching.
            rain = 0.0

            target = normalize_text(month)

            for key, value in monthly_rain.items():
                if normalize_text(key) == target:
                    rain = float(value)
                    break

    else:
        # No district and no rainfall supplied.
        # Preserve a safe zero rather than inventing rainfall.
        rain = 0.0

    # --------------------------------------------------------
    # Physical calculation
    # --------------------------------------------------------

    total_rain_raw = rain * roof_m2

    harvestable_raw = (
        total_rain_raw
        * roof_coefficient
        * COLLECTION_EFFICIENCY
    )

    water_lost_raw = max(
        0.0,
        total_rain_raw - harvestable_raw,
    )

    # --------------------------------------------------------
    # Household demand
    # --------------------------------------------------------

    monthly_household_demand = (
        family_size
        * DAILY_WATER_NEED_PER_PERSON
        * DAYS_PER_MONTH
    )

    months_drinking_water = (
        harvestable_raw / monthly_household_demand
        if monthly_household_demand > 0
        else 0.0
    )

    harvest_percentage = (
        harvestable_raw / total_rain_raw * 100
        if total_rain_raw > 0
        else 0.0
    )

    loss_percentage = (
        water_lost_raw / total_rain_raw * 100
        if total_rain_raw > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "zone": zone,
        "district": (
            selected_district.get("name")
            if selected_district
            else district
        ),
        "month": month,
        "family_size": family_size,

        "rainfall_mm": round(rain, 2),

        "roof_m2": round(roof_m2, 2),
        "roof_type": roof_type_normalized,
        "roof_coefficient": roof_coefficient,
        "collection_efficiency": (
            COLLECTION_EFFICIENCY
        ),

        "total_rain_liters": round(
            total_rain_raw,
            2,
        ),

        "harvestable_liters": round(
            harvestable_raw,
            2,
        ),

        "water_lost_liters": round(
            water_lost_raw,
            2,
        ),

        "harvest_percentage": round(
            harvest_percentage,
            2,
        ),

        "loss_percentage": round(
            loss_percentage,
            2,
        ),

        "daily_water_need_per_person": (
            DAILY_WATER_NEED_PER_PERSON
        ),

        "monthly_household_demand_liters": round(
            monthly_household_demand,
            2,
        ),

        "months_drinking_water": round(
            months_drinking_water,
            2,
        ),
    }


# ============================================================
# AI ADVISOR
# ============================================================

try:
    from .ai_advisor import reply as ai_reply
except ImportError:
    from ai_advisor import reply as ai_reply


@app.post("/api/chat")
async def chat(payload: dict):
    """
    Frontend sends:

    {
        "message": "...",
        "mode": "standard" | "deep"
    }
    """

    message = str(
        payload.get("message", "")
    ).strip()

    mode = str(
        payload.get("mode", "standard")
    ).strip().lower()

    if not message:
        return {
            "reply": "કૃપા કરીને તમારો પ્રશ્ન લખો."
        }

    if mode not in {"standard", "deep"}:
        mode = "standard"

    try:
        response = ai_reply(
            message,
            mode,
        )

        return {
            "reply": response
        }

    except Exception:
        # Never allow an AI failure to break the website.
        return {
            "reply": (
                "માફ કરશો, હાલમાં AI સલાહકાર ઉપલબ્ધ નથી. "
                "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
            )
        }


# ============================================================
# STATIC FRONTEND
# ============================================================

# This is mainly useful for local `uvicorn` development.
# Vercel can also promote StaticFiles content to its CDN.
#
# IMPORTANT:
# API routes are declared BEFORE this mount, so:
# /api/... -> FastAPI
# /        -> public/
#
if PUBLIC_DIR.exists():
    app.mount(
        "/",
        StaticFiles(
            directory=str(PUBLIC_DIR),
            html=True,
        ),
        name="public",
    )


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.index:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
