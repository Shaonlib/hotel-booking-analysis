"""
02_eda_visualizations.py
────────────────────────────────────────────────────────────
Generates 6 analysis charts from the cleaned dataset and
saves them to outputs/charts/.
────────────────────────────────────────────────────────────
"""

import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# ── Style ─────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f1117",
    "axes.facecolor":   "#1a1d27",
    "axes.edgecolor":   "#2e3250",
    "axes.labelcolor":  "#c9d1e8",
    "xtick.color":      "#8890b0",
    "ytick.color":      "#8890b0",
    "text.color":       "#c9d1e8",
    "grid.color":       "#2e3250",
    "grid.linewidth":   0.6,
    "font.family":      "DejaVu Sans",
})
PALETTE = ["#4f8ef7", "#f7904f", "#4fd1a5", "#b04ff7", "#f74f7e"]

# ── Load ──────────────────────────────────────────────────
df = pd.read_csv("data/hotel_bookings_clean.csv")
confirmed = df[df["is_canceled"] == 0]

MONTH_ORDER = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
df["arrival_date_month"] = pd.Categorical(
    df["arrival_date_month"], categories=MONTH_ORDER, ordered=True
)

def save(fig, name):
    path = f"outputs/charts/{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"  Saved: {path}")
    plt.close(fig)

print("Generating charts...")

# ── Chart 1: Monthly Booking Volume ───────────────────────
monthly = (df.groupby(["arrival_date_month", "hotel"], observed=True)
             .size().reset_index(name="bookings"))

fig, ax = plt.subplots(figsize=(13, 5))
for i, hotel in enumerate(["City Hotel", "Resort Hotel"]):
    sub = monthly[monthly["hotel"] == hotel]
    ax.plot(sub["arrival_date_month"].astype(str), sub["bookings"],
            marker="o", lw=2.2, color=PALETTE[i], label=hotel)
ax.set_title("Monthly Booking Volume by Hotel Type", fontsize=14, pad=12)
ax.set_xlabel("Month"); ax.set_ylabel("Bookings")
ax.legend(framealpha=0); ax.grid(axis="y")
plt.xticks(rotation=30, ha="right")
save(fig, "01_monthly_bookings")

# ── Chart 2: Cancellation Rate by Market Segment ──────────
seg = (df.groupby("market_segment")
         .agg(total=("is_canceled","count"), canceled=("is_canceled","sum"))
         .assign(cancel_rate=lambda x: x["canceled"] / x["total"] * 100)
         .sort_values("cancel_rate", ascending=True))

fig, ax = plt.subplots(figsize=(9, 6))
bars = ax.barh(seg.index, seg["cancel_rate"], color=PALETTE[0], edgecolor="none")
for bar, val in zip(bars, seg["cancel_rate"]):
    ax.text(val + 0.4, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", fontsize=9)
ax.set_title("Cancellation Rate by Market Segment", fontsize=14, pad=12)
ax.set_xlabel("Cancellation Rate (%)"); ax.grid(axis="x")
save(fig, "02_cancellation_by_segment")

# ── Chart 3: ADR Trend ────────────────────────────────────
df["arrival_yearmon"] = pd.to_datetime(
    df["arrival_date_year"].astype(str) + "-" +
    df["arrival_date_month"].astype(str) + "-01",
    format="%Y-%B-%d", errors="coerce"
).dt.to_period("M")

adr_trend = (confirmed.groupby(["arrival_yearmon","hotel"])["adr"]
               .mean().reset_index())
adr_trend["period_str"] = adr_trend["arrival_yearmon"].astype(str)

fig, ax = plt.subplots(figsize=(13, 5))
for i, hotel in enumerate(["City Hotel", "Resort Hotel"]):
    sub = adr_trend[adr_trend["hotel"] == hotel].sort_values("arrival_yearmon")
    ax.plot(sub["period_str"], sub["adr"],
            marker="o", lw=2.2, color=PALETTE[i], label=hotel)
ax.set_title("Average Daily Rate Trend (Confirmed Bookings Only)", fontsize=14, pad=12)
ax.set_xlabel("Period"); ax.set_ylabel("ADR ($)")
ax.legend(framealpha=0); ax.grid(axis="y")
plt.xticks(rotation=45, ha="right", fontsize=7)
save(fig, "03_adr_trend")

# ── Chart 4: Lead Time Distribution ──────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
for i, hotel in enumerate(["City Hotel", "Resort Hotel"]):
    sub = df[df["hotel"] == hotel]["lead_time"]
    ax.hist(sub, bins=60, alpha=0.65, color=PALETTE[i], label=hotel, edgecolor="none")
ax.set_title("Booking Lead Time Distribution", fontsize=14, pad=12)
ax.set_xlabel("Days Before Arrival"); ax.set_ylabel("Number of Bookings")
ax.legend(framealpha=0); ax.grid(axis="y")
save(fig, "04_lead_time_distribution")

# ── Chart 5: Revenue by Distribution Channel ─────────────
rev_ch = (confirmed.groupby("distribution_channel")["total_revenue"]
            .sum().sort_values(ascending=False))

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(rev_ch.index, rev_ch / 1e6,
              color=PALETTE[:len(rev_ch)], edgecolor="none")
for bar, val in zip(bars, rev_ch / 1e6):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.2,
            f"${val:.1f}M", ha="center", fontsize=9)
ax.set_title("Total Revenue by Distribution Channel", fontsize=14, pad=12)
ax.set_ylabel("Revenue ($ Millions)"); ax.grid(axis="y")
save(fig, "05_revenue_by_channel")

# ── Chart 6: Room Assignment Match ───────────────────────
upgrade = confirmed["room_match"].value_counts(normalize=True) * 100
labels = ["Room Matched", "Upgraded / Changed"]
colors = [PALETTE[2], PALETTE[1]]

fig, ax = plt.subplots(figsize=(6, 6))
wedges, texts, autotexts = ax.pie(
    upgrade.values, labels=labels, autopct="%1.1f%%",
    colors=colors, startangle=90,
    wedgeprops={"edgecolor": "#0f1117", "linewidth": 2})
for t in texts + autotexts:
    t.set_color("#c9d1e8")
ax.set_title("Room Assignment: Match vs Change", fontsize=14, pad=12)
save(fig, "06_room_assignment")

print("\nAll 6 charts saved to outputs/charts/")
