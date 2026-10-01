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
    from api.ai_advisor import reply as ai_reply
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
        "app:app",
