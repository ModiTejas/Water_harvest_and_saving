import pandas as pd

files = [
    'notuseful/temprature_tel_hr_gujarat_sw_gw_gj_2021_2025.csv',
    'notuseful/gwl_tel_6_hourly_gujarat_sw_gw_gj_2021_2025.csv',
    'notuseful/rainfall_manual_daily_gujarat_sw_gw_gj_2021_2025.csv'
]

for f in files:
    try:
        df = pd.read_csv(f, nrows=2)
        print(f"\n{'='*20}\nFILE: {f}\nCOLUMNS:")
        print(df.columns.tolist())
        print("\nSAMPLE ROW:")
        print(df.iloc[0].to_dict())
    except Exception as e:
        print(f"\nERROR on {f}: {e}")