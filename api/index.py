import json
import os
from dotenv import load_dotenv

load_dotenv()  # ponytail: reads .env next to this file so GEMINI_API_KEY works offline

import joblib
import pandas as pd
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE = os.path.dirname(__file__)
PUBLIC_DIR = os.path.join(BASE, "..", "public")

model_harvest = joblib.load(os.path.join(BASE, "harvest_model.pkl"))
model_loss = joblib.load(os.path.join(BASE, "loss_model.pkl"))

summary_path = os.path.join(PUBLIC_DIR, "summary_stats.json")
if os.path.exists(summary_path):
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
else:
    summary = {}

ZONE_MAP = {"arid": "Arid", "semi-arid": "Semi-Arid", "coastal": "Coastal"}

def _standard_reply(message: str) -> str:
    """Rule-based Gujarati fallback used when deep mode is unavailable."""
    msg = message.lower()
    if "કચ્છ" in msg or "શુષ્ક" in msg or "arid" in msg:
        return "કચ્છ અને શુષ્ક વિસ્તારોમાં ચોમાસાનું ૬૫% પાણી વહી જાય છે. સપ્ટેમ્બર ૨૦૨૬ પછીના સમય માટે ખેતતલાવડી અને બોરવેલ રિચાર્જ શ્રેષ્ઠ ઉપાય છે."
    elif "દરિયા" in msg or "દક્ષિણ" in msg or "coastal" in msg:
        return "દરિયાકાંઠાના વિસ્તારમાં ભારે વરસાદ હોવા છતાં સંચયના અભાવે પાણી દરિયામાં વહી જાય છે. છત પર પાણી સંચય (Rooftop Rainwater Harvesting) થી આ પાણી બચાવી શકાય છે."
    elif "એલ નીનો" in msg or "૨૦૨૬" in msg or "elnino" in msg:
        return "૨૦૨૬ ના એલ નીનો પ્રભાવથી ગુજરાતમાં વરસાદમાં ૨૨% નો ઘટાડો નોંધાયો છે. આગામી શિયાળા અને ઉનાળા માટે સંચય કરેલું પાણી જ મુખ્ય આધાર બનશે."
    elif "નીતિ" in msg or "સરકાર" in msg or "પાણી" in msg or "બચાવવાના" in msg:
        return "૧) ૧૦૦ ચો.મી.થી મોટા મકાનો માટે રેન વોટર હાર્વેસ્ટિંગ ફરજિયાત બનાવવું. ૨) ચેકડેમ ઊંડા કરવા. ૩) તળાવોનું ચોમાસા પછીનું ડિસિલ્ટિંગ (કાંપ કાઢવો)."
    else:
        return "જળશક્તિ AI મોડેલમાં આપનું સ્વાગત છે. તમે ગુજરાતના કોઈપણ વિસ્તાર, ૨૦૨૬ ની સ્થિતિ અથવા પાણી બચાવવાના ઉપાયો વિશે પૂછી શકો છો."

@app.get("/api/summary")
def get_summary():
    return summary

@app.get("/api/predict")
def predict(zone: str, family_size: int, month: int):
    z = ZONE_MAP.get(zone.lower(), "Semi-Arid")
    features = pd.DataFrame({
        'zone': [z],
        'family_size': [family_size],
        'rainfall_mm': [50.0],
        'avg_temp_c': [32.0],
        'month': [month]
    })
    harvest = float(model_harvest.predict(features)[0])
    loss = float(model_loss.predict(features)[0])
    drinking_months = round(harvest / (family_size * 135 * 30), 2)
    return {
        "zone": z,
        "family_size": family_size,
        "month": month,
        "harvestable_liters": round(harvest, 1),
        "water_lost_liters": round(loss, 1),
        "months_drinking_water": drinking_months
    }

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    mode = body.get("mode", "standard")

    if mode == "deep":
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                return {"reply": "નોંધ: AI કી ઉપલબ્ધ નથી, તેથી હું સામાન્ય મોડેલનો ઉપયોગ કરી રહ્યો છું.\n\n" + _standard_reply(message)}
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-3.8-flash")
            prompt = f"""તમે 'જળશક્તિ ગુજરાત' પ્રોજેક્ટના મુખ્ય AI નિષ્ણાત છો.
તમે ગુજરાતના ૩ વિસ્તારો (કચ્છ-શુષ્ક, મધ્ય/ઉત્તર ગુજરાત-અર્ધ શુષ્ક, દક્ષિણ/દરિયાકાંઠો) ના ૮૦૦ ઘરોનો ૨૦૨૨-૨૦૨૬ નો ડેટા એનાલાઇઝ કર્યો છે.
આજે ૨૮ સપ્ટેમ્બર ૨૦૨૬ છે (૨૦૨૬ નું ચોમાસું પૂરું થવા આવ્યું છે).
તમારો મુખ્ય હેતુ પાણીનો બગાડ રોકવો અને વરસાદી પાણીનો સંચય કરવાનો છે, પાણી વાપરવા પર પ્રતિબંધ મૂકવાનો નથી.
તમારે માત્ર અને માત્ર ગુજરાતી ભાષામાં જ ટૂંકો (૨ થી ૩ વાક્યોમાં) સ્પષ્ટ અને સચોટ જવાબ આપવાનો છે.
પ્રશ્ન: {message}"""
            response = model.generate_content(prompt)
            return {"reply": response.text}
        except Exception as e:
            err = str(e)
            print("[gemini] error:", type(e).__name__, err, flush=True)  # ponytail: real error goes to console
            if "429" in err or "quota" in err.lower():
                return {"reply": "નોંધ: એલ નીનો AI સલાહકારની માંગ પૂરી થઈ ગઈ છે (ફ્રી ક્વોટા પૂરું). હું હવે સામાન્ય મોડેલનો ઉપયોગ કરીને જવાબ આપું છું.\n\n" + _standard_reply(message)}
            return {"reply": "નોંધ: AI સલાહકાર હજુ તૈયાર નથી. હું હવે સામાન્ય મોડેલનો ઉપયોગ કરીને જવાબ આપું છું.\n\n" + _standard_reply(message)}
    else:
        return {"reply": _standard_reply(message)}

# Serve static files from public/ folder
if os.path.exists(PUBLIC_DIR):
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")

try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)