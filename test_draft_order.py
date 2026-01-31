"""Test the draft_order functionality."""
from tools.implementations import ToolImplementations

def test_draft_order():
    """Test draft_order with various scenarios."""
    tools = ToolImplementations()
    
    print("=" * 80)
    print("TEST 1: Empty draft_order (no information provided)")
    print("=" * 80)
    result = tools.draft_order()
    print(f"Success: {result.get('success')}")
    print(f"Ready to order: {result.get('ready_to_order')}")
    print(f"Message: {result.get('message')}")
    print(f"Missing fields: {result.get('missing_fields')}")
    print()
    
    print("=" * 80)
    print("TEST 2: Partial information (name and address only)")
    print("=" * 80)
    result = tools.draft_order(
        customer_name="Amy Ryan",
        shipping_address="56538 Acroby Ave, Kansas City, MO, 60601"
    )
    print(f"Success: {result.get('success')}")
    print(f"Ready to order: {result.get('ready_to_order')}")
    print(f"Message: {result.get('message')}")
    print(f"Missing fields: {result.get('missing_fields')}")
    print(f"Provided fields: {result.get('provided_fields')}")
    print()
    
    print("=" * 80)
    print("TEST 3: All info except products")
    print("=" * 80)
    result = tools.draft_order(
        customer_name="Amy Ryan",
        customer_email="amy@somycorp.com",
        customer_phone="555-1234",
        shipping_address="56538 Acroby Ave, Kansas City, MO, 60601"
    )
    print(f"Success: {result.get('success')}")
    print(f"Ready to order: {result.get('ready_to_order')}")
    print(f"Message: {result.get('message')}")
    print(f"Missing fields: {result.get('missing_fields')}")
    print()
    
    print("=" * 80)
    print("TEST 4: Complete information with product (Aether X1)")
    print("=" * 80)
    # First, find the Aether X1 product
    products = tools.product_catalog(search_query="Aether X1")
    if products['success'] and products['count'] > 0:
        product_id = products['products'][0]['id']
        print(f"Found Aether X1 with ID: {product_id}")
        
        result = tools.draft_order(
            customer_name="Amy Ryan",
            customer_email="amy@somycorp.com",
            customer_phone="555-1234",
            shipping_address="56538 Acroby Ave, Kansas City, MO, 60601",
            product_ids=[product_id],
            quantities=[10]
        )
        print(f"Success: {result.get('success')}")
        print(f"Ready to order: {result.get('ready_to_order')}")
        print(f"Message: {result.get('message')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        
        if result.get('ready_to_order'):
            print("\n--- Order Summary ---")
            summary = result.get('order_summary', {})
            print(f"Customer: {summary.get('customer_name')}")
            print(f"Email: {summary.get('customer_email')}")
            print(f"Phone: {summary.get('customer_phone')}")
            print(f"Address: {summary.get('shipping_address')}")
            print(f"\nProducts:")
            for product in summary.get('products', []):
                print(f"  - {product['name']}: {product['quantity']} x ${product['unit_price']} = ${product['item_total']}")
            print(f"\nTotal Cost: ${summary.get('total_cost')}")
            print(f"Total Weight: {summary.get('total_weight')} lbs")
            print(f"\nNext step: {result.get('next_step')}")
    else:
        print("Could not find Aether X1 product")
    print()
    
    print("=" * 80)
    print("TEST 5: Invalid product ID")
    print("=" * 80)
    result = tools.draft_order(
        customer_name="Amy Ryan",
        customer_email="amy@somycorp.com",
        customer_phone="555-1234",
        shipping_address="56538 Acroby Ave, Kansas City, MO, 60601",
        product_ids=[99999],  # Invalid product ID
        quantities=[10]
    )
    print(f"Success: {result.get('success')}")
    print(f"Ready to order: {result.get('ready_to_order')}")
    print(f"Error: {result.get('error')}")
    print()
    
    print("=" * 80)
    print("TEST 6: Insufficient stock")
    print("=" * 80)
    # Try to order more than available
    products = tools.product_catalog(search_query="Aether X1")
    if products['success'] and products['count'] > 0:
        product_id = products['products'][0]['id']
        stock = products['products'][0]['stock_quantity']
        print(f"Available stock: {stock}")
        
        result = tools.draft_order(
            customer_name="Amy Ryan",
            customer_email="amy@somycorp.com",
            customer_phone="555-1234",
            shipping_address="56538 Acroby Ave, Kansas City, MO, 60601",
            product_ids=[product_id],
            quantities=[stock + 100]  # More than available
        )
        print(f"Success: {result.get('success')}")
        print(f"Ready to order: {result.get('ready_to_order')}")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    test_draft_order()
