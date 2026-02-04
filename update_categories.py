"""Update product categories to lowercase singular form."""
import psycopg2
from database.db_manager import DatabaseManager

def update_categories():
    """Update all product categories to lowercase singular."""
    db = DatabaseManager()
    
    # Category mapping from old to new
    category_map = {
        'Headphones': 'headphone',
        'Cameras': 'camera',
        'Monitors': 'monitor',
        'Keyboards': 'keyboard',
        'Speakers': 'speaker',
        'Accessories': 'accessory'
    }
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                for old_cat, new_cat in category_map.items():
                    query = "UPDATE agent_products SET category = %s WHERE category = %s"
                    cursor.execute(query, (new_cat, old_cat))
                    print(f"Updated {cursor.rowcount} products from '{old_cat}' to '{new_cat}'")
                
                conn.commit()
                print("\n✓ All categories updated successfully!")
                
                # Show current category distribution
                cursor.execute("SELECT category, COUNT(*) FROM agent_products GROUP BY category ORDER BY category")
                print("\nCurrent category distribution:")
                for row in cursor.fetchall():
                    print(f"  {row[0]}: {row[1]} products")
                    
    except Exception as e:
        print(f"Error updating categories: {e}")
        raise

if __name__ == "__main__":
    update_categories()
