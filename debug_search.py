"""Debug script to test product search."""
import logging
from database.db_manager import DatabaseManager

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Initialize database manager
db = DatabaseManager()

# Test the exact search the agent is doing
print("\n=== Testing product search for 'Aether X1' ===\n")
results = db.get_products(category=None, search_query='Aether X1')

print(f"Number of results: {len(results)}")
print("\nResults:")
for product in results:
    print(f"  - ID: {product['id']}, Name: {product['name']}")

# Test a few variations
print("\n\n=== Testing variations ===\n")

test_queries = [
    'aether',
    'AETHER',
    'Aether',
    'X1',
    'aether x1',
    'Protis Aether',
]

for query in test_queries:
    results = db.get_products(category=None, search_query=query)
    print(f"Query '{query}': {len(results)} results")
    if results:
        print(f"  First match: {results[0]['name']}")
