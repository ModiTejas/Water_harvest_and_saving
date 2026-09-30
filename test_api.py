import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def get_json(endpoint):
    try:
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

print("=" * 60)
print("🔍 TESTING JAL SHAKTI GUJARAT BACKEND API & DATA ENFORCEMENT")
print("=" * 60)

# 1. Test /api/districts
print("\n1. Testing GET /api/districts...")
districts = get_json("/api/districts")
if isinstance(districts, list) and len(districts) > 0:
    print(f"   ✅ Successfully loaded {len(districts)} districts.")
    print("   Sample District (Valsad):", next((d for d in districts if d.get('en') == 'Valsad'), districts[0]))
else:
    print("   ❌ Error or empty list:", districts)

# 2. Test /api/summary
print("\n2. Testing GET /api/summary...")
summary = get_json("/api/summary")
for zone in ["Arid", "Semi-Arid", "Coastal"]:
    if zone in summary:
        hist_m7 = summary[zone].get("historical_monthly", {}).get("7", {})
        print(f"   📍 Zone '{zone}' (July): Rain = {hist_m7.get('rainfall_mm')} mm | Harvest = {hist_m7.get('harvestable_liters')} L | GWL = {hist_m7.get('avg_gwl_m')} m")
    else:
        print(f"   ⚠️ Zone '{zone}' missing from summary")

# 3. Test /api/district (Valsad - Coastal)
print("\n3. Testing GET /api/district?name=વલસાડ (Valsad)...")
valsad_res = get_json("/api/district?name=" + urllib.parse.quote("વલસાડ"))
if "error" not in valsad_res:
    m7 = valsad_res.get("monthly", {}).get("7", {})
    print(f"   📍 District: {valsad_res.get('name')} | Zone: {valsad_res.get('zone')} | Annual Rain Norm: {valsad_res.get('annual_rain_mm')} mm")
    print(f"      July Rain: {m7.get('rainfall_mm')} mm | Harvest: {m7.get('harvestable_liters')} L | Loss: {m7.get('water_lost_liters')} L | GWL: {m7.get('avg_gwl_m')} m")
else:
    print("   ❌ Error:", valsad_res)

# 4. Test /api/predict (July, 100 sq.m roof)
print("\n4. Testing GET /api/predict...")
predict_res = get_json("/api/predict?zone=Coastal&family_size=4&month=7&roof_m2=100&district=" + urllib.parse.quote("વલસાડ"))
print(f"   📍 Prediction Result for Valsad (100 m² roof, July):")
print(f"      Total Rain Volume: {predict_res.get('total_rain_liters')} L")
print(f"      Harvestable:       {predict_res.get('harvestable_liters')} L")
print(f"      Wasted (Loss):     {predict_res.get('water_lost_liters')} L")
print(f"      Drinking Coverage: {predict_res.get('months_drinking_water')} months")

print("\n" + "=" * 60)
print("Diagnostic test completed.")
print("=" * 60)