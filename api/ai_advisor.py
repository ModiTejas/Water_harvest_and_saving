from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Load .env locally if available.
# On Vercel, GEMINI_API_KEY should come from Environment Variables.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


# ============================================================
# GEMINI SDK
# ============================================================

try:
    from google import genai
    from google.genai import types
except ImportError as e:
    print(f"Gemini SDK import failed: {type(e).__name__}: {e}")
    genai = None
    types = None


client = None

if not GEMINI_API_KEY:
    print("GEMINI_API_KEY is not configured.")

elif genai is None:
    print("Gemini SDK is not available.")

else:
    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        print("Gemini client initialized successfully.")

    except Exception as e:
        print(
            "Gemini client initialization failed: "
            f"{type(e).__name__}: {e}"
        )
        client = None


# ============================================================
# MODEL FALLBACKS
# ============================================================

# Try the preferred model first.
# Older models are kept only as fallbacks.
MODEL_FALLBACKS = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


_LAST_WORKING_MODEL: str | None = None


# ============================================================
# STANDARD OFFLINE RESPONSES
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

def _standard_response(message: str) -> str | None:
    """
    Return a predefined Gujarati response when the
    question matches one of the offline keywords.
    """

    text = message.lower()

    for keyword, response in STANDARD_RESPONSES.items():

        if keyword.lower() in text:
            return response

    return None


def _is_greeting(message: str) -> bool:
    """
    Detect common greetings.
    """

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


def _get_models_to_try() -> list[str]:
    """
    Build a model list from:

    1. Last successful model
    2. Preferred fallback models
    3. Models currently exposed by the Gemini API

    This allows the application to continue working if a
    particular model is unavailable to the API project.
    """

    models: list[str] = []

    def add(model_name: str):
        if not model_name:
            return

        if model_name not in models:
            models.append(model_name)

    # Last successful model first.
    if _LAST_WORKING_MODEL:
        add(_LAST_WORKING_MODEL)

    # Preferred fallback models.
    for model_name in MODEL_FALLBACKS:
        add(model_name)

    # Discover currently available Gemini models.
    if client is not None:

        try:

            for model in client.models.list():

                name = getattr(
                    model,
                    "name",
                    None,
                )

                if not name:
                    continue

                clean_name = str(name)

                if clean_name.startswith("models/"):
                    clean_name = clean_name[
                        len("models/"):
                    ]

                lowered = clean_name.lower()

                # Only consider Gemini text/generative models.
                if (
                    "gemini" in lowered
                    and "embedding" not in lowered
                    and "image" not in lowered
                    and "veo" not in lowered
                ):
                    add(clean_name)

        except Exception as e:

            print(
                "Gemini model discovery failed: "
                f"{type(e).__name__}: {e}"
            )

    return models


def _extract_text(response: Any) -> str:
    """
    Safely extract generated text from a Gemini response.
    """

    try:

        text = getattr(
            response,
            "text",
            None,
        )

        if text:
            return str(text).strip()

    except Exception as e:

        print(
            "Gemini response text extraction failed: "
            f"{type(e).__name__}: {e}"
        )

    return ""


# ============================================================
# PUBLIC REPLY FUNCTION
# ============================================================

def reply(
    message: str,
    mode: str = "standard",
) -> str:

    global _LAST_WORKING_MODEL

    message = str(message or "").strip()

    # --------------------------------------------------------
    # Empty message
    # --------------------------------------------------------

    if not message:
        return "કૃપા કરીને તમારો પ્રશ્ન લખો."

    mode = str(
        mode or "standard"
    ).lower().strip()

    # --------------------------------------------------------
    # Greeting
    # --------------------------------------------------------

    if _is_greeting(message):

        return (
            "નમસ્તે! 💧 "
            "જળ સંચય, વરસાદી પાણી, ભૂગર્ભજળ અથવા "
            "ગુજરાતના કોઈ વિસ્તાર વિશે તમારો પ્રશ્ન પૂછો."
        )

    # --------------------------------------------------------
    # Standard / Offline Mode
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
    # Deep AI Mode — API Key / Client Check
    # --------------------------------------------------------

    if not GEMINI_API_KEY:

        print(
            "Deep AI requested, but GEMINI_API_KEY is missing."
        )

        standard = _standard_response(message)

        if standard:
            return standard

        return (
            "હાલમાં AI સેવા ઉપલબ્ધ નથી. "
            "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
        )

    if client is None:

        print(
            "Deep AI requested, but Gemini client is unavailable."
        )

        standard = _standard_response(message)

        if standard:
            return standard

        return (
            "હાલમાં AI સેવા ઉપલબ્ધ નથી. "
            "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
        )

    # --------------------------------------------------------
    # Get Models
    # --------------------------------------------------------

    models_to_try = _get_models_to_try()

    if not models_to_try:

        print("No Gemini models are available.")

        return (
            "હાલમાં AI મોડેલ ઉપલબ્ધ નથી. "
            "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
        )

    print(
        "Gemini models to try:",
        models_to_try
    )

    # --------------------------------------------------------
    # Gemini Generation
    # --------------------------------------------------------

    for model_name in models_to_try:

        try:

            # ----------------------------------------------
            # Generate content configuration
            # ----------------------------------------------

            if types is not None:

                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.4,
                    max_output_tokens=700,
                )

            else:

                config = None

            # ----------------------------------------------
            # Generate response
            # ----------------------------------------------

            if config is not None:

                response = client.models.generate_content(
                    model=model_name,
                    contents=message,
                    config=config,
                )

            else:

                response = client.models.generate_content(
                    model=model_name,
                    contents=message,
                )

            # ----------------------------------------------
            # Extract response text
            # ----------------------------------------------

            answer = _extract_text(response)

            if answer:

                _LAST_WORKING_MODEL = model_name

                print(
                    f"Gemini response successful using: "
                    f"{model_name}"
                )

                return answer

            print(
                f"Gemini returned empty response: "
                f"{model_name}"
            )

        except Exception as e:

            # IMPORTANT:
            # Do not crash FastAPI.
            # Log the actual Gemini error so it can be
            # diagnosed from Vercel Runtime Logs.

            print(
                f"Gemini model failed [{model_name}]: "
                f"{type(e).__name__}: {e}"
            )

            continue

    # --------------------------------------------------------
    # AI Failed -> Offline Fallback
    # --------------------------------------------------------

    print(
        "All Gemini models failed. "
        "Using offline fallback."
    )

    standard = _standard_response(message)

    if standard:
        return standard

    return (
        "હાલમાં AI સલાહકારનો જવાબ મળ્યો નથી. "
        "કૃપા કરીને થોડા સમય પછી ફરી પ્રયાસ કરો."
    )
