import pandas as pd
import numpy as np
import joblib
import json
import os

print("=== 1/4: Processing Real Government Climate & GWL CSVs ===")

ZONE_MAP = {
    'Kachchh': 'Arid', 'Kutch': 'Arid', 'Banaskantha': 'Arid', 'Patan': 'Arid', 'Surendranagar': 'Arid',
    'Rajkot': 'Semi-Arid', 'Ahmedabad': 'Semi-Arid', 'Bhavnagar': 'Semi-Arid', 'Junagadh': 'Semi-Arid',
    'Jamnagar': 'Semi-Arid', 'Amreli': 'Semi-Arid', 'Gandhinagar': 'Semi-Arid', 'Sabarkantha': 'Semi-Arid',
    'Mahesana': 'Semi-Arid', 'Mehsana': 'Semi-Arid', 'Botad': 'Semi-Arid', 'Morbi': 'Semi-Arid',
    'Kheda': 'Semi-Arid', 'Mahisagar': 'Semi-Arid', 'Aravalli': 'Semi-Arid',
    'Surat': 'Coastal', 'Navsari': 'Coastal', 'Valsad': 'Coastal', 'Bharuch': 'Coastal',
    'Tapi': 'Coastal', 'Dang': 'Coastal', 'The Dangs': 'Coastal', 'Narmada': 'Coastal',
    'Anand': 'Coastal', 'Vadodara': 'Coastal', 'Panch Mahals': 'Coastal', 'Panchmahal': 'Coastal',
    'Dahod': 'Coastal', 'Gir Somnath': 'Coastal', 'Porbandar': 'Coastal', 'Devbhumi Dwarka': 'Coastal',
    'Chhotaudepur': 'Coastal'
}

def clean_district(name):
    if pd.isna(name):
        return 'Semi-Arid'
    name_clean = str(name).strip().title()
    for k, v in ZONE_MAP.items():
        if k.lower() in name_clean.lower():
            return v
    return 'Semi-Arid'

# 1. Process Temperature
print("Extracting Temperature data...")
temp_chunks = pd.read_csv(
    'notuseful/temprature_tel_hr_gujarat_sw_gw_gj_2021_2025.csv',
    chunksize=300000,
    usecols=['District', 'Data Acquisition Time', 'Air Temperature Telemetry Hourly (ºC)']
)
temp_records = []
for chunk in temp_chunks:
    chunk['val'] = pd.to_numeric(chunk['Air Temperature Telemetry Hourly (ºC)'], errors='coerce')
    chunk = chunk.dropna(subset=['val'])
    chunk['zone'] = chunk['District'].apply(clean_district)
    chunk['date'] = pd.to_datetime(chunk['Data Acquisition Time'], format='%d-%m-%Y %H:%M', errors='coerce')
    chunk = chunk.dropna(subset=['date'])
    chunk['year'] = chunk['date'].dt.year
    chunk['month'] = chunk['date'].dt.month
    chunk = chunk[chunk['year'].between(2022, 2025)]
    agg = chunk.groupby(['zone', 'year', 'month'])['val'].agg(['mean', 'count']).reset_index()
    temp_records.append(agg)

temp_df = pd.concat(temp_records).groupby(['zone', 'year', 'month']).apply(
    lambda x: (x['mean'] * x['count']).sum() / x['count'].sum()
).reset_index(name='avg_temp_c')

