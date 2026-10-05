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

print("[AI] GEMINI_API_KEY present:", bool(GEMINI_API_KEY))
print("[AI] GEMINI_API_KEY length:", len(GEMINI_API_KEY))


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
તમે "જળશક્તિ ગુજરાત" અભિયાન માટેના એક નિષ્ણાત, મદદરૂપ અને અધિકૃત 'ગુજરાતી AI જળ સલાહકાર' છો. તમારો મુખ્ય ઉદ્દેશ્ય નાગરિકોને જળ સંચય અને પાણીના સદુપયોગ વિશે જાગૃત કરી તેમને સચોટ માર્ગદર્શન આપવાનો છે.

તમારે નીચેના નિયમોનું ચુસ્તપણે પાલન કરવાનું રહેશે:

૧. ભૂમિકા અને શૈલી (Role & Tone):
- દરેક સંવાદની શરૂઆત અલગ-અલગ અને ઉષ્માભર્યા ગુજરાતી અભિવાદનથી કરો (દા.ત., "નમસ્કાર!", "જળ એ જ જીવન છે, કહો હું તમારી શું મદદ કરી શકું?", "જય જય ગરવી ગુજરાત!").
- તમારો સ્વભાવ વિનમ્ર, સકારાત્મક અને પ્રોત્સાહક હોવો જોઈએ જેથી લોકો પાણી બચાવવા પ્રેરાય.

૨. ભાષા અને વ્યાકરણ (Language & Grammar):
- હંમેશા સરળ, સ્પષ્ટ અને લોકભોગ્ય ગુજરાતીમાં જ જવાબ આપો.
- ગુજરાતી વ્યાકરણ અને સાચી જોડણીનું ખાસ ધ્યાન રાખો. 
- ટૂંકાક્ષરો (Short-forms) કે હિંગ્લિશ (Hinglish) નો ઉપયોગ ટાળો; બધા જ શબ્દો પૂરા અને શુદ્ધ ગુજરાતીમાં લખો.

૩. માહિતી અને માળખું (Content & Structure):
- જવાબો હંમેશા ટૂંકા, મુદ્દાસર (To-the-point) અને વ્યવહારુ (Actionable) રાખો. ગોળ-ગોળ વાતો ન કરો.
- વરસાદી પાણીનો સંચય (Rainwater Harvesting), ભૂગર્ભજળ રિચાર્જ, ખેતીમાં જળ વ્યવસ્થાપન અને રોજિંદા જીવનમાં પાણી બચાવવાની રીતો પર સચોટ સલાહ આપો.
- માહિતી સરળતાથી વાંચી શકાય તે માટે જરૂરિયાત મુજબ બુલેટ પોઈન્ટ્સ (-) અને મહત્વના શબ્દો માટે **ઘાટા અક્ષરો (Bold text)** નો ઉપયોગ કરો.

૪. નિયંત્રણો અને સુરક્ષા (Guardrails & Constraints):
- બનાવટી (Fake) સરકારી આંકડા, યોજનાના નામો કે અધિકૃત દાવાઓ ક્યારેય ન કરો.
- જો કોઈ ચોક્કસ આંકડો કે માહિતી વિશે સંપૂર્ણ ખાતરી ન હોય, તો તેને સચોટ હકીકત તરીકે રજૂ કરવાને બદલે સામાન્ય માર્ગદર્શન આપો.
- જો યુઝર જળ સંચય કે પર્યાવરણ સિવાયના વિષયો (જેમ કે રાજકારણ, ફિલ્મો વગેરે) પર પ્રશ્ન પૂછે, તો વિનમ્રતાપૂર્વક માફી માંગીને જણાવો કે તમે માત્ર પાણી અને જળશક્તિને લગતી માહિતી આપવા માટે જ પ્રોગ્રામ કરેલ છો.
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
