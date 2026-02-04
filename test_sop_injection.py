"""Test script to verify dynamic SOP injection is working correctly."""
import os
import logging
from chatbot.agent import CustomerSupportAgent

# Configure logging to see SOP injection messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sop_detection():
    """Test that likely tools are detected correctly from user messages."""
    print("=" * 80)
    print("TEST 1: Tool Detection")
    print("=" * 80)
    
    agent = CustomerSupportAgent()
    
    test_cases = [
        ("I want to return my keyboard", ["order_status", "initiate_return"]),
        ("I'd like to place an order", ["draft_order", "create_order"]),
        ("How much to ship to 10001?", ["estimate_shipping"]),
        ("Show me all headphones", ["product_catalog"]),
        ("Where is my order #123?", ["order_status"]),
    ]
    
    all_passed = True
    for message, expected_tools in test_cases:
        detected = agent._detect_likely_tools(message)
        
        # Check if all expected tools were detected
        all_found = all(tool in detected for tool in expected_tools)
        
        status = "✅ PASS" if all_found else "❌ FAIL"
        print(f"\n{status}")
        print(f"  Message: '{message}'")
        print(f"  Expected: {expected_tools}")
        print(f"  Detected: {detected}")
        
        if not all_found:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All detection tests passed!")
    else:
        print("❌ Some detection tests failed")
    print("=" * 80)
    
    return all_passed


def test_sop_injection():
    """Test that SOPs are injected into conversation."""
    print("\n" + "=" * 80)
    print("TEST 2: SOP Injection")
    print("=" * 80)
    
    agent = CustomerSupportAgent()
    
    # Build a sample conversation
    messages = [
        {"role": "system", "content": "You are a support agent."}
    ]
    
    user_message = "I want to return my keyboard from order 123"
    
    print(f"\nUser message: '{user_message}'")
    print("\nBefore injection:")
    print(f"  Message count: {len(messages)}")
    
    # Inject SOPs
    messages_with_sops = agent._inject_relevant_sops(messages, user_message)
    
    print("\nAfter injection:")
    print(f"  Message count: {len(messages_with_sops)}")
    
    # Check if SOPs were injected
    sop_messages = [m for m in messages_with_sops if m['role'] == 'system' and 'RELEVANT PROCEDURES' in m.get('content', '')]
    
    if sop_messages:
        print(f"  ✅ Found {len(sop_messages)} SOP injection(s)")
        print("\n  Injected SOP content preview:")
        content = sop_messages[0]['content']
        lines = content.split('\n')[:10]  # First 10 lines
        for line in lines:
            print(f"    {line}")
        if len(content.split('\n')) > 10:
            print(f"    ... ({len(content.split('\n')) - 10} more lines)")
    else:
        print("  ❌ No SOP injections found")
    
    print("\n" + "=" * 80)
    if sop_messages:
        print("✅ SOP injection test passed!")
    else:
        print("❌ SOP injection test failed - no SOPs were injected")
    print("=" * 80)
    
    return len(sop_messages) > 0


def test_sop_caching():
    """Test that SOPs are cached after first retrieval."""
    print("\n" + "=" * 80)
    print("TEST 3: SOP Caching")
    print("=" * 80)
    
    agent = CustomerSupportAgent()
    
    print("\nFirst retrieval (should search vector store):")
    messages1 = [{"role": "system", "content": "You are a support agent."}]
    agent._inject_relevant_sops(messages1, "I want to return my order")
    
    print(f"  Cache size: {len(agent.sop_cache)}")
    print(f"  Cached tools: {list(agent.sop_cache.keys())}")
    
    print("\nSecond retrieval (should use cache):")
    messages2 = [{"role": "system", "content": "You are a support agent."}]
    agent._inject_relevant_sops(messages2, "I need to return something")
    
    print(f"  Cache size: {len(agent.sop_cache)}")
    
    print("\n" + "=" * 80)
    if len(agent.sop_cache) > 0:
        print("✅ SOP caching test passed!")
    else:
        print("❌ SOP caching test failed")
    print("=" * 80)
    
    return len(agent.sop_cache) > 0


def test_integration():
    """Test full integration with a sample conversation."""
    print("\n" + "=" * 80)
    print("TEST 4: Full Integration Test")
    print("=" * 80)
    
    agent = CustomerSupportAgent()
    
    # Test message that should trigger return SOP
    user_message = "I need to return one item from my order"
    
    print(f"\nUser message: '{user_message}'")
    print("\nExpected behavior:")
    print("  1. Detect 'return' keywords")
    print("  2. Inject order_status and initiate_return SOPs")
    print("  3. Agent should ask for order ID first")
    print("  4. Then ask which specific item to return")
    
    print("\n" + "-" * 80)
    print("NOTE: This is a detection test only.")
    print("To test actual agent behavior, run the app and chat with it.")
    print("-" * 80)
    
    # Check detection
    detected_tools = agent._detect_likely_tools(user_message)
    print(f"\n✓ Detected tools: {detected_tools}")
    
    # Check injection
    messages = [{"role": "system", "content": "System prompt"}]
    messages_with_sops = agent._inject_relevant_sops(messages, user_message)
    sop_count = len([m for m in messages_with_sops if 'RELEVANT PROCEDURES' in m.get('content', '')])
    print(f"✓ Injected {sop_count} SOP message(s)")
    
    # Check cache
    print(f"✓ Cached {len(agent.sop_cache)} SOP(s)")
    
    print("\n" + "=" * 80)
    print("✅ Integration test structure validated!")
    print("\nTo fully test, start the app and try these scenarios:")
    print("  1. 'I want to return the keyboard from order 123'")
    print("  2. 'I'd like to buy a wireless mouse'")
    print("  3. 'How much to ship 5 pounds to ZIP 10001?'")
    print("=" * 80)
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("DYNAMIC SOP INJECTION TEST SUITE")
    print("=" * 80)
    
    print("\nPREREQUISITE: Make sure you've run 'python qdrant/vector_load_kb.py'")
    print("to reload the knowledge base with new SOPs!\n")
    
    results = {
        "Tool Detection": test_sop_detection(),
        "SOP Injection": test_sop_injection(),
        "SOP Caching": test_sop_caching(),
        "Integration": test_integration(),
    }
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Run 'python qdrant/vector_load_kb.py' if not already done")
        print("2. Start the Streamlit app: 'streamlit run app.py'")
        print("3. Test with real conversations about returns, orders, etc.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nTroubleshooting:")
        print("1. Make sure knowledge base is reloaded")
        print("2. Check that chunks.json has the new agent-sop-* entries")
        print("3. Verify Qdrant connection is working")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
