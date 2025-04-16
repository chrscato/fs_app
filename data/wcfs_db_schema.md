# Workers' Comp Fee Schedule (WCFS) Database Schema

This schema is designed to support a flexible, scalable fee schedule lookup system. It accommodates both **statewide** and **region-specific** rate structures (e.g., by ZIP code, county, or MSA).

---

## 📦 Table: `rates`

Stores rates by procedure code, modifier, and region.

| Column Name     | Data Type | Description |
|------------------|-----------|-------------|
| `rate_id`        | INTEGER   | Primary key (auto-increment) |
| `cpt_code`       | TEXT      | CPT or procedure code |
| `modifier`       | TEXT      | Optional modifier (e.g., 26, TC) |
| `description`    | TEXT      | Procedure description |
| `rate_amount`    | FLOAT     | Fee schedule amount |
| `rate_unit`      | TEXT      | Unit of measure (e.g., per-procedure, per-hour) |
| `region_type`    | TEXT      | Scope of rate (e.g., `state`, `zip`, `county`, `msa`) |
| `region_value`   | TEXT      | Value that matches the appropriate region (e.g., 'GA', '30303', 'Fulton', 'ATL_MSA') |

**💡 Example:**
| cpt_code | modifier | rate_amount | region_type | region_value |
|----------|----------|-------------|-------------|--------------|
| 72148    | TC       | 164.88      | state       | GA           |

---

## 🌍 Table: `zip_regions`

Maps ZIP codes to their corresponding region value (used for rate lookup).

| Column Name     | Data Type | Description |
|------------------|-----------|-------------|
| `zip`            | TEXT      | 5-digit ZIP code |
| `state`          | TEXT      | 2-letter state code |
| `county_name`    | TEXT      | County name (if applicable) |
| `region_value`   | TEXT      | Matches `region_value` in `rates` table |
| `region_type`    | TEXT      | Matches `region_type` in `rates` table |

**💡 Example:**
| zip   | state | county_name | region_value | region_type |
|-------|--------|--------------|----------------|----------------|
| 30303 | GA     | Fulton       | GA             | state          |
| 90210 | CA     | Los Angeles  | LAX_Region     | msa            |

---

## ⚙️ Lookup Flow (Web App)

1. **User selects a state**
2. App checks if the state requires:
   - No further input (e.g., GA → statewide)
   - A ZIP, county, or MSA input
3. Normalize user input to `region_value`
4. Query the `rates` table using `cpt_code`, `modifier`, and `region_value`

---

## ✅ State Rate Mapping Config (Optional JSON Example)

```json
{
  "GA": { "region_type": "state" },
  "CA": { "region_type": "zip" },
  "TX": { "region_type": "county" },
  "FL": { "region_type": "msa" }
}
