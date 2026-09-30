# જળશક્તિ ગુજરાત — Run + AI setup

## Run the app
```bash
cd "E:\MY LLM\gpt\Water project"
uvicorn api.index:app --host 127.0.0.1 --port 8000
```
Then open http://127.0.0.1:8000 .

## Connect Gemini (AI advisor)
The deep mode in `api/index.py` already calls Gemini — it just needs the key.

1. Get a free key: https://aistudio.google.com/apikey
2. Edit `.env` in the project folder and paste your key:
   ```
   GEMINI_API_KEY=your_key_here
   ```
   (The server loads `.env` automatically via `python-dotenv`. No terminal env vars needed.)
3. Restart the server, then toggle **"ઊંડાણપૂર્વક વિશ્લેષણ (AI)"** ON in the chat box and ask a question in Gujarati.

If the key is missing, the app falls back to the rule-based standard mode and says so in the reply.

## Folder layout
- `api/` — FastAPI app + ML models (live)
- `public/` — website (live)
- `notuseful/` — raw CSVs, build scripts, generated dataset (build-time only, not served)