# Workers' Compensation Rate Intelligence Database Schema

## Overview

This document provides a comprehensive overview of the database schema designed for the Workers' Compensation Rate Intelligence Platform. The database is structured to store and retrieve various types of medical fee schedules including workers' compensation rates, Medicare rates, and commercial payer rates. It supports geographical variations in pricing and provides efficient lookup pathways from zip codes to appropriate rates.

## Database Tables

### 1. State Table
Stores information about states and their fee schedules.

```sql
CREATE TABLE state (
    state_code CHAR(2) PRIMARY KEY,         -- Two-letter state code (e.g., 'GA' for Georgia)
    state_name VARCHAR(50) NOT NULL,        -- Full state name
    effective_date DATE NOT NULL,           -- When this state record became effective
    expiration_date DATE,                   -- Optional end date for the state record
    has_regions BOOLEAN DEFAULT 0,          -- Whether this state uses regional pricing
    data_source VARCHAR(255),               -- Source of the rate data
    data_url VARCHAR(255),                  -- URL to the official fee schedule
    notes TEXT                              -- Additional notes about the state's fee schedules
)
```

### 2. Zip Code Table
Provides complete geographic information for each zip code.

```sql
CREATE TABLE zip_code (
    zip_code VARCHAR(10) PRIMARY KEY,       -- Zip code (supports Zip+4 format)
    city VARCHAR(100),                      -- City name
    state_code CHAR(2),                     -- Reference to state table
    county VARCHAR(100),                    -- County name
    latitude DECIMAL(9,6),                  -- Geographic coordinates
    longitude DECIMAL(9,6),                 -- Geographic coordinates
    timezone VARCHAR(50),                   -- Time zone information
    active BOOLEAN DEFAULT 1,               -- Whether this zip code is still active
    last_updated TIMESTAMP,                 -- When this record was last updated
    FOREIGN KEY (state_code) REFERENCES state(state_code)
)
```

### 3. Region Table
Defines regions within states for regional pricing variations.

```sql
CREATE TABLE region (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique identifier for the region
    state_code CHAR(2),                     -- Reference to state table
    region_type VARCHAR(50) NOT NULL,       -- Type of region (e.g., 'county', 'zip', 'metro')
    region_code VARCHAR(50) NOT NULL,       -- Code identifying the specific region
    region_name VARCHAR(100),               -- Human-readable name for the region
    FOREIGN KEY (state_code) REFERENCES state(state_code),
    UNIQUE (state_code, region_type, region_code) -- Ensures unique regions per state
)
```

### 4. Zip Code to Region Mapping
Maps zip codes to their associated regions for rate lookup.

```sql
CREATE TABLE zip_region_map (
    zip_code VARCHAR(10),                   -- Reference to zip_code table
    region_id INTEGER,                      -- Reference to region table
    PRIMARY KEY (zip_code, region_id),      -- Composite primary key
    FOREIGN KEY (zip_code) REFERENCES zip_code(zip_code),
    FOREIGN KEY (region_id) REFERENCES region(region_id)
)
```

### 5. Fee Schedule Master
Defines different fee schedules available in the system.

```sql
CREATE TABLE fee_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the fee schedule
    state_code CHAR(2),                     -- Reference to state table
    schedule_type VARCHAR(50) NOT NULL,     -- Type of schedule (e.g., 'general_medicine', 'surgery')
    effective_date DATE NOT NULL,           -- When this fee schedule became effective
    expiration_date DATE,                   -- Optional end date for the fee schedule
    conversion_factor DECIMAL(10,4),        -- For states using RVU-based systems
    notes TEXT,                             -- Additional notes about the fee schedule
    FOREIGN KEY (state_code) REFERENCES state(state_code)
)
```

### 6. Procedure Code Master
Stores information about medical procedure codes.

```sql
CREATE TABLE procedure_code (
    procedure_code VARCHAR(20) PRIMARY KEY, -- CPT or HCPCS code
    description TEXT NOT NULL,              -- Description of the procedure
    code_type VARCHAR(10) NOT NULL,         -- Code system (e.g., 'CPT', 'HCPCS')
    category VARCHAR(50),                   -- General category of the procedure
    subcategory VARCHAR(50)                 -- Subcategory for more specific grouping
)
```

### 7. Fee Schedule Rates
Stores the actual rate amounts for procedure codes.

```sql
CREATE TABLE fee_schedule_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the rate
    fee_schedule_id INTEGER,                -- Reference to fee_schedule table
    procedure_code VARCHAR(20),             -- Reference to procedure_code table
    modifier VARCHAR(5) DEFAULT NULL,       -- Procedure code modifier (if any)
    region_id INTEGER,                      -- Reference to region table (if applicable)
    rate DECIMAL(10,2),                     -- The monetary rate amount
    rate_unit VARCHAR(20) DEFAULT '1',      -- Unit of measurement for the rate
    is_by_report BOOLEAN DEFAULT 0,         -- Whether the rate is determined on a case-by-case basis
    effective_date DATE NOT NULL,           -- When this rate became effective
    last_updated TIMESTAMP,                 -- When this record was last updated
    access_count INTEGER DEFAULT 0,         -- Number of times this rate has been accessed
    last_accessed TIMESTAMP,                -- When this rate was last accessed
    FOREIGN KEY (fee_schedule_id) REFERENCES fee_schedule(id),
    FOREIGN KEY (procedure_code) REFERENCES procedure_code(procedure_code),
    FOREIGN KEY (region_id) REFERENCES region(region_id),
    UNIQUE (fee_schedule_id, procedure_code, modifier, region_id) -- Ensures unique rates
)
```

