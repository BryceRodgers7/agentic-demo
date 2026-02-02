# Returns Schema Migration Summary

## Date: 2026-02-02

## Overview
Migrated the returns database structure from a flat table to a normalized structure that mirrors the orders/order_items pattern. This provides better data modeling and cleaner separation of concerns.

## Schema Changes

### Before (Old Structure)
```sql
CREATE TABLE IF NOT EXISTS agent_return_orders (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,  -- ❌ Product stored directly in return
    return_reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    refund_amount DECIMAL(10, 2),  -- ❌ Individual item refund
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES agent_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES agent_products(id) ON DELETE CASCADE
);
```

**Problem:** Required multiple rows in `agent_return_orders` for a single return request with multiple items.

### After (New Structure)
```sql
-- Main return order (one per return request)
CREATE TABLE IF NOT EXISTS agent_return_orders (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    return_reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    refund_total_amount DECIMAL(10, 2),  -- ✅ Total refund for entire return
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES agent_orders(id) ON DELETE CASCADE
);

-- Return items (one per product in the return)
CREATE TABLE IF NOT EXISTS agent_return_items (
    id SERIAL PRIMARY KEY,
    return_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_purchase DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (return_id) REFERENCES agent_return_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES agent_products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_return_items_return_id ON agent_return_items(return_id);
```

**Benefits:**
- ✅ One return order per return request
- ✅ Clean separation of return metadata and item details
- ✅ Matches the orders/order_items pattern
- ✅ Easier to query and maintain
- ✅ Better data integrity

## Files Updated

### 1. Database Schema (`database/schema.sql`)
- Modified `agent_return_orders` table structure
- Added new `agent_return_items` table
- Added index on `return_items.return_id`

### 2. Insert Data (`database/returns_insert.sql`)
- Updated to insert into both tables
- Separated return orders from return items
- Added proper foreign key relationships

### 3. Database Manager (`database/db_manager.py`)

#### `create_return()` method:
- **Before:** Created multiple rows in `agent_return_orders`, one per product
- **After:** Creates one row in `agent_return_orders` with total refund, plus separate rows in `agent_return_items` for each product

```python
# OLD APPROACH
for product_id, quantity in zip(product_ids, quantities):
    cursor.execute(
        """INSERT INTO agent_return_orders (order_id, return_reason, refund_amount, product_id)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (order_id, return_reason, item_refund, product_id)
    )

# NEW APPROACH
# Create single return order
cursor.execute(
    """INSERT INTO agent_return_orders (order_id, return_reason, refund_total_amount)
       VALUES (%s, %s, %s) RETURNING id""",
    (order_id, return_reason, refund_total_amount)
)
# Create return items
for item_data in return_items_data:
    cursor.execute(
        """INSERT INTO agent_return_items (return_id, product_id, quantity, price_at_purchase)
           VALUES (%s, %s, %s, %s)""",
        (return_id, item_data['product_id'], item_data['quantity'], item_data['price_at_purchase'])
    )
```

#### `get_return()` method:
- **Before:** Returned single row from `agent_return_orders`
- **After:** Returns return order with joined `items` array from `agent_return_items`

```python
# NEW APPROACH
cursor.execute("SELECT * FROM agent_return_orders WHERE id = %s", (return_id,))
return_order = dict(cursor.fetchone())

cursor.execute(
    """SELECT ri.*, p.name as product_name 
       FROM agent_return_items ri
       JOIN agent_products p ON ri.product_id = p.id
       WHERE ri.return_id = %s""",
    (return_id,)
)
return_order['items'] = [dict(row) for row in cursor.fetchall()]
```

#### `get_all_returns()` method:
- Updated to include items for each return

### 4. Tool Implementation (`tools/implementations.py`)

#### `initiate_return()` method:
- Updated field reference: `refund_amount` → `refund_total_amount`
- Updated success messages to use correct field name
- Return info now includes `items` array

### 5. Test Files

#### `test_return_fix.py`:
- Updated all `refund_amount` references to `refund_total_amount`

#### `test_single_item_return.py`:
- Updated `refund_amount` to `refund_total_amount`
- Updated to access `product_id` from `items` array instead of directly from return record
- Updated validation logic to check `len(returned_items) == 1`

### 6. Frontend (`frontend/5_Returns.py`)
- Updated metrics to use `refund_total_amount`
- Updated column configuration for dataframe
- Excluded `items` column from main table view
- Added detailed items view in return details section
- Shows returned products with quantity and price

### 7. Documentation (`RETURN_FIX_SUMMARY.md`)
- Added section explaining schema changes
- Updated code examples to reflect new structure
- Documented benefits of normalized structure

## Data Migration Notes

### For Existing Data:
If you have existing return data in the old format, you'll need to:

1. **Create new tables:**
   ```sql
   -- Run schema.sql to create new structure
   ```

2. **Migrate data:**
   ```sql
   -- For each old return, create new return order
   INSERT INTO agent_return_orders (id, order_id, return_reason, status, refund_total_amount, created_at, updated_at, processed_at)
   SELECT 
       id,
       order_id,
       return_reason,
       status,
       refund_amount as refund_total_amount,
       created_at,
       updated_at,
       processed_at
   FROM agent_return_orders_old
   GROUP BY order_id, return_reason, status, created_at, updated_at, processed_at;
   
   -- Create return items from old structure
   INSERT INTO agent_return_items (return_id, product_id, quantity, price_at_purchase)
   SELECT 
       id as return_id,
       product_id,
       1 as quantity,  -- Assuming quantity 1 for old returns
       refund_amount as price_at_purchase
   FROM agent_return_orders_old;
   ```

3. **Verify migration:**
   ```bash
   python test_single_item_return.py
   python test_return_fix.py
   ```

## Testing

All tests updated and passing:
- ✅ `test_return_fix.py` - Tests refund calculations
- ✅ `test_single_item_return.py` - Tests single item returns from multi-item orders
- ✅ Frontend displays returns correctly with items

## API Changes

### Return Response Structure

**Before:**
```json
{
  "id": 1,
  "order_id": 26,
  "product_id": 1,
  "return_reason": "Defective",
  "status": "pending",
  "refund_amount": 399.00,
  "created_at": "2025-01-04T10:15:00"
}
```

**After:**
```json
{
  "id": 1,
  "order_id": 26,
  "return_reason": "Defective",
  "status": "pending",
  "refund_total_amount": 399.00,
  "created_at": "2025-01-04T10:15:00",
  "items": [
    {
      "id": 1,
      "return_id": 1,
      "product_id": 1,
      "product_name": "Aether X1 Headphones",
      "quantity": 1,
      "price_at_purchase": 399.00
    }
  ]
}
```

## Backward Compatibility

⚠️ **Breaking Change:** This is a breaking schema change.

- API responses now include `items` array instead of direct `product_id`
- Field renamed: `refund_amount` → `refund_total_amount`
- All consuming code must be updated (completed in this migration)

## Benefits of New Structure

1. **Better Data Model:** Matches orders pattern (order → order_items, return → return_items)
2. **Cleaner Queries:** Single return ID per request
3. **Accurate Totals:** Clear separation between item-level and total refunds
4. **Scalability:** Easy to add more return metadata without affecting items
5. **Reporting:** Simpler to generate reports on return patterns
6. **Integrity:** Better foreign key relationships and constraints

## Next Steps

1. ✅ All code updated
2. ✅ All tests passing
3. ✅ Frontend updated
4. ✅ Documentation updated
5. 🔄 Deploy schema changes to database
6. 🔄 Migrate any existing production data (if applicable)
7. 🔄 Update any external integrations or API consumers
