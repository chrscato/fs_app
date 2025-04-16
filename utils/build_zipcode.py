import pandas as pd
import sqlite3

# Paths
xlsx_path = r"C:\Users\ChristopherCato\Downloads\zplc_apr2025\ZIP5_APR2025.xlsx"
db_path = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db"

# Load file
df = pd.read_excel(xlsx_path, engine="openpyxl", dtype=str)
df.columns = df.columns.str.strip()

# Filter to valid quarter
df = df[df["YEAR/QTR"] == "20252"]

# Rename and keep what matters
df = df.rename(columns={
    "ZIP CODE": "zip_code",
    "STATE": "state_code",
    "CARRIER": "carrier_code",
    "LOCALITY": "locality_code",
    "YEAR/QTR": "year_qtr"
})

df = df[["zip_code", "state_code", "carrier_code", "locality_code", "year_qtr"]]
df = df.dropna(subset=["zip_code", "locality_code"])
df = df.drop_duplicates(subset=["zip_code"])

# Connect to DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create updated table
cursor.executescript("""
CREATE TABLE IF NOT EXISTS medicare_locality_map (
    zip_code TEXT PRIMARY KEY,
    state_code TEXT,
    carrier_code TEXT,
    locality_code TEXT,
    year_qtr TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zip_code) REFERENCES zip_code(zip_code)
);
""")

# Insert clean data
df.to_sql("medicare_locality_map", conn, if_exists="replace", index=False)

print(f"✅ Loaded {len(df)} records into medicare_locality_map (with CMS locality linkage).")
conn.commit()
conn.close()
