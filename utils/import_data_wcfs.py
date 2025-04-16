import os
import csv
import sqlite3
import time
import glob
import shutil
from datetime import datetime

# Configuration
TARGET_FOLDER = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\wcfs_drop"  # Folder to monitor for new CSV files
PROCESSED_FOLDER = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\wcfs_drop\processed_data"  # Folder to move files after processing
ERROR_FOLDER = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\wcfs_drop\error_data"  # Folder for files that couldn't be processed
DATABASE_FILE = r"C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db"  # Path to your SQLite database

# Create folders if they don't exist
for folder in [TARGET_FOLDER, PROCESSED_FOLDER, ERROR_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def log_message(message):
    """Print a timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def parse_csv_filename(filename):
    """Parse information from the filename, looking for _XX suffix for state code"""
    try:
        base = os.path.basename(filename)
        name_without_ext = os.path.splitext(base)[0]
        
        # Look for state code at the end (_XX)
        parts = name_without_ext.split('_')
        
        if len(parts) >= 2:
            # Check if the last part is a two-letter state code
            potential_state_code = parts[-1].upper()
            if len(potential_state_code) == 2 and potential_state_code.isalpha():
                state_code = potential_state_code
                # Remove the state code from parts to get the schedule type
                schedule_parts = parts[:-1]
                # Skip 'import' if it's the first part
                if schedule_parts[0].lower() == 'import':
                    schedule_parts = schedule_parts[1:]
                schedule_type = '_'.join(schedule_parts)
                
                log_message(f"Parsed filename {base}: state_code={state_code}, schedule_type={schedule_type}")
                return state_code, schedule_type
        
        # If we get here, the filename doesn't match the expected pattern
        log_message(f"Couldn't find state code in {base}, please ensure filename ends with _XX where XX is the state code")
        return None, None
        
    except Exception as e:
        log_message(f"Error parsing filename {filename}: {str(e)}")
        return None, None

def import_file_to_database(conn, filepath):
    """Import data from a CSV file into the database"""
    cursor = conn.cursor()
    
    # Parse state code and schedule type from filename
    state_code, schedule_type = parse_csv_filename(filepath)
    if not state_code or not schedule_type:
        return False
    
    log_message(f"Processing file for state {state_code}, schedule type {schedule_type}")
    
    try:
        # Check if state exists, create if not
        cursor.execute("SELECT 1 FROM state WHERE state_code = ?", (state_code,))
        if not cursor.fetchone():
            log_message(f"Adding new state: {state_code}")
            cursor.execute(
                "INSERT INTO state (state_code, state_name, effective_date) VALUES (?, ?, ?)",
                (state_code, state_code, datetime.now().strftime("%Y-%m-%d"))
            )
        
        # Check if fee schedule exists, create if not
        cursor.execute(
            "SELECT id FROM fee_schedule WHERE state_code = ? AND schedule_type = ? AND (expiration_date IS NULL OR expiration_date >= date('now'))",
            (state_code, schedule_type)
        )
        fee_schedule_row = cursor.fetchone()
        
        if fee_schedule_row:
            fee_schedule_id = fee_schedule_row[0]
        else:
            cursor.execute(
                "INSERT INTO fee_schedule (state_code, schedule_type, effective_date) VALUES (?, ?, ?)",
                (state_code, schedule_type, datetime.now().strftime("%Y-%m-%d"))
            )
            fee_schedule_id = cursor.lastrowid
            log_message(f"Created new fee schedule with ID {fee_schedule_id}")
        
        # Process the CSV file
        with open(filepath, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            rows_processed = 0
            
            for row in reader:
                # Get or create procedure code
                proc_code = row['proc_cd']
                cursor.execute("SELECT 1 FROM procedure_code WHERE procedure_code = ?", (proc_code,))
                if not cursor.fetchone():
                    description = row.get('description', '')
                    cursor.execute(
                        "INSERT INTO procedure_code (procedure_code, description, code_type) VALUES (?, ?, ?)",
                        (proc_code, description, 'CPT')  # Assuming CPT codes, adjust if needed
                    )
                
                # Handle region if applicable
                region_id = None
                region_type = row.get('region_type')
                region_value = row.get('region_value')
                
                if region_type and region_type != 'state':
                    cursor.execute(
                        "SELECT region_id FROM region WHERE state_code = ? AND region_type = ? AND region_code = ?",
                        (state_code, region_type, region_value)
                    )
                    region_row = cursor.fetchone()
                    
                    if region_row:
                        region_id = region_row[0]
                    else:
                        cursor.execute(
                            "INSERT INTO region (state_code, region_type, region_code, region_name) VALUES (?, ?, ?, ?)",
                            (state_code, region_type, region_value, f"{state_code} {region_type} {region_value}")
                        )
                        region_id = cursor.lastrowid
                
                # Insert or update the fee schedule rate
                modifier = row.get('modifier', '').strip() or None
                rate = float(row.get('rate', 0)) if row.get('rate') else 0
                rate_unit = int(row.get('rate_unit', 1)) if row.get('rate_unit') else 1
                is_by_report = 1 if row.get('is_by_report') in ['True', 'true', '1', 'TRUE', 'T', 'Yes', 'yes', 'Y', 'y'] else 0
                
                # Check if rate entry already exists
                cursor.execute(
                    """
                    SELECT id FROM fee_schedule_rate 
                    WHERE fee_schedule_id = ? AND procedure_code = ? AND 
                          (modifier = ? OR (modifier IS NULL AND ? IS NULL)) AND
                          (region_id = ? OR (region_id IS NULL AND ? IS NULL))
                    """,
                    (fee_schedule_id, proc_code, modifier, modifier, region_id, region_id)
                )
                rate_row = cursor.fetchone()
                
                if rate_row:
                    # Update existing entry
                    cursor.execute(
                        """
                        UPDATE fee_schedule_rate
                        SET rate = ?, rate_unit = ?, is_by_report = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (rate, rate_unit, is_by_report, rate_row[0])
                    )
                else:
                    # Insert new entry
                    cursor.execute(
                        """
                        INSERT INTO fee_schedule_rate 
                        (fee_schedule_id, procedure_code, modifier, region_id, rate, rate_unit, is_by_report, effective_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, date('now'))
                        """,
                        (fee_schedule_id, proc_code, modifier, region_id, rate, rate_unit, is_by_report)
                    )
                
                rows_processed += 1
                
                # Commit every 1000 rows to avoid large transactions
                if rows_processed % 1000 == 0:
                    conn.commit()
                    log_message(f"Processed {rows_processed} rows...")
        
        # Final commit
        conn.commit()
        log_message(f"Successfully imported {rows_processed} rows from {filepath}")
        return True
        
    except Exception as e:
        conn.rollback()
        log_message(f"Error processing file {filepath}: {str(e)}")
        return False

