from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

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
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )
        print("[AI] Gemini client initialized.")
    except Exception as e:
        print(
            f"[AI] Gemini client error: "
            f"{type(e).__name__}: {e}"
        )
        client = None
else:
    if not GEMINI_API_KEY:
        print("[AI] GEMINI_API_KEY is missing.")

    if genai is None:
        print("[AI] Gemini SDK is unavailable.")


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "gemini-flash-lite-latest"


# ============================================================
# OFFLINE RESPONSES
# ============================================================

STANDARD_RESPONSES = {
    "કચ્છ": (
        "કચ્છ જેવા શુષ્ક વિસ્તારમાં વરસાદી પાણીનો સંગ્રહ, "
        "છત પરથી રેઇનવોટર હાર્વેસ્ટિંગ અને ભૂગર્ભજળ રિચાર્જ "
        "માટે રિચાર્જ શાફ્ટ ઉપયોગી ઉપાયો છે."
    ),

    "દરિયાકાંઠો": (
        "દરિયાકાંઠાના વિસ્તારોમાં વરસાદી પાણીનો સ્થાનિક સંગ્રહ "
        "અને યોગ્ય રિચાર્જ વ્યવસ્થા ભૂગર્ભજળ પરનો દબાણ ઘટાડવામાં "
        "મદદ કરી શકે છે."
    ),

    "એલ નીનો": (
        "એલ નીનોની સ્થિતિમાં વરસાદ ઓછો રહેવાની શક્યતા હોય ત્યારે "
        "વરસાદી પાણીનો સંગ્રહ અને પાણીનો કાર્યક્ષમ ઉપયોગ વધુ "
        "મહત્વનો બને છે."
    ),

    "બચાવવાના ઉપાયો": (
        "છત પરથી વરસાદી પાણી એકત્ર કરો, લીકેજ સુધારો, "
        "પાણીનો બિનજરૂરી વપરાશ ટાળો અને શક્ય હોય ત્યાં "
        "ભૂગર્ભજળ રિચાર્જની વ્યવસ્થા કરો."
    ),
}


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
તમે 'જળશક્તિ ગુજરાત' માટે ગુજરાતી ભાષામાં પાણી સલાહકાર છો.

તમારું કામ ગુજરાતના નાગરિકોને પાણી સંચય અને પાણી વ્યવસ્થાપન અંગે
સરળ, ટૂંકી અને વ્યવહારુ માહિતી આપવાનું છે.

મુખ્ય વિષયો:
- વરસાદી પાણીનું સંચય
- Rooftop Rainwater Harvesting
- ભૂગર્ભજળ રિચાર્જ
- પાણી બચત
- કચ્છ અને સૌરાષ્ટ્ર
- મધ્ય ગુજરાત
- દક્ષિણ ગુજરાત
- દરિયાકાંઠાના વિસ્તાર
- એલ નીનો અને વરસાદી પરિસ્થિતિ
- ઘરેલુ પાણી વ્યવસ્થાપન

નિયમો:
1. જવાબ મુખ્યત્વે ગુજરાતીમાં આપો.
2. સરળ અને સામાન્ય માણસને સમજાય તેવી ભાષા વાપરો.
3. વ્યવહારુ ઉપાયો આપો.
4. ખોટા અથવા બનાવટી સરકારી આંકડા ન આપો.
5. કોઈ ચોક્કસ સરકારી યોજના, આંકડો અથવા અધિકૃત દાવો
   ખાતરી વિના રજૂ ન કરો.
6. ખૂબ લાંબા જવાબો ટાળો.
7. જરૂરી હોય ત્યારે bullet points વાપરો.
8. પાણીની ગુણવત્તા અથવા આરોગ્ય સંબંધિત બાબતોમાં
   સલામતી અંગે યોગ્ય ચેતવણી આપો.
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
        "hey",
        "namaste",
    )

    text = message.strip().lower()

    return any(
        greeting in text
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

def reply(
    message: str,
    mode: str = "standard",
) -> str:

    message = str(message or "").strip()

    if not message:
        return "કૃપા કરીને તમારો પ્રશ્ન લખો."

    mode = str(
        mode or "standard"
    ).strip().lower()


    # --------------------------------------------------------
    # GREETING
    # --------------------------------------------------------

    if _is_greeting(message):

        return (
            "નમસ્તે! 💧 "
            "જળ સંચય, વરસાદી પાણી, ભૂગર્ભજળ અથવા "
            "ગુજરાતના કોઈ વિસ્તાર વિશે તમારો પ્રશ્ન પૂછો."
        )


    # --------------------------------------------------------
    # STANDARD MODE
    # --------------------------------------------------------

    if mode != "deep":

        standard = _standard_response(message)

        if standard:
            return standard

        return (
            "વરસાદી પાણીનો સંગ્રહ, છત પરથી રેઇનવોટર "
            "હાર્વેસ્ટિંગ અને ભૂગર્ભજળ રિચાર્જ પાણી સંચયના "
            "મહત્વપૂર્ણ ઉપાયો છે. વધુ ચોક્કસ સલાહ માટે "
            "'ઊંડાણપૂર્વક (AI)' મોડ પસંદ કરો."
        )


    # --------------------------------------------------------
    # DEEP MODE — API KEY CHECK
    # --------------------------------------------------------

    if not GEMINI_API_KEY:

        print("[AI] ERROR: GEMINI_API_KEY is empty.")

        return (
            "હાલમાં AI સેવા ઉપલબ્ધ નથી. "
            "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
        )


    # --------------------------------------------------------
    # DEEP MODE — CLIENT CHECK
    # --------------------------------------------------------

    if client is None:

        print("[AI] ERROR: Gemini client is None.")

        return (
            "હાલમાં AI સેવા ઉપલબ્ધ નથી. "
            "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
        )


    # --------------------------------------------------------
    # GEMINI REQUEST
    # --------------------------------------------------------

    try:

        print(
            f"[AI] Sending request to {MODEL_NAME}"
        )

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            thinking_config=types.ThinkingConfig(
                thinking_level="low"
            ),
            max_output_tokens=700,
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=message,
            config=config,
        )

        answer = getattr(
            response,
            "text",
            None
        )

        if answer:

            answer = str(answer).strip()

            print("[AI] Gemini response received.")

            return answer


        print("[AI] Gemini returned an empty response.")

        return (
            "AI તરફથી ખાલી જવાબ મળ્યો. "
            "કૃપા કરીને ફરી પ્રયાસ કરો."
        )


    except Exception as e:

        print(
            "[AI] GEMINI ERROR: "
            f"{type(e).__name__}: {e}"
        )

        standard = _standard_response(message)

        if standard:
            return standard

        return (
            "હાલમાં AI સલાહકારનો જવાબ મળ્યો નથી. "
            "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
        )
