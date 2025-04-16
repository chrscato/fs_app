import sqlite3
import pandas as pd

# Load DB
db_path = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db"
conn = sqlite3.connect(db_path)

# Get conversion factor
cf = conn.execute("SELECT conversion_factor FROM cms_conversion_factor WHERE year = 2025").fetchone()[0]

# Get 5 random localities
localities = pd.read_sql("""
    SELECT DISTINCT locality_code, locality_name, work_gpci, pe_gpci, mp_gpci
    FROM cms_gpci
    WHERE year = 2025
    ORDER BY RANDOM()
    LIMIT 5
""", conn)

# Get RVU data for the target CPT codes (all modifiers)
rvus = pd.read_sql("""
    SELECT procedure_code, modifier, work_rvu, practice_expense_rvu, malpractice_rvu
    FROM cms_rvu
    WHERE year = 2025
    AND procedure_code IN ('73221', '73721')
""", conn)

# Calculate rates
results = []

for _, loc in localities.iterrows():
    for _, rvu in rvus.iterrows():
        total_rvu = (
            (rvu["work_rvu"] or 0) * loc["work_gpci"] +
            (rvu["practice_expense_rvu"] or 0) * loc["pe_gpci"] +
            (rvu["malpractice_rvu"] or 0) * loc["mp_gpci"]
        )
        rate = round(total_rvu * cf, 2)
        results.append({
            "locality_name": loc["locality_name"],
            "locality_code": loc["locality_code"],
            "procedure_code": rvu["procedure_code"],
            "modifier": rvu["modifier"] if rvu["modifier"] else "<none>",
            "rate": rate
        })

# Output
df_result = pd.DataFrame(results)
print("💵 CMS Rates for 73221 and 73721 (All Modifiers) Across 5 Random Localities:\n")
print(df_result.pivot_table(index=["locality_name", "locality_code"],
                            columns=["procedure_code", "modifier"],
                            values="rate", aggfunc="first").fillna("—"))
