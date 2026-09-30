import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Robust Environment Loading
BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")
load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY and genai:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logging.error(f"Gemini client initialization failed: {e}")

# Global cache to reuse the last verified model instantly
_LAST_WORKING_MODEL = None

MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
]

STANDARD_RESPONSES = {
    "કચ્છ": "🏜️ **શુષ્ક વિસ્તાર (કચ્છ/ઉત્તર ગુજરાત) માટે ઉપાયો:**\n"
            "૧. **બોરવેલ રિચાર્જ શાફ્ટ:** વરસાદી પાણીને સીધું જમીનમાં ઉતારી ભૂગર્ભ જળ વધારવું.\n"
            "૨. **તળાવો ઊંડા કરવા:** ગામના સ્થાનિક તળાવોની ક્ષમતા વધારવી જેથી સિંચાઈ માટે પાણી સચવાય.\n"
            "૩. **ટપક પદ્ધતિ:** ખેતીમાં ટપક અને ફુવારા પદ્ધતિનો ઉપયોગ કરી ૫૦% પાણી બચાવવું.",

    "દરિયાકાંઠો": "🌊 **દરિયાકાંઠાના વિસ્તાર (દક્ષિણ ગુજરાત) માટે ઉપાયો:**\n"
                 "૧. **રૂફટોપ રેઇન વોટર હાર્વેસ્ટિંગ:** ૧૦૦ ચો.મી. ની છત પરથી વર્ષે ૮૦,૦૦૦ લીટર પાણી એકઠું કરી શકાય.\n"
                 "૨. **ખારાશ અટકાવવી:** તટીય વિસ્તારોમાં ચેકડેમ બનાવી મીઠા પાણીને દરિયામાં વહી જતું રોકવું.\n"
                 "૩. **ચોમાસાના વહેણનું વ્યવસ્થાપન:** વધારાના વહી જતા પાણીને ટાંકાઓ કે કૂવાઓ દ્વારા સ્ટોર કરવું.",

    "એલ નીનો": "🌡️ **એલ નીનો ૨૦૨૬ ની ગુજરાત પર અસર:**\n"
               "આ વર્ષે એલ નીનો સક્રિય હોવાથી સરેરાશ વરસાદમાં ૨૨% સુધીનો ઘટાડો થવાની સંભાવના છે.\n"
               "• ઓગસ્ટ અને સપ્ટેમ્બરના વરસાદી પાણીનો ટીપે-ટીપો સંગ્રહ કરવો.\n"
               "• વાવ, તળાવો અને કૂવાનું જાળવણી કામ અત્યારથી જ પૂરું કરવું.\n"
               "• બિનજરૂરી પાણીનો વેડફાટ તાત્કાલિક બંધ કરવો.",

    "બચાવવાના ઉપાયો": "💧 **પાણી બચાવવાના સરળ ઉપાયો:**\n"
                       "૧. **ઘર સ્તરે:** વાસણ ધોવા કે નાહવા માટે વહેતા નળને બદલે ડોલનો ઉપયોગ કરવો.\n"
                       "૨. **RO વેસ્ટ વોટર:** RO સિસ્ટમમાંથી નીકળતા વેસ્ટ પાણીનો પોતાં કરવા કે છોડમાં ઉપયોગ કરવો.\n"
                       "૩. **સોસાયટી સ્તરે:** સમગ્ર સોસાયટીની છતનું પાણી ભેગું કરીને કોમન રિચાર્જ બોર બનાવો.",
}

SYSTEM_INSTRUCTION = """
તમે "જળશક્તિ ગુજરાત" ના AI જળ સલાહકાર છો.

નિયમો:
- હંમેશા સરળ અને સ્પષ્ટ ગુજરાતીમાં જવાબ આપો.
- જવાબ ટૂંકો, મુદ્દાસર અને વ્યવહારુ રાખો.
- જળ સંચય, વરસાદી પાણી, ભૂગર્ભ જળ, કચ્છ, સૌરાષ્ટ્ર, મધ્ય ગુજરાત, દક્ષિણ ગુજરાત અને એલ નીનો સંબંધિત સલાહ આપો.
- બુલેટ પોઇન્ટ અને **બોલ્ડ** શબ્દોનો ઉપયોગ કરી શકો છો.
- ખોટા આંકડા કે અચોક્કસ સરકારી દાવા ન કરો.
"""

def _get_models_to_try():
    """Builds unique priority list starting with the last working model."""
    global _LAST_WORKING_MODEL
    to_try = []
    if _LAST_WORKING_MODEL:
        to_try.append(_LAST_WORKING_MODEL)
    to_try.extend(MODEL_FALLBACKS)

    # Dynamically inject available models from API list if accessible
    if client:
        try:
            for m in client.models.list():
                name = m.name.replace("models/", "")
                if "gemini" in name and "embed" not in name and "image" not in name:
                    if name not in to_try:
                        to_try.append(name)
        except Exception:
            pass

    # Deduplicate matching preserves ordering
    seen, uniq = set(), []
    for x in to_try:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

async def reply(message: str, mode: str) -> str:
    global _LAST_WORKING_MODEL
    msg_clean = message.strip()
    if not msg_clean:
        return "કૃપા કરીને તમારો પ્રશ્ન લખો."

    low = msg_clean.lower()
    if low in ["hi", "hii", "hello", "hey", "નમસ્તે", "હાય"]:
        return "નમસ્તે! 🙏 હું જળશક્તિ AI સલાહકાર છું. કચ્છ, દરિયાકાંઠો, એલ નીનો કે પાણી બચાવવાના ઉપાયો વિશે પૂછો."

    # --- 1. STANDARD MODE (Offline, Fast, Keyword Match) ---
    if mode == "standard" or not client:
        for key, response in STANDARD_RESPONSES.items():
            if key in msg_clean:
                return response
        return (
            "🤖 **જળશક્તિ સામાન્ય સલાહ:**\n"
            "તમારા આ પ્રશ્ન માટે ઓફલાઇન મોડમાં માહિતી મર્યાદિત છે.\n\n"
            "**સૂચન:** સચોટ માહિતી માટે ઉપર આપેલ **'ઊંડાણપૂર્વક વિશ્લેષણ (AI)'** ઓપ્શન ચાલુ કરો."
        )

    # --- 2. DEEP MODE (Online, Gemini API with Auto-Fallback) ---
    models_to_try = _get_models_to_try()
    errors = []

    for model_name in models_to_try:
        try:
            print(f"[Gemini] Trying model: {model_name}")

            response = client.models.generate_content(
                model=model_name,
                contents=msg_clean,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.4,
                    max_output_tokens=700,
                ),
            )

            answer = (response.text or "").strip()
            if answer:
                _LAST_WORKING_MODEL = model_name
                print(f"[Gemini] Success with: {model_name}")
                return answer

            errors.append(f"{model_name}: Empty response")

        except Exception as error:
            error_text = f"{type(error).__name__}: {error}"
            errors.append(f"{model_name}: {error_text}")
            print(f"[Gemini] Failed - {model_name}: {error_text}")
            continue

    # All API model attempts failed -> Log to stdout and Fallback to offline standard responses
    print("[Gemini] All fallback models failed:")
    for err in errors:
        print(f"  - {err}")

    for key, response in STANDARD_RESPONSES.items():
        if key in msg_clean:
            return f"⚠️ API કનેક્શન નબળું છે. ઓફલાઇન જવાબ:\n\n{response}"

    return "⚠️ અત્યારે તમામ AI સર્વર્સ વ્યસ્ત છે. કૃપા કરીને 'સામાન્ય મોડેલ' પસંદ કરો."
