from pathlib import Path
import re, numpy as np, pandas as pd


df = pd.read_csv('/content/TiAl_Ball_Milling_imputed_dataset.csv')
print(df)

df = pd.read_csv('/content/TiAl_Ball_Milling_imputed_dataset.csv')
def parse_bpr(value):
    if pd.isna(value): return np.nan
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*:\s*1\s*$", str(value))
    return float(m.group(1)) if m else np.nan
df["bpr"] = df["bpr_reported"].map(parse_bpr)
# 0. Function to transform minutes to hours
def min_to_hours(minutes):
    """Convert time in minutes to hours."""
    return minutes / 60.0
df["time_h"] = df["Time"].apply(min_to_hours)
# Features
df["impact"]      = df["rpm"] * df["Time"]
df["log_time"]    = np.log1p(df["Time"])
df["intensity"]   = (df["rpm"] * df["Time"]) / df["bpr"]
df["milling_rate"]= df["rpm"] / df["Time"].replace(0, np.nan)

# Drop any existing *generated* mill_ dummy columns to avoid duplicates if the cell is run multiple times
existing_generated_mill_cols = [col for col in df.columns if col.startswith('mill_') and col != 'mill_type']
if existing_generated_mill_cols:
    df = df.drop(columns=existing_generated_mill_cols)

mill_dummies = pd.get_dummies(df["mill_type"], prefix="mill", dtype=int)
df = pd.concat([df, mill_dummies], axis=1)
df["hardness_strength_ratio"] = df["hardness_hv"] / df["strength_hv"].replace(0, np.nan)
MILL_DUMMIES = list(set([c for c in df.columns if c.startswith("mill_") and c != "mill_type"]))
EXPORT_COLS = (
    ["sample_name", "mill_type", "rpm", "time_h", "bpr"] + 
    ["impact", "log_time", "intensity", "milling_rate"] +
    MILL_DUMMIES +
    ["hardness_hv", "strength_hv"] 
)
EXPORT_COLS = [c for c in EXPORT_COLS if c in df.columns]

OUTPUT_PATH = '/content/Features_dataset.csv'
df_out = df[EXPORT_COLS].round(4)
df_out.to_csv(OUTPUT_PATH, index=False, na_rep="NA")
print(f"Shape: {df_out.shape[0]} rows x {df_out.shape[1]} columns")
print(f"Columns: {df_out.columns.tolist()}")
print(df_out[["sample_name", "time_h", "rpm", "impact", "hardness_hv"]].head(5).to_string())
