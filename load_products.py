"""Script to load product data into the database."""
import logging
from database.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Initialize database manager
db = DatabaseManager()

print("\n=== Loading product data ===\n")

# Read and execute the product insert SQL
with open('database/product_insert.sql', 'r') as f:
    sql = f.read()

try:
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            conn.commit()
            print("Product data loaded successfully!")
            
            # Verify
            cursor.execute("SELECT COUNT(*) FROM agent_products")
            count = cursor.fetchone()[0]
            print(f"Total products in database: {count}")
            
except Exception as e:
    print(f"Error loading data: {e}")
