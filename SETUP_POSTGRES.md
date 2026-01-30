# PostgreSQL/Supabase Setup Guide

## Quick Start

### 1. Install Dependencies

The required PostgreSQL driver is already listed in `requirements.txt`. If you haven't installed it yet:

```bash
pip install -r requirements.txt
```

### 2. Configure Database URL

Make sure your `.env` file or environment has the Supabase connection string:

```bash
SUPADATABASE_URL=postgresql://user:password@host.supabase.co:5432/postgres
```

**Note:** You mentioned you've already added the database URL, so this should be set.

### 3. Run the Application

When you start the application, it will automatically:
- Connect to your Supabase PostgreSQL database
- Create all necessary tables (products, orders, shipping_rates, support_tickets, return_orders)
- Create indexes for performance

```bash
streamlit run app.py
```

## Database Schema

The following tables will be created automatically:

- **products** - Product catalog with inventory tracking
- **orders** - Customer orders with status tracking
- **order_items** - Items in each order (many-to-many relationship)
- **shipping_rates** - Shipping options and pricing
- **support_tickets** - Customer support requests
- **return_orders** - Return requests and refunds

## Loading Sample Data

If you want to load sample data, you can execute the SQL insert files directly in your Supabase dashboard or via psql:

```bash
psql $SUPADATABASE_URL -f database/product_insert.sql
psql $SUPADATABASE_URL -f database/orders_insert.sql
psql $SUPADATABASE_URL -f database/shipping_rates_insert.sql
psql $SUPADATABASE_URL -f database/support_tickets_insert.sql
psql $SUPADATABASE_URL -f database/returns_insert.sql
```

Or through the Supabase SQL Editor (copy and paste each file's contents).

## Verification

To verify the migration worked:

1. Start the application: `streamlit run app.py`
2. Check that no database connection errors occur
3. Try accessing the different pages in the frontend (Products, Orders, etc.)
4. Test creating a support ticket or viewing product catalog

## Troubleshooting

### Connection Error
If you get a connection error, verify:
- `SUPADATABASE_URL` environment variable is set correctly
- Your Supabase database is accessible
- The connection string format is: `postgresql://user:password@host:port/database`

### Permission Errors
If you get permission errors on table creation:
- Ensure your Supabase user has CREATE TABLE permissions
- Check that your connection uses the correct credentials

### Import Errors
If you get `psycopg2` import errors:
- Run `pip install psycopg2-binary`
- Or `pip install -r requirements.txt`

## What Changed

All SQLite-specific code has been replaced with PostgreSQL equivalents:
- ✅ Connection management updated
- ✅ Query syntax converted (? → %s)
- ✅ Schema updated (AUTOINCREMENT → SERIAL, REAL → DECIMAL)
- ✅ All database operations tested and updated
- ✅ Data types optimized for PostgreSQL

See `MIGRATION_NOTES.md` for detailed technical changes.