# 2. Process GWL
print("Extracting Groundwater Level data...")
gwl_chunks = pd.read_csv(
    'notuseful/gwl_tel_6_hourly_gujarat_sw_gw_gj_2021_2025.csv',
    chunksize=300000,
    usecols=['District', 'Data Acquisition Time', 'Groundwater Level Telemetry 6 Hourly (meter)']
)
gwl_records = []
for chunk in gwl_chunks:
    chunk['val'] = pd.to_numeric(chunk['Groundwater Level Telemetry 6 Hourly (meter)'], errors='coerce')
    chunk = chunk.dropna(subset=['val'])
    chunk['zone'] = chunk['District'].apply(clean_district)
    chunk['date'] = pd.to_datetime(chunk['Data Acquisition Time'], format='%d-%m-%Y %H:%M', errors='coerce')
    chunk = chunk.dropna(subset=['date'])
    chunk['year'] = chunk['date'].dt.year
    chunk['month'] = chunk['date'].dt.month
    chunk = chunk[chunk['year'].between(2022, 2025)]
    agg = chunk.groupby(['zone', 'year', 'month'])['val'].agg(['mean', 'count']).reset_index()
    gwl_records.append(agg)

gwl_df = pd.concat(gwl_records).groupby(['zone', 'year', 'month']).apply(
    lambda x: (x['mean'] * x['count']).sum() / x['count'].sum()
).reset_index(name='avg_gwl_m')

# 3. Process Rainfall
print("Extracting Rainfall data...")
rain_chunks = pd.read_csv(
    'notuseful/rainfall_manual_daily_gujarat_sw_gw_gj_2021_2025.csv',
    chunksize=300000,
    usecols=['District', 'Data Acquisition Time', 'Manual Daily Rainfall (mm)']
)
rain_records = []
for chunk in rain_chunks:
    chunk['val'] = pd.to_numeric(chunk['Manual Daily Rainfall (mm)'], errors='coerce').fillna(0)
    chunk['zone'] = chunk['District'].apply(clean_district)
    chunk['date'] = pd.to_datetime(chunk['Data Acquisition Time'], format='%d-%m-%Y %H:%M', errors='coerce')
    chunk = chunk.dropna(subset=['date'])
    chunk['year'] = chunk['date'].dt.year
    chunk['month'] = chunk['date'].dt.month
    chunk = chunk[chunk['year'].between(2022, 2025)]
    agg = chunk.groupby(['zone', 'year', 'month', 'District'])['val'].sum().reset_index()
    rain_records.append(agg)

rain_df = pd.concat(rain_records).groupby(['zone', 'year', 'month'])['val'].mean().reset_index(name='rainfall_mm')

# Merge climate data
climate = pd.merge(rain_df, temp_df, on=['zone', 'year', 'month'], how='outer')
climate = pd.merge(climate, gwl_df, on=['zone', 'year', 'month'], how='outer')
climate['rainfall_mm'] = climate['rainfall_mm'].fillna(5.0)
climate['avg_temp_c'] = climate['avg_temp_c'].fillna(30.0)
climate['avg_gwl_m'] = climate['avg_gwl_m'].fillna(-15.0)

print(f"Clean Climate Grid Created: {len(climate)} zone-months.")

# === 2/4: Generate 800 Survey-Feasible Household Profiles ===
print("\n=== 2/4: Generating 800 Household Profiles ===")
np.random.seed(42)

houses = []
for hid in range(1, 801):
    zone = np.random.choice(['Arid', 'Semi-Arid', 'Coastal'], p=[0.30, 0.45, 0.25])
    family_size = np.random.choice([2, 3, 4, 5, 6, 7], p=[0.10, 0.20, 0.35, 0.20, 0.10, 0.05])
    soil_type = {'Arid': 'Sandy', 'Semi-Arid': 'Loam', 'Coastal': 'Clay'}[zone]
    has_harvesting = np.random.choice([0, 1], p=[0.75, 0.25])
    
    # Catchment area automatically derived from family size (CPHEEO standard)
    derived_catchment_sqm = (family_size * 20) + 40
    
    houses.append({
        'house_id': hid,
        'zone': zone,
        'family_size': family_size,
        'catchment_sqm': derived_catchment_sqm,
        'soil_type': soil_type,
        'has_harvesting': has_harvesting
    })

houses_df = pd.DataFrame(houses)

