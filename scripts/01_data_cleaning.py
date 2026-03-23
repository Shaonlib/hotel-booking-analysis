"""
01_data_cleaning.py
────────────────────────────────────────────────────────────
Loads the raw hotel_bookings.csv, cleans nulls, removes
invalid records, engineers key features, and exports
hotel_bookings_clean.csv for downstream analysis.
────────────────────────────────────────────────────────────
"""

import pandas as pd
import numpy as np

# ── 1. Load ───────────────────────────────────────────────
RAW_PATH   = "data/hotel_bookings.csv"
CLEAN_PATH = "data/hotel_bookings_clean.csv"

df = pd.read_csv(RAW_PATH)
print(f"Loaded  : {df.shape[0]:,} rows × {df.shape[1]} columns")

# ── 2. Fix nulls ──────────────────────────────────────────
df["children"] = df["children"].fillna(0).astype(int)
df["country"]  = df["country"].fillna("Unknown")
df["agent"]    = df["agent"].fillna(0).astype(int)
df["company"]  = df["company"].fillna(0).astype(int)

# ── 3. Remove invalid records ─────────────────────────────
# Drop negative / extreme ADR outliers
df = df[(df["adr"] >= 0) & (df["adr"] <= 1000)]

# Drop bookings with zero guests
df = df[(df["adults"] + df["children"] + df["babies"]) > 0]

print(f"Cleaned : {df.shape[0]:,} rows remain")

# ── 4. Feature engineering ────────────────────────────────
MONTH_ORDER = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]

df["arrival_date_month"] = pd.Categorical(
    df["arrival_date_month"], categories=MONTH_ORDER, ordered=True
)

df["total_nights"]  = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
df["total_revenue"] = df["adr"] * df["total_nights"]
df["total_guests"]  = df["adults"] + df["children"] + df["babies"]
df["room_match"]    = (df["reserved_room_type"] == df["assigned_room_type"]).astype(int)

df["arrival_date"] = pd.to_datetime(
    df["arrival_date_year"].astype(str) + "-" +
    df["arrival_date_month"].astype(str) + "-" +
    df["arrival_date_day_of_month"].astype(str),
    format="%Y-%B-%d", errors="coerce"
)
df["arrival_yearmon"] = df["arrival_date"].dt.to_period("M")

# ── 5. Export ─────────────────────────────────────────────
df.to_csv(CLEAN_PATH, index=False)
print(f"Exported: {CLEAN_PATH}")

# ── 6. Summary ────────────────────────────────────────────
confirmed = df[df["is_canceled"] == 0]
print("\n── Quick Stats ──────────────────────────────────────")
print(f"  Cancellation rate : {df['is_canceled'].mean()*100:.1f}%")
print(f"  Avg ADR           : ${confirmed['adr'].mean():.2f}")
print(f"  Avg stay          : {confirmed['total_nights'].mean():.1f} nights")
print(f"  Avg lead time     : {df['lead_time'].mean():.0f} days")
print(f"  Est. total revenue: ${confirmed['total_revenue'].sum()/1e6:.1f}M")
