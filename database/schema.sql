-- Customer Support Database Schema (PostgreSQL)

-- Products table
CREATE TABLE IF NOT EXISTS agent_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    specifications TEXT,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100),
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS agent_orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    shipping_address TEXT NOT NULL,
    zip_code VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items (for many-to-many relationship between orders and products)
CREATE TABLE IF NOT EXISTS agent_order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_purchase DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES agent_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES agent_products(id) ON DELETE CASCADE
);

-- Shipping rates table
CREATE TABLE IF NOT EXISTS agent_shipping_rates (
    id SERIAL PRIMARY KEY,
    carrier VARCHAR(100) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    base_rate DECIMAL(10, 2) NOT NULL,
    per_lb_rate DECIMAL(10, 2) DEFAULT 0,
    estimated_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support tickets table
CREATE TABLE IF NOT EXISTS agent_support_tickets (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    product_id INTEGER DEFAULT NULL,
    issue_description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    assigned_to VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES agent_products(id) ON DELETE SET NULL
);

-- Returns table
CREATE TABLE IF NOT EXISTS agent_return_orders (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    return_reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    refund_total_amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES agent_orders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_return_items (
    id SERIAL PRIMARY KEY,
    return_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_purchase DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (return_id) REFERENCES agent_return_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES agent_products(id) ON DELETE CASCADE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_orders_status ON agent_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON agent_orders(customer_name);
CREATE INDEX IF NOT EXISTS idx_products_category ON agent_products(category);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON agent_support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_return_orders_status ON agent_return_orders(status);
CREATE INDEX IF NOT EXISTS idx_return_items_return_id ON agent_return_items(return_id);