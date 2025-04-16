import pandas as pd
import sqlite3
from geopy.geocoders import Nominatim
from time import sleep

# DB + input
db_path = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db"
conn = sqlite3.connect(db_path)

# Get ZIPs from DB
df_zips = pd.read_sql("SELECT zip_code FROM zip_code where state_code = 'CA' or state_code = 'FL' or state_code = 'GA' limit 15", conn)
df_zips = df_zips.drop_duplicates().reset_index(drop=True)

# Setup geocoder
geolocator = Nominatim(user_agent="zip-code-enricher")

# Add new columns
df_zips["city"] = ""
df_zips["county"] = ""
df_zips["state"] = ""
df_zips["latitude"] = None
df_zips["longitude"] = None

for idx, row in df_zips.iterrows():
    zip_code = row["zip_code"]
    try:
        location = geolocator.geocode({"postalcode": zip_code, "country": "USA"}, timeout=10)
        if location:
            df_zips.at[idx, "latitude"] = location.latitude
            df_zips.at[idx, "longitude"] = location.longitude

            if location.raw.get("address"):
                addr = location.raw["address"]
                df_zips.at[idx, "city"] = addr.get("city", addr.get("town", ""))
                df_zips.at[idx, "county"] = addr.get("county", "")
                df_zips.at[idx, "state"] = addr.get("state", "")
        
        print(f"✅ Enriched {zip_code}")
    except Exception as e:
        print(f"❌ Error with {zip_code}: {e}")
    sleep(1)  # avoid hammering the OSM API (courtesy delay)

# Save to new table
df_zips.to_sql("zip_code_enriched", conn, if_exists="replace", index=False)
print("✅ Enriched ZIP data saved to zip_code_enriched")
conn.close()
