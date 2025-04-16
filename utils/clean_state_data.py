import sqlite3
import os

def delete_state_data(database_file, state_codes):
    """
    Delete all data associated with specified state codes from the database
    
    Args:
        database_file (str): Path to the SQLite database file
        state_codes (list): List of state codes to delete data for (e.g., ['GA', 'AL'])
    """
    if not os.path.exists(database_file):
        print(f"Database file {database_file} does not exist!")
        return
    
    # Format state codes for SQL IN clause
    state_codes_formatted = ', '.join([f"'{code}'" for code in state_codes])
    
    # Connect to the database
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Get fee schedule IDs for the specified states
        cursor.execute(f"SELECT id FROM fee_schedule WHERE state_code IN ({state_codes_formatted})")
        fee_schedule_ids = [row[0] for row in cursor.fetchall()]
        
        if fee_schedule_ids:
            # Format fee schedule IDs for SQL IN clause
            fee_ids_formatted = ', '.join([str(id) for id in fee_schedule_ids])
            
            # Delete from fee_schedule_rate
            cursor.execute(f"DELETE FROM fee_schedule_rate WHERE fee_schedule_id IN ({fee_ids_formatted})")
            print(f"Deleted {cursor.rowcount} records from fee_schedule_rate")
            
            # Delete from fee_schedule
            cursor.execute(f"DELETE FROM fee_schedule WHERE id IN ({fee_ids_formatted})")
            print(f"Deleted {cursor.rowcount} records from fee_schedule")
        
        # Get region IDs for the specified states
        cursor.execute(f"SELECT region_id FROM region WHERE state_code IN ({state_codes_formatted})")
        region_ids = [row[0] for row in cursor.fetchall()]
        
        if region_ids:
            # Format region IDs for SQL IN clause
            region_ids_formatted = ', '.join([str(id) for id in region_ids])
            
            # Delete from zip_region_map
            cursor.execute(f"DELETE FROM zip_region_map WHERE region_id IN ({region_ids_formatted})")
            print(f"Deleted {cursor.rowcount} records from zip_region_map")
            
            # Delete from fee_schedule_rate with region_id (in case some weren't caught by fee_schedule_id)
            cursor.execute(f"DELETE FROM fee_schedule_rate WHERE region_id IN ({region_ids_formatted})")
            print(f"Deleted {cursor.rowcount} additional records from fee_schedule_rate by region")
            
            # Delete from region
            cursor.execute(f"DELETE FROM region WHERE region_id IN ({region_ids_formatted})")
            print(f"Deleted {cursor.rowcount} records from region")
        
        # Delete from state
        cursor.execute(f"DELETE FROM state WHERE state_code IN ({state_codes_formatted})")
        print(f"Deleted {cursor.rowcount} records from state")
        
        # Delete from rate_query
        cursor.execute(f"DELETE FROM rate_query WHERE state IN ({state_codes_formatted})")
        print(f"Deleted {cursor.rowcount} records from rate_query")
        
        # Delete from zip_code where state_code matches
        cursor.execute(f"DELETE FROM zip_code WHERE state_code IN ({state_codes_formatted})")
        print(f"Deleted {cursor.rowcount} records from zip_code")
        
        # Commit changes
        conn.commit()
        print(f"Successfully removed all data for state codes: {', '.join(state_codes)}")
        
    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"Error: {str(e)}")
    finally:
        # Close connection
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Delete all data for specified state codes from the database')
    parser.add_argument('--db', type=str, default=r'C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db', help='Path to the SQLite database file')
    parser.add_argument('--states', type=str, required=True, help='Comma-separated list of state codes to delete data for (e.g., GA,AL,LA)')
    
    args = parser.parse_args()
    
    # Parse state codes
    state_codes = [code.strip().upper() for code in args.states.split(',')]
    
    # Execute deletion
    delete_state_data(args.db, state_codes)