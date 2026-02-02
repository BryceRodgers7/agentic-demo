"""Test script to verify single item return from multi-item order."""
import os
from database.db_manager import DatabaseManager
from tools.implementations import ToolImplementations

def test_single_item_return():
    """Test that returning one item from a multi-item order only creates one return record."""
    
    print("=" * 80)
    print("Testing Single Item Return from Multi-Item Order")
    print("=" * 80)
    
    tools = ToolImplementations()
    db = DatabaseManager()
    
    # Step 1: Create an order with 4 products
    print("\n1. Creating test order with 4 different products...")
    
    order_result = tools.create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        customer_phone="555-0000",
        shipping_address="123 Test St, Test City, TS 12345",
        product_ids=[1, 2, 3, 4],
        quantities=[1, 1, 1, 1]
    )
    
    if not order_result['success']:
        print(f"❌ Failed to create order: {order_result.get('error')}")
        return
    
    order_id = order_result['order_id']
    order = order_result['order']
    
    print(f"✅ Created order #{order_id} with {len(order['items'])} items:")
    for item in order['items']:
        print(f"   - Product #{item['product_id']}: {item['product_name']} - ${item['price_at_purchase']}")
    print(f"   Total: ${order['total_amount']}")
    
    # Step 2: Count returns before
    print("\n2. Checking returns before...")
    returns_before = db.get_all_returns()
    count_before = len([r for r in returns_before if r['order_id'] == order_id])
    print(f"   Returns for this order: {count_before}")
    
    # Step 3: Return ONLY product #2 (the second item)
    print(f"\n3. Returning ONLY product #{order['items'][1]['product_id']} ({order['items'][1]['product_name']})...")
    
    product_to_return = order['items'][1]['product_id']
    expected_refund = float(order['items'][1]['price_at_purchase'])
    
    return_result = tools.initiate_return(
        order_id=order_id,
        return_reason="Testing single item return",
        product_ids=[product_to_return],
        quantities=[1]
    )
    
    if not return_result['success']:
        print(f"❌ Failed to create return: {return_result.get('error')}")
        return
    
    print(f"✅ {return_result['message']}")
    
    # Step 4: Count returns after
    print("\n4. Verifying return records in database...")
    returns_after = db.get_all_returns()
    order_returns = [r for r in returns_after if r['order_id'] == order_id]
    count_after = len(order_returns)
    
    print(f"   Returns for this order: {count_after}")
    print(f"   New returns created: {count_after - count_before}")
    
    # Step 5: Verify only ONE return was created
    print("\n5. Validation:")
    
    if count_after - count_before == 1:
        print(f"   ✅ PASS: Only 1 return record created")
    else:
        print(f"   ❌ FAIL: Expected 1 return record, but {count_after - count_before} were created")
        print("\n   Return records created:")
        for ret in order_returns:
            if ret['id'] >= return_result['return_id']:
                items_desc = ", ".join([f"Product #{item['product_id']}" for item in ret.get('items', [])])
                print(f"      - Return #{ret['id']}: {items_desc}, Refund ${ret['refund_total_amount']}")
        return False
    
    # Verify the refund amount is correct
    new_return = order_returns[-1]
    actual_refund = float(new_return['refund_total_amount'])
    
    if abs(actual_refund - expected_refund) < 0.01:
        print(f"   ✅ PASS: Refund amount is correct (${actual_refund})")
    else:
        print(f"   ❌ FAIL: Expected refund ${expected_refund}, got ${actual_refund}")
        return False
    
    # Verify the correct product was returned
    returned_items = new_return.get('items', [])
    if len(returned_items) == 1 and returned_items[0]['product_id'] == product_to_return:
        print(f"   ✅ PASS: Correct product ID in return items ({product_to_return})")
    else:
        returned_product_ids = [item['product_id'] for item in returned_items]
        print(f"   ❌ FAIL: Expected product {product_to_return}, got {returned_product_ids}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nThe fix is working correctly:")
    print("- Only 1 return record was created")
    print("- Refund amount matches the single item price")
    print("- Correct product ID is recorded")
    
    return True


if __name__ == "__main__":
    try:
        test_single_item_return()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
