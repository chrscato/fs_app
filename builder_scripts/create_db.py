import sqlite3
import os
from datetime import datetime

def create_database(db_path=r'C:\Users\ChristopherCato\OneDrive - clarity-dx.com\compensation-fee-schedule-app\data\compensation_rates.db'):
    """Create a new SQLite database with all required tables"""
    
    # Remove existing database if any
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    
    # State table
    cursor.execute('''
    CREATE TABLE state (
        state_code CHAR(2) PRIMARY KEY,
        state_name VARCHAR(50) NOT NULL,
        effective_date DATE NOT NULL,
        expiration_date DATE,
        has_regions BOOLEAN DEFAULT 0,
        data_source VARCHAR(255),
        data_url VARCHAR(255),
        notes TEXT
    )
    ''')
    
    # Zip Code table
    cursor.execute('''
    CREATE TABLE zip_code (
        zip_code VARCHAR(10) PRIMARY KEY,
        city VARCHAR(100),
        state_code CHAR(2),
        county VARCHAR(100),
        latitude DECIMAL(9,6),
        longitude DECIMAL(9,6),
        timezone VARCHAR(50),
        active BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (state_code) REFERENCES state(state_code)
    )
    ''')
    
    # Region table
    cursor.execute('''
    CREATE TABLE region (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_code CHAR(2),
        region_type VARCHAR(50) NOT NULL,
        region_code VARCHAR(50) NOT NULL,
        region_name VARCHAR(100),
        FOREIGN KEY (state_code) REFERENCES state(state_code),
        UNIQUE (state_code, region_type, region_code)
    )
    ''')
    
    # Zip Code to Region mapping
    cursor.execute('''
    CREATE TABLE zip_region_map (
        zip_code VARCHAR(10),
        region_id INTEGER,
        PRIMARY KEY (zip_code, region_id),
        FOREIGN KEY (zip_code) REFERENCES zip_code(zip_code),
        FOREIGN KEY (region_id) REFERENCES region(region_id)
    )
    ''')
    
    # Fee Schedule Master
    cursor.execute('''
    CREATE TABLE fee_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_code CHAR(2),
        schedule_type VARCHAR(50) NOT NULL,
        effective_date DATE NOT NULL,
        expiration_date DATE,
        conversion_factor DECIMAL(10,4),
        notes TEXT,
        FOREIGN KEY (state_code) REFERENCES state(state_code)
    )
    ''')
    
    # Procedure Code Master
    cursor.execute('''
    CREATE TABLE procedure_code (
        procedure_code VARCHAR(20) PRIMARY KEY,
        description TEXT NOT NULL,
        code_type VARCHAR(10) NOT NULL,
        category VARCHAR(50),
        subcategory VARCHAR(50)
    )
    ''')
    
    # Fee Schedule Rates
    cursor.execute('''
    CREATE TABLE fee_schedule_rate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fee_schedule_id INTEGER,
        procedure_code VARCHAR(20),
        modifier VARCHAR(5) DEFAULT NULL,
        region_id INTEGER,
        rate DECIMAL(10,2),
        rate_unit VARCHAR(20) DEFAULT '1',
        is_by_report BOOLEAN DEFAULT 0,
        effective_date DATE NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        access_count INTEGER DEFAULT 0,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (fee_schedule_id) REFERENCES fee_schedule(id),
        FOREIGN KEY (procedure_code) REFERENCES procedure_code(procedure_code),
        FOREIGN KEY (region_id) REFERENCES region(region_id),
        UNIQUE (fee_schedule_id, procedure_code, modifier, region_id)
    )
    ''')
    
    # Commercial Rates
    cursor.execute('''
    CREATE TABLE commercial_rate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        procedure_code VARCHAR(20),
        modifier VARCHAR(5) DEFAULT NULL,
        zip_code VARCHAR(10),
        provider VARCHAR(200),
        payer VARCHAR(200),
        rate DECIMAL(10,2),
        effective_date DATE,
        data_source VARCHAR(100),
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (procedure_code) REFERENCES procedure_code(procedure_code),
        FOREIGN KEY (zip_code) REFERENCES zip_code(zip_code)
    )
    ''')
    
    # Medicare Rates
    cursor.execute('''
    CREATE TABLE medicare_rate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        procedure_code VARCHAR(20),
        modifier VARCHAR(5) DEFAULT NULL,
        locality_code VARCHAR(10),
        rate DECIMAL(10,2),
        effective_date DATE NOT NULL,
        expiration_date DATE,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (procedure_code) REFERENCES procedure_code(procedure_code)
    )
    ''')
    
    # Medicare Locality Mapping
    cursor.execute('''
    CREATE TABLE medicare_locality_map (
        zip_code VARCHAR(10) PRIMARY KEY,
        locality_code VARCHAR(10) NOT NULL,
        locality_name VARCHAR(100),
        FOREIGN KEY (zip_code) REFERENCES zip_code(zip_code)
    )
    ''')
    
    # User table (from your existing models.py)
    cursor.execute('''
    CREATE TABLE user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # RateQuery table (from your existing models.py)
    cursor.execute('''
    CREATE TABLE rate_query (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        state CHAR(2) NOT NULL,
        procedure_code VARCHAR(20) NOT NULL,
        query_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        result_count INTEGER,
        cache_hit BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES user(id)
    )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX idx_zip_state ON zip_code(state_code)')
    cursor.execute('CREATE INDEX idx_region_state ON region(state_code)')
    cursor.execute('CREATE INDEX idx_fee_schedule_state ON fee_schedule(state_code)')
    cursor.execute('CREATE INDEX idx_fee_schedule_rate_proc ON fee_schedule_rate(procedure_code)')
    cursor.execute('CREATE INDEX idx_fee_schedule_rate_region ON fee_schedule_rate(region_id)')
    cursor.execute('CREATE INDEX idx_query_state_procedure ON rate_query(state, procedure_code)')
    cursor.execute('CREATE INDEX idx_query_date ON rate_query(query_date)')
    
    # Add sample data for Georgia
    cursor.execute('''
    INSERT INTO state (state_code, state_name, effective_date, has_regions, data_source) 
    VALUES ('GA', 'Georgia', '2023-01-01', 0, 'State Workers Compensation Board')
    ''')
    
    # Create a fee schedule for Georgia
    cursor.execute('''
    INSERT INTO fee_schedule (state_code, schedule_type, effective_date, notes)
    VALUES ('GA', 'general_medicine', '2023-01-01', 'General Medicine Fee Schedule for Georgia')
    ''')
    
    # Save changes and close
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at {db_path}")
    
if __name__ == "__main__":
    create_database()