dataset_rows = []
for _, house in houses_df.iterrows():
    h_climate = climate[climate['zone'] == house['zone']]
    for _, c in h_climate.iterrows():
        temp_factor = 1.0 + max(0, (c['avg_temp_c'] - 30) * 0.02)
        monthly_demand = house['family_size'] * 135 * 30 * temp_factor
        
        # 1 mm rain on 1 sqm = 1 Liter; runoff coefficient = 0.85
        harvestable_liters = house['catchment_sqm'] * c['rainfall_mm'] * 0.85
        
        if house['has_harvesting'] == 1:
            saved_liters = min(harvestable_liters, 15000)
            lost_liters = max(0, harvestable_liters - saved_liters)
        else:
            saved_liters = 0
            lost_liters = harvestable_liters
            
        soil_mult = {'Sandy': 1.2, 'Loam': 1.0, 'Clay': 0.6}[house['soil_type']]
        recharge_score = min(100, (c['rainfall_mm'] * 0.2) * soil_mult)

        dataset_rows.append({
            'house_id': house['house_id'],
            'zone': house['zone'],
            'family_size': house['family_size'],
            'soil_type': house['soil_type'],
            'has_harvesting': house['has_harvesting'],
            'year': int(c['year']),
            'month': int(c['month']),
            'rainfall_mm': round(c['rainfall_mm'], 2),
            'avg_temp_c': round(c['avg_temp_c'], 2),
            'avg_gwl_m': round(c['avg_gwl_m'], 2),
            'monthly_demand_liters': round(monthly_demand, 1),
            'harvestable_liters': round(harvestable_liters, 1),
            'water_lost_liters': round(lost_liters, 1),
            'recharge_score': round(recharge_score, 1)
        })

full_df = pd.DataFrame(dataset_rows)
full_df.to_csv('notuseful/gujarat_household_water_master.csv', index=False)
print(f"Generated {len(full_df)} records saved to 'notuseful/gujarat_household_water_master.csv'.")

# === 3/4: Train Machine Learning Models ===
print("\n=== 3/4: Training ML Models ===")
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

features = ['zone', 'family_size', 'rainfall_mm', 'avg_temp_c', 'month']
X = full_df[features]
y_harvest = full_df['harvestable_liters']
y_loss = full_df['water_lost_liters']

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(drop='first'), ['zone'])
    ],
    remainder='passthrough'
)

model_harvest = Pipeline(steps=[
    ('prep', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=60, random_state=42))
])
model_harvest.fit(X, y_harvest)

model_loss = Pipeline(steps=[
    ('prep', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=60, random_state=42))
])
model_loss.fit(X, y_loss)

os.makedirs('backend_models', exist_ok=True)
joblib.dump(model_harvest, 'api/harvest_model.pkl')
joblib.dump(model_loss, 'api/loss_model.pkl')
print("Trained and saved ML pipelines to 'api/'.")

# === 4/4: Summary Stats & El Niño 2026 Simulation ===
print("\n=== 4/4: Generating Summary Stats & 2026 El Niño Projections ===")
summary = {}

for z in ['Arid', 'Semi-Arid', 'Coastal']:
    z_data = full_df[full_df['zone'] == z]
    monthly_avg = z_data.groupby('month')[['rainfall_mm', 'harvestable_liters', 'water_lost_liters', 'avg_gwl_m']].mean().to_dict(orient='index')
    
    elnino_monthly = {}
    for m, vals in monthly_avg.items():
        rain = vals['rainfall_mm'] * 0.78 if m in [6, 7, 8, 9] else vals['rainfall_mm']
        lost = vals['water_lost_liters'] * 0.78
        elnino_monthly[m] = {
            'rainfall_mm': round(rain, 1),
            'harvestable_liters': round(vals['harvestable_liters'] * 0.78, 1),
            'water_lost_liters': round(lost, 1),
            'avg_gwl_m': round(vals['avg_gwl_m'] - 1.2, 2)
        }
    
    summary[z] = {
        'historical_monthly': monthly_avg,
        'elnino_2026_monthly': elnino_monthly
    }

with open('summary_stats.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("All pipeline operations completed successfully!")