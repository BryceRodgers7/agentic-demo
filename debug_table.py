"""Debug script to check if products table has any data."""
import logging
from database.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Initialize database manager
db = DatabaseManager()

# Get connection and check table contents
import psycopg2.extras

print("\n=== Checking agent_products table ===\n")
try:
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # Count total rows
            cursor.execute("SELECT COUNT(*) FROM agent_products")
            count = cursor.fetchone()[0]
            print(f"Total rows in agent_products: {count}")
            
            if count > 0:
                # Get first few rows
                cursor.execute("SELECT id, name, category FROM agent_products LIMIT 5")
                rows = cursor.fetchall()
                print("\nFirst 5 products:")
                for row in rows:
                    print(f"  ID {row['id']}: {row['name']} ({row['category']})")
            else:
                print("\nThe table is EMPTY! Data needs to be inserted.")
                
except Exception as e:
    print(f"Error: {e}")
