import geopandas as gpd
import zipfile
import sqlite3
import os
import tempfile
import pandas as pd

# --- CONFIG ---
zip_path = r"C:\Users\ChristopherCato\Downloads\tl_2020_us_zcta520.zip"
db_path = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db"

# --- UNZIP TO TEMP FOLDER ---
with tempfile.TemporaryDirectory() as tmpdir:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)

    # Find the .shp file inside the extracted files
    shp_path = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith(".shp")][0]

    # Load shapefile into GeoDataFrame
    gdf = gpd.read_file(shp_path)
    print("🧠 Available columns in shapefile:")
    print(gdf.columns.tolist())

    # Extract needed fields
    df = gdf[["ZCTA5CE20", "INTPTLAT20", "INTPTLON20"]].copy()
    df = df.rename(columns={
        "ZCTA5CE20": "zip_code",
        "INTPTLAT20": "latitude",
        "INTPTLON20": "longitude"
    })
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

# --- INSERT INTO SQLITE ---
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add columns if missing
try:
    cursor.execute("ALTER TABLE zip_code ADD COLUMN latitude REAL;")
except sqlite3.OperationalError:
    pass  # column already exists

try:
    cursor.execute("ALTER TABLE zip_code ADD COLUMN longitude REAL;")
except sqlite3.OperationalError:
    pass  # column already exists

# Merge into zip_code table
for _, row in df.iterrows():
    cursor.execute("""
        UPDATE zip_code
        SET latitude = ?, longitude = ?
        WHERE zip_code = ?
    """, (row["latitude"], row["longitude"], row["zip_code"]))

conn.commit()
conn.close()
print("✅ ZIP centroid coordinates successfully added from Census shapefile.")