### 8. Commercial Rates
Stores commercial payer rates for comparison.

```sql
CREATE TABLE commercial_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the commercial rate
    procedure_code VARCHAR(20),             -- Reference to procedure_code table
    modifier VARCHAR(5) DEFAULT NULL,       -- Procedure code modifier (if any)
    zip_code VARCHAR(10),                   -- Reference to zip_code table
    provider VARCHAR(200),                  -- Healthcare provider information
    payer VARCHAR(200),                     -- Insurance payer information
    rate DECIMAL(10,2),                     -- The monetary rate amount
    effective_date DATE,                    -- When this rate became effective
    data_source VARCHAR(100),               -- Source of the rate data
    last_updated TIMESTAMP,                 -- When this record was last updated
    FOREIGN KEY (procedure_code) REFERENCES procedure_code(procedure_code),
    FOREIGN KEY (zip_code) REFERENCES zip_code(zip_code)
)
```

### 9. Medicare Rates
Stores Medicare rates for reference.

```sql
CREATE TABLE medicare_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the Medicare rate
    procedure_code VARCHAR(20),             -- Reference to procedure_code table
    modifier VARCHAR(5) DEFAULT NULL,       -- Procedure code modifier (if any)
    locality_code VARCHAR(10),              -- Medicare locality code
    rate DECIMAL(10,2),                     -- The monetary rate amount
    effective_date DATE NOT NULL,           -- When this rate became effective
    expiration_date DATE,                   -- Optional end date for the rate
    last_updated TIMESTAMP,                 -- When this record was last updated
    FOREIGN KEY (procedure_code) REFERENCES procedure_code(procedure_code)
)
```

### 10. Medicare Locality Mapping
Maps zip codes to Medicare localities.

```sql
CREATE TABLE medicare_locality_map (
    zip_code VARCHAR(10) PRIMARY KEY,       -- Reference to zip_code table
    locality_code VARCHAR(10) NOT NULL,     -- Medicare locality code
    locality_name VARCHAR(100),             -- Human-readable name for the locality
    FOREIGN KEY (zip_code) REFERENCES zip_code(zip_code)
)
```

### 11. User Table
Stores information about system users.

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the user
    username VARCHAR(80) UNIQUE NOT NULL,   -- User's login name
    email VARCHAR(120) UNIQUE NOT NULL,     -- User's email address
    created_at TIMESTAMP,                   -- When the user account was created
    last_login TIMESTAMP                    -- When the user last logged in
)
```

### 12. Rate Query Table
Tracks user queries for analytics.

```sql
CREATE TABLE rate_query (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the query
    user_id INTEGER,                        -- Reference to user table
    state CHAR(2) NOT NULL,                 -- State code being queried
    procedure_code VARCHAR(20) NOT NULL,    -- Procedure code being queried
    query_date TIMESTAMP,                   -- When the query was made
    result_count INTEGER,                   -- Number of results returned
    cache_hit BOOLEAN DEFAULT 0,            -- Whether the query hit the cache
    FOREIGN KEY (user_id) REFERENCES user(id)
)
```

## Database Indexes

The following indexes are created to optimize query performance:

```sql
CREATE INDEX idx_zip_state ON zip_code(state_code);
CREATE INDEX idx_region_state ON region(state_code);
CREATE INDEX idx_fee_schedule_state ON fee_schedule(state_code);
CREATE INDEX idx_fee_schedule_rate_proc ON fee_schedule_rate(procedure_code);
CREATE INDEX idx_fee_schedule_rate_region ON fee_schedule_rate(region_id);
CREATE INDEX idx_query_state_procedure ON rate_query(state, procedure_code);
CREATE INDEX idx_query_date ON rate_query(query_date);
```

## Data Flow: From Zip Code to Rate

When a user looks up a rate by providing a zip code and procedure code, the system follows this path:

1. **Zip Code Lookup**:
   - Query the `zip_code` table to find the state code and other geographic information.

2. **Region Determination**:
   - Check the `state` table to see if the state uses regional pricing.
   - If yes, use the `zip_region_map` table to determine which region the zip code belongs to.

3. **Fee Schedule Selection**:
   - Find the appropriate fee schedule in the `fee_schedule` table based on state code and current date.

4. **Rate Lookup**:
   - Query the `fee_schedule_rate` table with the procedure code, fee schedule ID, and region ID (if applicable).
   - If no region-specific rate exists, fall back to state-level rates.

5. **Comparison** (optional):
   - Look up corresponding rates in the `commercial_rate` or `medicare_rate` tables for comparison.

## Importing Data

Data can be imported from various file formats (e.g., CSV) representing state fee schedules. The import process involves:

1. Parsing the state code and schedule type from the filename.
2. Creating or updating the corresponding state and fee schedule records.
3. Creating procedure code records if they don't exist.
4. Creating or updating the fee schedule rates.

## Maintenance and Analytics

The schema supports:

- Tracking rate access patterns via the `access_count` and `last_accessed` fields.
- Historical analysis via the `effective_date` and `expiration_date` fields.
- Query analytics through the `rate_query` table.

## Database Type

This schema is implemented in SQLite, a self-contained, serverless database engine. The entire database is stored in a single file, making it portable and easy to deploy. For larger deployments, the same schema could be implemented in PostgreSQL or another relational database system.