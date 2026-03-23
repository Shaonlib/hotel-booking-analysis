"""
03_sql_analysis.py
────────────────────────────────────────────────────────────
Runs 7 business-focused SQL queries against the cleaned
dataset using an in-memory SQLite database.
Mirrors the logic you would use in SQL Server / PostgreSQL.
────────────────────────────────────────────────────────────
"""

import pandas as pd
import sqlite3

# ── Load into SQLite ──────────────────────────────────────
df   = pd.read_csv("data/hotel_bookings_clean.csv")
conn = sqlite3.connect(":memory:")
df.to_sql("hotel_bookings", conn, index=False, if_exists="replace")
print(f"Loaded {len(df):,} rows into SQLite\n")

def run(title, sql):
    divider = "═" * 62
    print(f"{divider}\n  {title}\n{divider}")
    result = pd.read_sql(sql, conn)
    print(result.to_string(index=False))
    print()
    return result

MONTH_CASE = """
    CASE arrival_date_month
        WHEN 'January'   THEN 1  WHEN 'February'  THEN 2
        WHEN 'March'     THEN 3  WHEN 'April'     THEN 4
        WHEN 'May'       THEN 5  WHEN 'June'      THEN 6
        WHEN 'July'      THEN 7  WHEN 'August'    THEN 8
        WHEN 'September' THEN 9  WHEN 'October'   THEN 10
        WHEN 'November'  THEN 11 WHEN 'December'  THEN 12
    END
"""

# ── Q1: Monthly Revenue & ADR ────────────────────────────
run("Q1 — Monthly ADR & Revenue (Confirmed Bookings)", f"""
SELECT
    arrival_date_year                               AS year,
    arrival_date_month                              AS month,
    hotel,
    COUNT(*)                                        AS confirmed_bookings,
    ROUND(AVG(adr), 2)                              AS avg_adr,
    ROUND(AVG(total_nights), 1)                     AS avg_stay_nights,
    ROUND(SUM(total_revenue), 0)                    AS total_revenue
FROM hotel_bookings
WHERE is_canceled = 0
GROUP BY 1, 2, 3
ORDER BY 1, {MONTH_CASE}, 3
""")

# ── Q2: Cancellation Risk ────────────────────────────────
run("Q2 — Cancellation Rate by Market Segment & Deposit Type", """
SELECT
    market_segment,
    deposit_type,
    COUNT(*)                                        AS total_bookings,
    SUM(is_canceled)                                AS cancellations,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 1)  AS cancel_rate_pct,
    ROUND(AVG(lead_time), 0)                        AS avg_lead_time_days
FROM hotel_bookings
GROUP BY 1, 2
HAVING total_bookings > 100
ORDER BY cancel_rate_pct DESC
""")

# ── Q3: Channel Profitability ────────────────────────────
run("Q3 — Distribution Channel Profitability", """
SELECT
    distribution_channel,
    COUNT(*)                                            AS total_bookings,
    SUM(CASE WHEN is_canceled = 0 THEN 1 ELSE 0 END)   AS confirmed,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 1)      AS cancel_rate_pct,
    ROUND(AVG(CASE WHEN is_canceled = 0 THEN adr END), 2) AS avg_adr,
    ROUND(SUM(CASE WHEN is_canceled = 0 THEN total_revenue ELSE 0 END), 0)
                                                        AS total_revenue
FROM hotel_bookings
GROUP BY 1
ORDER BY total_revenue DESC
""")

# ── Q4: Top Countries ────────────────────────────────────
run("Q4 — Top 10 Guest Countries by Revenue", """
SELECT
    country,
    COUNT(*)                                            AS bookings,
    ROUND(AVG(adr), 2)                                  AS avg_adr,
    ROUND(SUM(total_revenue), 0)                        AS total_revenue,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 1)       AS cancel_rate_pct
FROM hotel_bookings
WHERE country != 'Unknown'
GROUP BY 1
ORDER BY total_revenue DESC
LIMIT 10
""")

# ── Q5: Lead Time vs Cancellation ───────────────────────
run("Q5 — Booking Lead Time Buckets vs Cancellation Rate", """
SELECT
    CASE
        WHEN lead_time = 0      THEN '0  Same Day'
        WHEN lead_time <= 7     THEN '1  1-7 Days'
        WHEN lead_time <= 30    THEN '2  8-30 Days'
        WHEN lead_time <= 90    THEN '3  31-90 Days'
        WHEN lead_time <= 180   THEN '4  91-180 Days'
        ELSE                         '5  180+ Days'
    END                                                 AS lead_time_bucket,
    COUNT(*)                                            AS bookings,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 1)      AS cancel_rate_pct,
    ROUND(AVG(adr), 2)                                  AS avg_adr
FROM hotel_bookings
GROUP BY 1
ORDER BY 1
""")

# ── Q6: Repeat vs New Guest ──────────────────────────────
run("Q6 — Repeat vs New Guest Value Comparison", """
SELECT
    CASE WHEN is_repeated_guest = 1
         THEN 'Repeat Guest' ELSE 'New Guest'
    END                                                 AS guest_type,
    COUNT(*)                                            AS bookings,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 1)      AS cancel_rate_pct,
    ROUND(AVG(adr), 2)                                  AS avg_adr,
    ROUND(AVG(total_nights), 1)                         AS avg_nights,
    ROUND(AVG(total_of_special_requests), 2)            AS avg_special_requests
FROM hotel_bookings
GROUP BY 1
""")

# ── Q7: Forecast vs Actual ───────────────────────────────
run("Q7 — Monthly Forecast vs Actual Stays", f"""
SELECT
    arrival_date_year                                   AS year,
    arrival_date_month                                  AS month,
    hotel,
    COUNT(*)                                            AS bookings_made,
    SUM(CASE WHEN is_canceled = 0 THEN 1 ELSE 0 END)   AS actual_stays,
    SUM(is_canceled)                                    AS cancellations,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 1)      AS cancel_rate_pct
FROM hotel_bookings
GROUP BY 1, 2, 3
ORDER BY 1, {MONTH_CASE}, 3
""")

conn.close()
print("SQL analysis complete.")
