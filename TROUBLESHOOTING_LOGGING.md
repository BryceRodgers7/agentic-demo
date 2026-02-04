# Troubleshooting Query Logging

## Problem: I don't see DEBUG statements, only INFO statements

This is the most common issue. Here's how to fix it:

### Root Cause
Python's default logging level is **WARNING**. This means:
- ✅ You'll see: ERROR, WARNING, INFO
- ❌ You won't see: DEBUG

The query logging uses DEBUG level, so you must explicitly enable it.

### Solution 1: Check your logging.basicConfig()

Make sure you're setting `level=logging.DEBUG`:

```python
import logging

# CORRECT - Will show DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,  # This is key!
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

```python
# WRONG - Will NOT show DEBUG messages (default is WARNING)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

```python
# WRONG - Will NOT show DEBUG messages
logging.basicConfig(
    level=logging.INFO,  # INFO is not enough, must be DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Solution 2: Set it BEFORE importing DatabaseManager

Logging configuration must happen BEFORE you import or use DatabaseManager:

```python
# CORRECT ORDER
import logging

# Configure FIRST
logging.basicConfig(level=logging.DEBUG)

# Import AFTER
from database.db_manager import DatabaseManager

# Use
db = DatabaseManager()
```

```python
# WRONG ORDER - Won't work!
from database.db_manager import DatabaseManager

# Too late! DatabaseManager logger already created
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Solution 3: For Streamlit (app.py)

Use the environment variable method:

**Windows PowerShell:**
```powershell
$env:DEBUG_QUERIES="true"
streamlit run app.py
```

**Windows Command Prompt:**
```cmd
set DEBUG_QUERIES=true
streamlit run app.py
```

Or add to your `.env` file:
```
DEBUG_QUERIES=true
```

### Solution 4: Force the database logger level

If nothing else works, force it after import:

```python
import logging
from database.db_manager import DatabaseManager

# Force the database logger to DEBUG
logging.getLogger('database.db_manager').setLevel(logging.DEBUG)

# Also make sure root logger outputs DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

db = DatabaseManager()
```

## Quick Test

Run this script to verify DEBUG logging works:

```python
import logging

# Enable DEBUG
logging.basicConfig(level=logging.DEBUG)

# Import after configuring
from database.db_manager import DatabaseManager

# This should show DEBUG messages
db = DatabaseManager()
product = db.get_product_by_id(1)
```

You should see output like:
```
DEBUG - SQL Query: SELECT * FROM agent_products WHERE id = %s
DEBUG - Parameters: (1,)
INFO - get_product_by_id query for product_id=1 returned: product found
```

If you only see the INFO line, your DEBUG level is not enabled correctly.

## Logging Level Hierarchy

From most verbose to least verbose:
1. **DEBUG** ← You need this level to see queries
2. **INFO** ← You see this but not queries? Level is too high!
3. **WARNING** ← Default Python level
4. **ERROR**
5. **CRITICAL**
