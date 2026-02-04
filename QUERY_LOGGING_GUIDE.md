# Query Logging Guide

## Overview
All database queries in `database/db_manager.py` now log the full SQL query and parameters for debugging purposes.

## How to Enable Query Logging

⚠️ **IMPORTANT**: The query logs are sent at **DEBUG** level. Python's default logging level is WARNING, so you **MUST** explicitly enable DEBUG logging to see the queries. If you're only seeing INFO messages and not DEBUG messages, your logging level is not set to DEBUG.

The query logs are sent at **DEBUG** level, so you need to configure your logging to see them.

### Method 1: Using Environment Variable (Easiest for app.py)

For the main Streamlit app (`app.py`), simply set the `DEBUG_QUERIES` environment variable:

**Windows (PowerShell):**
```powershell
$env:DEBUG_QUERIES="true"
streamlit run app.py
```

**Windows (Command Prompt):**
```cmd
set DEBUG_QUERIES=true
streamlit run app.py
```

**Linux/Mac:**
```bash
DEBUG_QUERIES=true streamlit run app.py
```

Or set it in your `.env` file:
```
DEBUG_QUERIES=true
```

### Method 2: Enable in your script

Add this at the top of your script (e.g., `test_*.py`):

```python
import logging

# Enable DEBUG level logging for ALL modules (including database)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**⚠️ IMPORTANT**: Call `logging.basicConfig()` BEFORE importing or creating DatabaseManager, otherwise it won't take effect!

### Method 3: Enable only for database module

If you only want to see database queries without other debug messages:

```python
import logging

# Set root logger to INFO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable DEBUG only for database module
logging.getLogger('database.db_manager').setLevel(logging.DEBUG)
```

### Method 4: Save to a file

To save all query logs to a file:

```python
import logging

# Create file handler
file_handler = logging.FileHandler('queries.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Add handler to database logger
logging.getLogger('database.db_manager').addHandler(file_handler)
logging.getLogger('database.db_manager').setLevel(logging.DEBUG)
```

## Example Output

When enabled, you'll see logs like:

```
2026-02-03 10:15:23 - database.db_manager - DEBUG - SQL Query: SELECT * FROM agent_products WHERE id = %s
2026-02-03 10:15:23 - database.db_manager - DEBUG - Parameters: (123,)
2026-02-03 10:15:23 - database.db_manager - INFO - get_product_by_id query for product_id=123 returned: product found
```

For complex queries with multiple parameters:

```
2026-02-03 10:16:45 - database.db_manager - DEBUG - SQL Query: INSERT INTO agent_orders (customer_name, customer_email, customer_phone, shipping_address, total_amount, status) VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id
2026-02-03 10:16:45 - database.db_manager - DEBUG - Parameters: ('John Doe', 'john@example.com', '555-1234', '123 Main St', 99.99)
2026-02-03 10:16:45 - database.db_manager - INFO - create_order: Created order_id=456 for customer=John Doe, total_amount=$99.99
```

## What's Logged

For every database query, you'll see:
- **SQL Query**: The exact SQL statement with parameter placeholders (`%s`)
- **Parameters**: The actual values being substituted into the query
- **Result Info**: High-level summary of what was returned (at INFO level)

This makes it much easier to:
- Debug query issues
- Verify correct parameter binding
- Track down performance problems
- Understand the exact SQL being executed
