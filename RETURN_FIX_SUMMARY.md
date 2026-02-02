# Return Refund Calculation Fix

## Problem
When initiating a return for a single item from an order with multiple items, the system was refunding the entire order total instead of just the price of the individual item being returned.

## Root Cause
The `create_return` method in `database/db_manager.py` was always using the order's `total_amount` for the refund calculation, regardless of which specific items were being returned.

```python
# OLD CODE (BUGGY)
refund_amount = row['total_amount']  # Always used full order total!
```

## Database Schema Update
After implementing the fix, the schema was further improved to follow the same pattern as orders:

**Old Structure:**
- `agent_return_orders`: Stored one row per product with `product_id` and `refund_amount` directly in the table
- Problem: Required multiple return records for a single return request

**New Structure (Current):**
- `agent_return_orders`: One row per return request with `refund_total_amount`
- `agent_return_items`: Separate table storing individual items being returned (like `agent_order_items`)
- Benefits: Cleaner data model, single return ID per request, easier to query

## Solution
The fix adds support for specifying which specific items (and quantities) should be returned:

### 1. Updated Tool Schema (`tools/schemas.py`)
Added optional parameters to the `initiate_return` function:
- `product_ids`: List of specific product IDs to return
- `quantities`: List of quantities for each product

These are optional - if not provided, the entire order is returned (preserving backward compatibility).

### 2. Updated Implementation (`tools/implementations.py`)
The `initiate_return` method now:
- Accepts `product_ids` and `quantities` parameters
- Validates that the products exist in the order
- Validates that the quantities don't exceed what was ordered
- Passes this information to the database layer

### 3. Updated Database Layer (`database/db_manager.py`)
The `create_return` method now:
- Accepts optional `product_ids` and `quantities` parameters
- If not provided, defaults to returning all items in the order
- Calculates refund based on the `price_at_purchase` for each specific item
- Creates ONE return order record with the total refund amount
- Creates separate return item records in `agent_return_items` table for each product

```python
# NEW CODE (FIXED)
# Calculate total refund
for product_id, quantity in zip(product_ids, quantities):
    item_refund = float(item['price_at_purchase']) * quantity
    refund_total_amount += item_refund

# Create single return order
INSERT INTO agent_return_orders (order_id, return_reason, refund_total_amount)

# Create return items
for each item:
    INSERT INTO agent_return_items (return_id, product_id, quantity, price_at_purchase)
```

## Usage Examples

### Example 1: Return a single item from a multi-item order
```python
# Order has: 2x Product #1, 1x Product #2, 3x Product #3
tools.initiate_return(
    order_id=123,
    return_reason="Defective item",
    product_ids=[1],      # Return only Product #1
    quantities=[1]        # Return just 1 unit
)
# Refund: Price of 1 unit of Product #1 only
```

### Example 2: Return multiple specific items
```python
# Order has: 3x Product #2, 2x Product #3, 1x Product #4
tools.initiate_return(
    order_id=124,
    return_reason="Wrong size",
    product_ids=[2, 3],   # Return Products #2 and #3
    quantities=[2, 1]     # Return 2 units of #2, 1 unit of #3
)
# Refund: (Price of Product #2 × 2) + (Price of Product #3 × 1)
```

### Example 3: Return entire order (backward compatible)
```python
tools.initiate_return(
    order_id=125,
    return_reason="Changed mind"
    # No product_ids or quantities specified
)
# Refund: Full order total (all items returned)
```

## Agent Behavior
When a user asks to return items, the agent will now:

1. **Ask for specifics** if the order has multiple items:
   - "Which item(s) would you like to return?"
   - "How many units of each?"

2. **Calculate correct refund** based on:
   - The price at purchase (not current price)
   - The specific quantity being returned

3. **Provide accurate information** to the customer:
   - Expected refund amount
   - Which items are being returned

## Agent Guidance Updates

To ensure the agent uses the new parameters correctly, I updated:

### 1. System Prompt (`chatbot/prompts.py`)
Added specific instructions for return processing:
- Check order details first using `order_status`
- For partial returns, ask which specific items to return
- **ALWAYS use `product_ids` and `quantities` for partial returns**
- Only omit these parameters when returning the entire order

### 2. Tool Schema Description (`tools/schemas.py`)
Made the description more explicit:
- Emphasized that `product_ids` and `quantities` are REQUIRED for partial returns
- Warned that omitting them returns the ENTIRE order
- Added clear examples in parameter descriptions

### 3. Enhanced Logging (`tools/implementations.py`)
Added detailed logging to track:
- What parameters are passed to `initiate_return`
- How many items are in the order
- Which specific items are being returned
- Clear success messages showing returned items and refund amounts

## Testing
Run the test scripts to verify the fix:

```bash
# Test the core functionality
python test_return_fix.py

# Test single item return specifically (recommended)
python test_single_item_return.py
```

The `test_single_item_return.py` script specifically tests:
- ✅ Creating an order with 4 items
- ✅ Returning ONLY 1 specific item
- ✅ Verifying only 1 return record is created (not 4)
- ✅ Verifying the refund matches the single item price

## Benefits
1. **Accurate refunds**: Customers only get refunded for items they're actually returning
2. **Partial returns**: Supports returning some items while keeping others
3. **Better UX**: Agent can handle complex return scenarios
4. **Backward compatible**: Old behavior (return entire order) still works if no products specified
