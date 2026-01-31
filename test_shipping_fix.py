"""Test script to verify the shipping estimate fix."""
from database.db_manager import DatabaseManager
from tools.implementations import ToolImplementations

def test_shipping_estimate():
    """Test that shipping estimates work for ZIP 60601."""
    print("Testing shipping estimate fix for ZIP code 60601...\n")
    
    # Test at database level
    print("1. Testing database layer:")
    db = DatabaseManager()
    estimates = db.estimate_shipping(destination_zip="60601", weight_lbs=15.0, service_level="overnight")
    
    if estimates:
        print(f"   ✓ Found {len(estimates)} shipping option(s):")
        for est in estimates:
            print(f"     - {est['carrier']} {est['service_type']}: ${est['estimated_cost']} ({est['estimated_days']} days)")
    else:
        print("   ✗ No estimates found!")
    
    # Test at tool level
    print("\n2. Testing tool implementation layer:")
    tools = ToolImplementations()
    result = tools.estimate_shipping(destination_zip="60601", weight=15.0, service_level="overnight")
    
    if result['success']:
        print(f"   ✓ Tool returned {result['count']} option(s)")
        print(f"   Message: {result['message']}")
    else:
        print(f"   ✗ Tool failed: {result['error']}")
    
    print("\n" + "="*60)
    print("Test complete!")

if __name__ == "__main__":
    test_shipping_estimate()
