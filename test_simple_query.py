"""Simple test to verify query logging is working."""
import logging

# IMPORTANT: Configure logging BEFORE importing DatabaseManager
logging.basicConfig(
    level=logging.DEBUG,  # Must be DEBUG to see queries
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now import (after configuring logging)
from database.db_manager import DatabaseManager

print("=" * 80)
print("SIMPLE QUERY LOGGING TEST")
print("=" * 80)
print("\nIf query logging is working, you should see DEBUG messages like:")
print("  'DEBUG - SQL Query: SELECT * FROM ...'")
print("  'DEBUG - Parameters: ...'")
print("\nIf you only see INFO messages, your logging level is not set to DEBUG.\n")
print("-" * 80)

# Create database manager and run a simple query
db = DatabaseManager()
product = db.get_product_by_id(1)

print("-" * 80)
if product:
    print(f"\nResult: Found product '{product['name']}'")
else:
    print("\nResult: Product not found")

print("\n" + "=" * 80)
print("EXPECTED OUTPUT ABOVE:")
print("  1. DEBUG - SQL Query: SELECT 1")
print("  2. DEBUG - Parameters: None")
print("  3. INFO - Database connection successful")
print("  4. DEBUG - SQL Query: SELECT * FROM agent_products WHERE id = %s")
print("  5. DEBUG - Parameters: (1,)")
print("  6. INFO - get_product_by_id query...")
print("\nIf you saw all 6 lines above, query logging is working!")
print("If you only saw lines 3 and 6 (INFO), DEBUG is not enabled.")
print("=" * 80)
