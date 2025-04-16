import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
folder = r"C:\Users\ChristopherCato\Downloads\rvu25a (1)"
db_path = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db"

# --- DATABASE CONNECTION ---
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# --- TABLE SETUP ---
cursor.executescript("""
CREATE TABLE IF NOT EXISTS cms_rvu (
    procedure_code TEXT,
    year INTEGER NOT NULL,
    work_rvu REAL,
    practice_expense_rvu REAL,
    malpractice_rvu REAL,
    total_rvu REAL,
    modifier TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (procedure_code, year, modifier)
);

CREATE TABLE IF NOT EXISTS cms_gpci (
    locality_code TEXT,
    year INTEGER NOT NULL,
    work_gpci REAL,
    pe_gpci REAL,
    mp_gpci REAL,
    locality_name TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (locality_code, year)
);

CREATE TABLE IF NOT EXISTS cms_conversion_factor (
    year INTEGER PRIMARY KEY,
    conversion_factor REAL,
    effective_date DATE NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicare_locality_meta (
    mac_code TEXT,
    locality_code TEXT,
    state_name TEXT,
    fee_schedule_area TEXT,
    counties TEXT,
    PRIMARY KEY (mac_code, locality_code)
);
""")

# --- 1. Load RVU Data ---
rvu_path = f"{folder}\\PPRRVU25_JAN.xlsx"
rvu_columns = [
    "HCPCS", "MOD", "DESCRIPTION", "STATUS_CODE", "MEDICARE_PAYMENT", "WORK_RVU",
    "NON_FAC_PE_RVU", "NON_FAC_NA_IND", "FAC_PE_RVU", "FAC_NA_IND", "MP_RVU",
    "NON_FAC_TOTAL", "FAC_TOTAL", "PCTC_IND", "GLOB_DAYS"
]
df_rvu = df_rvu = pd.read_excel(rvu_path, dtype=str)
print("🧠 Detected RVU Columns:")
print(df_rvu.columns.tolist())

# 🧼 Drop blank rows and rows without HCPCS
df_rvu = df_rvu.dropna(how='all')
df_rvu = df_rvu[df_rvu["HCPCS"].notna()]

# Convert to numeric
df_rvu["WORK_RVU"] = pd.to_numeric(df_rvu["WORK_RVU"], errors="coerce")
df_rvu["NON_FAC_PE_RVU"] = pd.to_numeric(df_rvu["NON_FAC_PE_RVU"], errors="coerce")
df_rvu["MP_RVU"] = pd.to_numeric(df_rvu["MP_RVU"], errors="coerce")
df_rvu["NON_FAC_TOTAL"] = pd.to_numeric(df_rvu["NON_FAC_TOTAL"], errors="coerce")

# Prepare insert
rvu_rows = df_rvu[[
    "HCPCS", "MOD", "WORK_RVU", "NON_FAC_PE_RVU", "MP_RVU", "NON_FAC_TOTAL"
]].copy()
rvu_rows = rvu_rows.rename(columns={
    "HCPCS": "procedure_code",
    "MOD": "modifier",
    "WORK_RVU": "work_rvu",
    "NON_FAC_PE_RVU": "practice_expense_rvu",
    "MP_RVU": "malpractice_rvu",
    "NON_FAC_TOTAL": "total_rvu"
})
rvu_rows["year"] = 2025
rvu_rows.to_sql("cms_rvu", conn, if_exists="replace", index=False)
print(f"✅ Loaded {len(rvu_rows)} rows into cms_rvu")

# --- 2. Load GPCI Data ---
gpci_path = f"{folder}\\GPCI2025.csv"
df_gpci = pd.read_csv(gpci_path, skip_blank_lines=True, header=None, dtype=str)

# 🧼 Drop blank rows and invalid entries
df_gpci = df_gpci.dropna(how='all')
df_gpci = df_gpci[df_gpci[2].notna()]  # Locality Code must be present

# Assign headers
df_gpci.columns = [
    "mac_code", "state", "locality_code", "locality_name",
    "work_gpci", "pe_gpci", "mp_gpci"
]

# Convert to numeric
df_gpci["work_gpci"] = pd.to_numeric(df_gpci["work_gpci"], errors="coerce")
df_gpci["pe_gpci"] = pd.to_numeric(df_gpci["pe_gpci"], errors="coerce")
df_gpci["mp_gpci"] = pd.to_numeric(df_gpci["mp_gpci"], errors="coerce")
df_gpci["year"] = 2025

df_gpci[[
    "locality_code", "year", "work_gpci", "pe_gpci", "mp_gpci", "locality_name"
]].to_sql("cms_gpci", conn, if_exists="replace", index=False)
print(f"✅ Loaded {len(df_gpci)} rows into cms_gpci")

# --- 3. Load Locality Meta Data ---
meta_path = f"{folder}\\25LOCCO.csv"
df_meta = pd.read_csv(meta_path, header=None, skip_blank_lines=True, dtype=str)

# 🧼 Drop fully blank rows and rows without locality/state
df_meta = df_meta.dropna(how='all')
df_meta = df_meta[df_meta[1].notna() & df_meta[2].notna()]  # locality_code & state_name

# Assign headers
df_meta.columns = [
    "mac_code", "locality_code", "state_name",
    "fee_schedule_area", "counties"
]

df_meta = df_meta.drop_duplicates()
df_meta.to_sql("medicare_locality_meta", conn, if_exists="replace", index=False)
print(f"✅ Loaded {len(df_meta)} rows into medicare_locality_meta")

# --- 4. Load Conversion Factor ---
cursor.execute("""
INSERT OR REPLACE INTO cms_conversion_factor (year, conversion_factor, effective_date)
VALUES (?, ?, ?)
""", (2025, 32.7442, "2025-01-01"))
print("✅ Loaded 2025 conversion factor")

# --- FINALIZE ---
conn.commit()
conn.close()
print("✅ All Medicare 2025 reference data loaded successfully.")
