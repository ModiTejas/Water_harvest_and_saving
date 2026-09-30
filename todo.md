# TODO — JalShakti Gujarat UI (10-Std Science Fair)

Status legend: `[ ]` pending · `[~]` in progress · `[x]` done

## ✅ Completed (verified against code, 2026-09-29)

All items below are done and match the live code in `api/index.py` + `public/index.html`.

### Data quality
- [x] Read `summary_stats.json` shape — zones × {historical_monthly, elnino_2026_monthly} × 12 months
- [x] `avg_gwl_m` is negative (depth below surface) — rendered as positive depth via `Math.abs()` in `renderZoneCards` + `renderGWLChart`
- [x] Coastal `historical_monthly` is flat (5 mm every month) — flagged with ⚡ ડેટા ગેપ badge on zone card + chart banner, not presented as truth
- [x] `water_lost_liters` labeled "અંદાજ" (estimate) in zone cards, chart, and simulator output
- [x] Simulator fallback in `index.html` removed — line 159 falls back to `/summary_stats.json` only, no duplicated `/api/predict` logic

### UI improvements (Gujarati dashboard)
- [x] Hero: one-line "મુખ્ય સંદેશ" (`.hero-msg`) summarizing 2026 El Niño outlook
- [x] Zone cards: `harvestable_liters` (સંચય ક્ષમતા) stat present alongside rain/loss/GWL
- [x] Chart: rainfall vs loss vs harvestable as 3 datasets (rain, loss, harvest)
- [x] GWL chart: El Niño vs historical as a shaded/contrast pair (fill + borderDash), not just a toggle
- [x] Simulator: 100 m² roof example (૮૦,૦૦૦ લીટર / ~5 months drinking water) shown as static example block
- [x] Policy list: per-zone actionable cards (check dams / recharge shafts / desilting) in `.policy-grid`
- [x] Chat: quick-chip buttons (કચ્છ · દરિયાકાંઠો · એલ નીનો · બચાવવાના ઉપાયો) so users don't type
- [x] Footer: data source (GWRDC) + last-updated (૨૮-૦૯-૨૦૨૬) + model-estimate disclaimer

### AI Advisor
- [x] Standard mode: routes keyword queries (કચ્છ/દરિયા/એલ નીનો/નીતિ) to zone-specific policy answers in `_standard_reply`
- [x] Deep mode: wires Gemini only if `GEMINI_API_KEY` set; else falls back to standard with a notice
- [x] Gujarati output enforced (prompt + fallback both Gujarati-only)

### Polish
- [x] Mobile: cards/chart use `repeat(auto-fit, minmax(...))` responsive grids
- [x] Accessibility: chart `aria-label`s, button `aria-label`s on zone buttons, chips, and send button
- [x] Loading state: `#loading` banner shown while `/api/summary` fetches, cleared in `renderAll()`

## ✅ Done since last update (2026-09-29)

- [x] **Trend chart** — `public/trend.json` was unused; now rendered as a 3-line GWL chart (`renderTrendChart`, `#trendChart`) below the monthly GWL chart. Only GWL is plotted: rainfall/harvest/lost are flat synthetic values across 2023–2025, so a trend line on them would be noise. Chart title says so in Gujarati.
- [x] **`api/index.py` startup bug** — `if __name__ == "__main__":` block had no body, so `python -m uvicorn` crashed with IndentationError. Added the `uvicorn.run(...)` call back. Server now boots cleanly (verified: `/`, `/api/summary`, `/trend.json` all 200).

## ✅ Done since last update (2026-09-29)

- [x] **Human-understandable labels** — removed the `⚠️ ડેટા ગેપ` badge from the Coastal zone card; the flat 5 mm/month coastal rainfall is now shown as-is with a calm `નોંધ:` note in the chart box instead of an alarm.
- [x] **Zone cards now explain each stat** — each metric has a one-line Gujarati explanation (e.g. `સંચય ક્ષમતા` → "છત પરથી એકત્ર કરી શકાય તેવું પાણી") plus a zone-specific summary line at the bottom of the card.
- [x] **Dropdowns are now readable** — `<select>` options are emoji-prefixed (🏜️/🌾/🌊) and numbere
d (e.g. `7 — જુલાઈ`), font bumped to 1rem, native down-arrow added via CSS `appearance:none` + SVG arrow, and a hint line under each select explains what the choice does.
- [x] **Simulator output is now plain language** — each of the 3 result boxes has a bold label + a one-sentence explanation, and a green summary banner on top states what the numbers mean in one line ("આ મહિનામાં X લીટર પાણી એકત્ર કરી શકાય — તમારા N સભ્યોના પરિવાર માટે લગભág M મહિના (D દિવસ) નું પીવાનું પાણી!").

## ✅ Restructured (2026-09-29)

- [x] **Folder split** — non-useful files moved to `notuseful/` (raw CSVs, build script, generated dataset, inspection script, empty lockfile, crash dump). Live app (`api/`, `public/`) untouched.
- [x] **Build script still runs** — `notuseful/build_dataset_and_models.py` + `notuseful/inspect_files.py` updated with `notuseful/` CSV paths so they work from their new location.
- [x] **App verified live** — `/api/summary`, `/`, `/trend.json`, `/api/predict` all 200 after the move.
- [x] **README.md** — run instructions + Gemini API setup steps.

## 🔜 Next (pick one, small diffs)

- [ ] `build_dataset_and_models.py` + the 3 CSVs (1.1–1.3 GB each) are raw inputs, not served — add a README note on regenerating `summary_stats.json`
- [ ] `vercel.json` / `package-lock.json` present but no `package.json` — check what they're for before deploying
- [ ] Fair-statement copy: "10-Std Science Fair" — confirm the exact project/stage name for the footer badge

## Notes
- Stack: FastAPI (`api/index.py`) + static `public/` + Chart.js CDN. Run with `uvicorn api.index:app` or deploy as-is (Vercel-ready via `mangum`).
- Data: `summary_stats.json` is the only file served at runtime; the big CSVs are build-time inputs.