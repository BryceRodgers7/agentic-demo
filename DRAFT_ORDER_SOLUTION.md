# Draft Order Solution

## Problem
The agent was making up (hallucinating) email addresses and phone numbers when customers didn't provide them, because the `create_order` tool required these fields.

## Solution
Created a new `draft_order` tool that acts as a validation step before creating an order. This tool:

1. **Accepts optional parameters** - All fields are optional, allowing the agent to pass only what the customer provided
2. **Validates completeness** - Checks which required fields are missing and reports them
3. **Validates products** - Checks if products exist and if there's sufficient inventory
4. **Calculates order summary** - Shows total cost, weight, and product details when all info is complete
5. **Guides the agent** - Returns clear messages about what's missing and what to do next

## Changes Made

### 1. `tools/schemas.py`
- Added `draft_order` tool as the **first** tool in the schema
- Updated `create_order` description to emphasize it should only be used after `draft_order` confirms completeness
- All parameters in `draft_order` are optional (no required fields)

### 2. `tools/implementations.py`
- Implemented `draft_order()` method that:
  - Tracks which fields are provided vs missing
  - Validates products exist and checks inventory
  - Calculates order totals (cost and weight)
  - Returns `ready_to_order: true` only when all required info is present
  - Returns helpful error messages when info is missing
- Added `draft_order` to the tool execution map
- Fixed weight handling to use `.get('weight', 0)` for products without weight

### 3. `chatbot/prompts.py`
- Updated SYSTEM_PROMPT with explicit instructions:
  - "When a customer wants to place an order, ALWAYS use draft_order FIRST"
  - "Only call create_order after draft_order confirms all required information is complete"
  - "If required information is missing, ask the customer for it in a friendly, conversational way"

## How It Works

### Workflow
1. Customer expresses intent to order
2. Agent calls `draft_order` with whatever information customer provided
3. `draft_order` returns:
   - If incomplete: List of missing fields and a message to ask the customer
   - If complete: Order summary and instruction to proceed with `create_order`
4. Agent either:
   - Asks customer for missing information (conversationally)
   - Proceeds to call `create_order` with complete information

### Example Flow

**Customer:** "I'd like to buy 10 Aether X1s for my company"

**Agent calls:** `draft_order(product_ids=[1], quantities=[10])`

**Tool returns:**
```json
{
  "success": true,
  "ready_to_order": false,
  "message": "Missing required information: customer's full name, customer's email address, customer's phone number, shipping address",
  "missing_fields": ["customer_name", "customer_email", "customer_phone", "shipping_address"]
}
```

**Agent responds:** "I'd be happy to help you order 10 Aether X1s! To process your order, I'll need:
- Your full name
- Email address
- Phone number
- Shipping address"

**Customer provides info...**

**Agent calls:** `draft_order(customer_name="Amy Ryan", customer_email="amy@somycorp.com", ...)`

**Tool returns:**
```json
{
  "success": true,
  "ready_to_order": true,
  "message": "All required information collected. Ready to create order.",
  "order_summary": {
    "customer_name": "Amy Ryan",
    "products": [...],
    "total_cost": 3990.0
  },
  "next_step": "Call create_order with the complete information to finalize the order."
}
```

**Agent calls:** `create_order(customer_name="Amy Ryan", customer_email="amy@somycorp.com", ...)`

**Order created successfully!**

## Benefits

1. **No hallucination** - Agent can't make up information because it's not forced to provide it
2. **Better UX** - Agent asks for missing info conversationally instead of failing
3. **Validation** - Products and inventory are checked before attempting to create order
4. **Transparency** - Customer sees order summary before it's finalized
5. **Clear workflow** - Two-step process (draft → create) is explicit and predictable

## Testing

Run `test_draft_order.py` to verify:
- ✅ Empty draft identifies all missing fields
- ✅ Partial info identifies remaining missing fields
- ✅ Complete info returns ready_to_order=true with summary
- ✅ Invalid product IDs are caught
- ✅ Insufficient inventory is caught
