import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# ENVIRONMENT
# ============================================================

BASE = Path(__file__).resolve().parent

load_dotenv(BASE / ".env")
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


# ============================================================
# GEMINI SDK
# ============================================================

try:
    from google import genai
    from google.genai import types
except Exception as e:
    print(f"[AI] SDK import error: {type(e).__name__}: {e}")
    genai = None
    types = None


client = None

if GEMINI_API_KEY and genai is not None:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("[AI] Gemini client initialized.")
    except Exception as e:
        print(f"[AI] Gemini client initialization failed: {e}")
        client = None
else:
    if not GEMINI_API_KEY:
        print("[AI] GEMINI_API_KEY is missing.")

    if genai is None:
        print("[AI] Gemini SDK is unavailable.")


# ============================================================
# GEMINI MODEL
# ============================================================

MODEL_NAME = "gemini-flash-lite-latest"


# ============================================================
# STANDARD / OFFLINE RESPONSES
# ============================================================

STANDARD_RESPONSES = {
    "કચ્છ": (
        "🏜️ **કચ્છ જેવા શુષ્ક વિસ્તાર માટે ઉપાયો:**\n"
        "૧. **રિચાર્જ શાફ્ટ:** વરસાદી પાણીને જમીનમાં ઉતારવામાં મદદ કરે છે.\n"
        "૨. **તળાવ સંરક્ષણ:** સ્થાનિક તળાવોની સંગ્રહ ક્ષમતા જાળવવી.\n"
        "૩. **ટપક સિંચાઈ:** ખેતીમાં પાણીનો કાર્યક્ષમ ઉપયોગ કરવો."
    ),

    "દરિયાકાંઠો": (
        "🌊 **દરિયાકાંઠાના વિસ્તારો માટે ઉપાયો:**\n"
        "૧. રૂફટોપ રેઇનવોટર હાર્વેસ્ટિંગ.\n"
        "૨. સ્થાનિક વરસાદી પાણીનો સંગ્રહ.\n"
        "૩. યોગ્ય ભૂગર્ભજળ રિચાર્જ વ્યવસ્થા."
    ),

    "એલ નીનો": (
        "🌡️ **એલ નીનો અને વરસાદ:**\n"
        "એલ નીનો જેવી હવામાન પરિસ્થિતિઓ વરસાદની સ્થિતિને અસર કરી શકે છે.\n"
        "• વરસાદી પાણીનો શક્ય તેટલો સંગ્રહ કરો.\n"
        "• પાણીનો બિનજરૂરી વેડફાટ ટાળો.\n"
        "• સ્થાનિક પાણી સ્ત્રોતોની જાળવણી કરો."
    ),

    "બચાવવાના ઉપાયો": (
        "💧 **પાણી બચાવવાના સરળ ઉપાયો:**\n"
        "૧. લીકેજવાળા નળ અને પાઇપ સમયસર સુધારો.\n"
        "૨. બિનજરૂરી પાણીનો વપરાશ ટાળો.\n"
        "૩. વરસાદી પાણીનો સંગ્રહ કરો.\n"
        "૪. શક્ય હોય ત્યાં ભૂગર્ભજળ રિચાર્જ કરો."
    ),
}


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
તમે "જળશક્તિ ગુજરાત" માટે ગુજરાતી AI જળ સલાહકાર છો.

- હંમેશા સરળ અને સ્પષ્ટ ગુજરાતીમાં જવાબ આપો.
- જવાબ ટૂંકો, મુદ્દાસર અને વ્યવહારુ રાખો.
- પાણી સંચય, વરસાદી પાણી, ભૂગર્ભજળ અને પાણી બચત
  સંબંધિત સલાહ આપો.
- જરૂર હોય ત્યારે bullet points વાપરો.
- બનાવટી સરકારી આંકડા અથવા અધિકૃત દાવા ન કરો.
- ચોક્કસ આંકડો ખાતરીપૂર્વક ઉપલબ્ધ ન હોય તો તેને
  હકીકત તરીકે રજૂ ન કરો.
"""


# ============================================================
# HELPERS
# ============================================================

def _is_greeting(message: str) -> bool:
    greetings = (
        "નમસ્તે",
        "હેલો",
        "હાય",
        "hello",
        "hi",
        "hii",
        "hey",
        "namaste",
    )

    text = message.strip().lower()

    return any(
        text == greeting or text.startswith(greeting + " ")
        for greeting in greetings
    )


def _standard_response(message: str) -> str | None:
    text = message.lower()

    for keyword, response in STANDARD_RESPONSES.items():
        if keyword.lower() in text:
            return response

    return None


# ============================================================
# PUBLIC REPLY
# ============================================================

async def reply(message: str, mode: str = "standard") -> str:

    message = str(message or "").strip()

    if not message:
        return "કૃપા કરીને તમારો પ્રશ્ન લખો."

    mode = str(mode or "standard").strip().lower()

    # --------------------------------------------------------
    # GREETING
    # --------------------------------------------------------

    if _is_greeting(message):
        return (
            "નમસ્તે! 🙏 હું જળશક્તિ AI સલાહકાર છું. "
            "પાણી સંચય, વરસાદી પાણી, ભૂગર્ભજળ અથવા "
            "પાણી બચાવવા અંગે તમારો પ્રશ્ન પૂછો."
        )

    # --------------------------------------------------------
    # STANDARD MODE
    # --------------------------------------------------------

    if mode != "deep":

        standard = _standard_response(message)

        if standard:
            return standard

        return (
            "🤖 **જળશક્તિ સામાન્ય સલાહ:**\n"
            "આ પ્રશ્ન માટે ઓફલાઇન મોડમાં માહિતી મર્યાદિત છે.\n\n"
            "વધુ વિગતવાર જવાબ માટે **✨ Gemini AI** મોડ ચાલુ કરો."
        )

    # --------------------------------------------------------
    # GEMINI MODE
    # --------------------------------------------------------

    if not GEMINI_API_KEY:
        print("[AI] ERROR: GEMINI_API_KEY is missing.")
        return (
            "⚠️ Gemini AI ઉપલબ્ધ નથી કારણ કે API key મળતી નથી."
        )

    if client is None:
        print("[AI] ERROR: Gemini client is unavailable.")
        return (
            "⚠️ Gemini AI સેવા હાલમાં ઉપલબ્ધ નથી."
        )

    # --------------------------------------------------------
    # GEMINI REQUEST
    # --------------------------------------------------------

    try:

        print(
            f"[Gemini] Sending request | "
            f"model={MODEL_NAME} | mode={mode}"
        )

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            max_output_tokens=700,
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=message,
            config=config,
        )

        answer = getattr(response, "text", None)

        if answer:
            answer = str(answer).strip()

            print(
                f"[Gemini] Success | model={MODEL_NAME}"
            )

            return answer

        print("[Gemini] Empty response.")

        return (
            "⚠️ Gemini તરફથી ખાલી જવાબ મળ્યો. "
            "કૃપા કરીને ફરી પ્રયાસ કરો."
        )

    except Exception as e:

        print(
            f"[Gemini] ERROR | "
            f"{type(e).__name__}: {e}"
        )

        # IMPORTANT:
        # Do NOT silently return an offline answer here.
        # This makes Gemini failures visible during testing.

        return (
            "⚠️ Gemini AI સાથે જોડાણમાં સમસ્યા આવી છે. "
            "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
        )
