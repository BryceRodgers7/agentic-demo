"""PostgreSQL database manager for customer support system."""
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

DB_URL = os.getenv("SUPADATABASE_URL")


class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self, db_url: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            db_url: PostgreSQL connection URL (defaults to SUPADATABASE_URL env var)
        """
        self.db_url = db_url or DB_URL
        if not self.db_url:
            raise ValueError("Database URL not provided. Set SUPADATABASE_URL environment variable.")
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with schema."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections.
        
        Yields:
            psycopg2.Connection: Database connection
        """
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
        finally:
            conn.close()
    
    # Product operations
    def get_products(self, category: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get products from database.
        
        Args:
            category: Filter by category
            search_query: Search in name and description
            
        Returns:
            List of product dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                query = "SELECT * FROM agent_products WHERE 1=1" # what is the point of this??
                params = []
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                if search_query:
                    query += " AND (name ILIKE %s OR description ILIKE %s)"
                    params.extend([f"%{search_query}%", f"%{search_query}%"])
                
                query += " ORDER BY name"
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a single product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product dictionary or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM agent_products WHERE id = %s", (product_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def check_inventory(self, product_id: int) -> Optional[int]:
        """Check inventory for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Stock quantity or None if product not found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT stock_quantity FROM agent_products WHERE id = %s", (product_id,))
                row = cursor.fetchone()
                return row['stock_quantity'] if row else None
    
    def update_inventory(self, product_id: int, quantity_change: int):
        """Update product inventory.
        
        Args:
            product_id: Product ID
            quantity_change: Change in quantity (positive or negative)
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE agent_products SET stock_quantity = stock_quantity + %s WHERE id = %s",
                    (quantity_change, product_id)
                )
            conn.commit()
    
    # Order operations
    def create_order(self, customer_name: str, customer_email: str, customer_phone: str,
                    shipping_address: str, product_ids: List[int], quantities: List[int]) -> int:
        """Create a new order.
        
        Args:
            customer_name: Customer name
            customer_email: Customer email
            customer_phone: Customer phone
            shipping_address: Shipping address
            product_ids: List of product IDs
            quantities: List of quantities for each product
            
        Returns:
            New order ID
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Calculate total
                total_amount = 0
                order_items = []
                
                for product_id, quantity in zip(product_ids, quantities):
                    cursor.execute("SELECT price FROM agent_products WHERE id = %s", (product_id,))
                    row = cursor.fetchone()
                    if row:
                        price = row['price']
                        total_amount += float(price) * quantity
                        order_items.append((product_id, quantity, price))
                
                # Create order
                cursor.execute(
                    """INSERT INTO agent_orders (customer_name, customer_email, customer_phone, 
                       shipping_address, total_amount, status) 
                       VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id""",
                    (customer_name, customer_email, customer_phone, shipping_address, total_amount)
                )
                order_id = cursor.fetchone()['id']
                
                # Create order items
                for product_id, quantity, price in order_items:
                    cursor.execute(
                        """INSERT INTO agent_order_items (order_id, product_id, quantity, price_at_purchase)
                           VALUES (%s, %s, %s, %s)""",
                        (order_id, product_id, quantity, price)
                    )
                    # Update inventory
                    cursor.execute(
                        "UPDATE agent_products SET stock_quantity = stock_quantity - %s WHERE id = %s",
                        (quantity, product_id)
                    )
                
                conn.commit()
                return order_id
    
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order dictionary with items or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Get order
                cursor.execute("SELECT * FROM agent_orders WHERE id = %s", (order_id,))
                order_row = cursor.fetchone()
                
                if not order_row:
                    return None
                
                order = dict(order_row)
                
                # Get order items
                cursor.execute(
                    """SELECT oi.*, p.name as product_name 
                       FROM agent_order_items oi 
                       JOIN agent_products p ON oi.product_id = p.id 
                       WHERE oi.order_id = %s""",
                    (order_id,)
                )
                order['items'] = [dict(row) for row in cursor.fetchall()]
                
                return order
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders.
        
        Returns:
            List of order dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM agent_orders ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
    
    def update_order_status(self, order_id: int, status: str):
        """Update order status.
        
        Args:
            order_id: Order ID
            status: New status
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE agent_orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (status, order_id)
                )
            conn.commit()
    
    # Shipping operations
    def get_shipping_rates(self, service_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get shipping rates.
        
        Args:
            service_type: Filter by service type
            
        Returns:
            List of shipping rate dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                if service_type:
                    cursor.execute(
                        "SELECT * FROM agent_shipping_rates WHERE service_type = %s ORDER BY base_rate",
                        (service_type,)
                    )
                else:
                    cursor.execute("SELECT * FROM agent_shipping_rates ORDER BY base_rate")
                
                return [dict(row) for row in cursor.fetchall()]
    
    def estimate_shipping(self, weight_lbs: float, service_level: str = 'standard') -> Optional[Dict[str, Any]]:
        """Estimate shipping cost.
        
        Args:
            weight_lbs: Package weight in pounds
            service_level: Service level (standard, express, overnight)
            
        Returns:
            Shipping estimate dictionary or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM agent_shipping_rates WHERE service_type = %s ORDER BY base_rate LIMIT 1",
                    (service_level,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                rate = dict(row)
                total_cost = float(rate['base_rate']) + (float(rate['per_lb_rate']) * weight_lbs)
                
                return {
                    'carrier': rate['carrier'],
                    'service_type': rate['service_type'],
                    'estimated_cost': round(total_cost, 2),
                    'estimated_days': rate['estimated_days']
                }
    
    # Support ticket operations
    def create_support_ticket(self, customer_name: str, customer_email: str,
                            issue_description: str, priority: str = 'medium') -> int:
        """Create a support ticket.
        
        Args:
            customer_name: Customer name
            customer_email: Customer email
            issue_description: Description of the issue
            priority: Priority level (low, medium, high, urgent)
            
        Returns:
            New ticket ID
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(
                    """INSERT INTO agent_support_tickets (customer_name, customer_email, issue_description, priority, status)
                       VALUES (%s, %s, %s, %s, 'open') RETURNING id""",
                    (customer_name, customer_email, issue_description, priority)
                )
                ticket_id = cursor.fetchone()['id']
                conn.commit()
                return ticket_id
    
    def get_support_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get support ticket details.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket dictionary or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM agent_support_tickets WHERE id = %s", (ticket_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def get_all_support_tickets(self) -> List[Dict[str, Any]]:
        """Get all support tickets.
        
        Returns:
            List of ticket dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM agent_support_tickets ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
    
    def update_ticket_status(self, ticket_id: int, status: str):
        """Update ticket status.
        
        Args:
            ticket_id: Ticket ID
            status: New status
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                if status == 'resolved':
                    cursor.execute(
                        """UPDATE agent_support_tickets 
                           SET status = %s, updated_at = CURRENT_TIMESTAMP, resolved_at = CURRENT_TIMESTAMP 
                           WHERE id = %s""",
                        (status, ticket_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE agent_support_tickets SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (status, ticket_id)
                    )
            conn.commit()
    
    # Return operations
    def create_return(self, order_id: int, return_reason: str) -> int:
        """Create a return request.
        
        Args:
            order_id: Order ID
            return_reason: Reason for return
            
        Returns:
            New return ID
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Get order total for refund calculation and first product
                cursor.execute(
                    """SELECT o.total_amount, oi.product_id 
                       FROM agent_orders o 
                       LEFT JOIN agent_order_items oi ON o.id = oi.order_id 
                       WHERE o.id = %s 
                       LIMIT 1""",
                    (order_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    raise ValueError(f"Order {order_id} not found")
                
                refund_amount = row['total_amount']
                product_id = row['product_id'] or 1  # Default to 1 if no items
                
                cursor.execute(
                    """INSERT INTO agent_return_orders (order_id, return_reason, status, refund_amount, product_id)
                       VALUES (%s, %s, 'pending', %s, %s) RETURNING id""",
                    (order_id, return_reason, refund_amount, product_id)
                )
                return_id = cursor.fetchone()['id']
                conn.commit()
                return return_id
    
    def get_return(self, return_id: int) -> Optional[Dict[str, Any]]:
        """Get return details.
        
        Args:
            return_id: Return ID
            
        Returns:
            Return dictionary or None
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM agent_return_orders WHERE id = %s", (return_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    def get_all_returns(self) -> List[Dict[str, Any]]:
        """Get all returns.
        
        Returns:
            List of return dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("SELECT * FROM agent_return_orders ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
    
    def update_return_status(self, return_id: int, status: str):
        """Update return status.
        
        Args:
            return_id: Return ID
            status: New status
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                if status == 'processed':
                    cursor.execute(
                        """UPDATE agent_return_orders 
                           SET status = %s, updated_at = CURRENT_TIMESTAMP, processed_at = CURRENT_TIMESTAMP 
                           WHERE id = %s""",
                        (status, return_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE agent_return_orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (status, return_id)
                    )
            conn.commit()