def process_pending_files():
    """Process all CSV files in the target folder"""
    conn = sqlite3.connect(DATABASE_FILE)
    
    # Find all CSV files in the target folder
    csv_files = glob.glob(os.path.join(TARGET_FOLDER, "*.csv"))
    
    if not csv_files:
        log_message("No CSV files found in target folder.")
        return
    
    log_message(f"Found {len(csv_files)} CSV files to process")
    
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        log_message(f"Processing {file_name}...")
        
        success = import_file_to_database(conn, file_path)
        
        # Move file to processed or error folder
        if success:
            dest_folder = PROCESSED_FOLDER
            log_message(f"Successfully processed {file_name}")
        else:
            dest_folder = ERROR_FOLDER
            log_message(f"Failed to process {file_name}")
        
        # Create a timestamped filename to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dest_file = os.path.join(dest_folder, f"{timestamp}_{file_name}")
        shutil.move(file_path, dest_file)
    
    conn.close()

def run_import_service(interval=60):
    """Run as a service, checking for new files at the specified interval (seconds)"""
    log_message(f"Starting import service. Monitoring folder: {TARGET_FOLDER}")
    log_message(f"Check interval: {interval} seconds")
    
    try:
        while True:
            process_pending_files()
            time.sleep(interval)
    except KeyboardInterrupt:
        log_message("Service stopped by user")
    except Exception as e:
        log_message(f"Service error: {str(e)}")

def run_once():
    """Process files once and exit"""
    log_message("Processing files in one-time mode")
    process_pending_files()
    log_message("Processing complete")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import fee schedule CSV files into the database')
    parser.add_argument('--service', action='store_true', help='Run as a continuous service')
    parser.add_argument('--interval', type=int, default=60, help='Interval in seconds for checking new files (when running as service)')
    
    args = parser.parse_args()
    
    if args.service:
        run_import_service(args.interval)
    else:
        run_once()