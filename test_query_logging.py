"""Test script to demonstrate query logging functionality."""
import logging
import sys
from database.db_manager import DatabaseManager

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Enable DEBUG level logging to see query details
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see query logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_query_logging():
    """Test various database operations to see query logging."""
    print("=" * 80)
    print("QUERY LOGGING TEST")
    print("=" * 80)
    print("\nThis test demonstrates the new query logging functionality.")
    print("Watch the console output to see SQL queries and parameters.\n")
    
    db = DatabaseManager()
    
    # Test 1: Simple SELECT
    print("\n" + "-" * 80)
    print("TEST 1: Get Product by ID")
    print("-" * 80)
    product = db.get_product_by_id(1)
    if product:
        print(f"✅ Retrieved product: {product['name']}")
    else:
        print("❌ Product not found")
    
    # Test 2: SELECT with WHERE clause
    print("\n" + "-" * 80)
    print("TEST 2: Get Products by Category")
    print("-" * 80)
    products = db.get_products(category='Keyboards')
    print(f"✅ Retrieved {len(products)} keyboard products")
    
    # Test 3: SELECT with multiple parameters
    print("\n" + "-" * 80)
    print("TEST 3: Search Products")
    print("-" * 80)
    products = db.get_products(search_query='wireless')
    print(f"✅ Retrieved {len(products)} products matching 'wireless'")
    
    # Test 4: Get order with JOIN
    print("\n" + "-" * 80)
    print("TEST 4: Get Order Details (with items)")
    print("-" * 80)
    order = db.get_order(1)
    if order:
        print(f"✅ Retrieved order for {order['customer_name']}")
        print(f"   Order has {len(order.get('items', []))} item(s)")
    else:
        print("ℹ️  Order 1 not found (this is OK if you haven't created any orders)")
    
    # Test 5: Get shipping estimates
    print("\n" + "-" * 80)
    print("TEST 5: Estimate Shipping Costs")
    print("-" * 80)
    estimates = db.estimate_shipping('10001', 5.0)
    if estimates:
        print(f"✅ Retrieved {len(estimates)} shipping estimates")
        for est in estimates:
            print(f"   {est['carrier']} {est['service_type']}: ${est['rate']:.2f} ({est['delivery_days']} days)")
    else:
        print("ℹ️  No shipping rates found for ZIP 10001")
    
    # Test 6: Get support tickets
    print("\n" + "-" * 80)
    print("TEST 6: Get Support Tickets")
    print("-" * 80)
    tickets = db.get_support_tickets(status='open')
    print(f"✅ Retrieved {len(tickets)} open support tickets")
    
    # Test 7: Get returns
    print("\n" + "-" * 80)
    print("TEST 7: Get Returns")
    print("-" * 80)
    returns = db.get_returns(status='pending')
    print(f"✅ Retrieved {len(returns)} pending returns")
    
    print("\n" + "=" * 80)
    print("✅ QUERY LOGGING TEST COMPLETE")
    print("=" * 80)
    print("\nReview the console output above to see:")
    print("  • SQL Query: The exact SQL statement with placeholders")
    print("  • Parameters: The actual values being substituted")
    print("  • Results: High-level summary of what was returned")
    print("\nAll queries are now logged with full details for debugging!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_query_logging()
