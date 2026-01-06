"""SQLite database manager for customer support system."""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: str = "customer_support.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with schema."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if search_query:
                query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{search_query}%", f"%{search_query}%"])
            
            query += " ORDER BY name"
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a single product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
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
            cursor = conn.execute("SELECT stock_quantity FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return row['stock_quantity'] if row else None
    
    def update_inventory(self, product_id: int, quantity_change: int):
        """Update product inventory.
        
        Args:
            product_id: Product ID
            quantity_change: Change in quantity (positive or negative)
        """
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
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
            # Calculate total
            total_amount = 0
            order_items = []
            
            for product_id, quantity in zip(product_ids, quantities):
                cursor = conn.execute("SELECT price FROM products WHERE id = ?", (product_id,))
                row = cursor.fetchone()
                if row:
                    price = row['price']
                    total_amount += price * quantity
                    order_items.append((product_id, quantity, price))
            
            # Create order
            cursor = conn.execute(
                """INSERT INTO orders (customer_name, customer_email, customer_phone, 
                   shipping_address, total_amount, status) 
                   VALUES (?, ?, ?, ?, ?, 'pending')""",
                (customer_name, customer_email, customer_phone, shipping_address, total_amount)
            )
            order_id = cursor.lastrowid
            
            # Create order items
            for product_id, quantity, price in order_items:
                conn.execute(
                    """INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
                       VALUES (?, ?, ?, ?)""",
                    (order_id, product_id, quantity, price)
                )
                # Update inventory
                conn.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
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
            # Get order
            cursor = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order_row = cursor.fetchone()
            
            if not order_row:
                return None
            
            order = dict(order_row)
            
            # Get order items
            cursor = conn.execute(
                """SELECT oi.*, p.name as product_name 
                   FROM order_items oi 
                   JOIN products p ON oi.product_id = p.id 
                   WHERE oi.order_id = ?""",
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
            cursor = conn.execute("SELECT * FROM orders ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_order_status(self, order_id: int, status: str):
        """Update order status.
        
        Args:
            order_id: Order ID
            status: New status
        """
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
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
            if service_type:
                cursor = conn.execute(
                    "SELECT * FROM shipping_rates WHERE service_type = ? ORDER BY base_rate",
                    (service_type,)
                )
            else:
                cursor = conn.execute("SELECT * FROM shipping_rates ORDER BY base_rate")
            
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
            cursor = conn.execute(
                "SELECT * FROM shipping_rates WHERE service_type = ? ORDER BY base_rate LIMIT 1",
                (service_level,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            rate = dict(row)
            total_cost = rate['base_rate'] + (rate['per_lb_rate'] * weight_lbs)
            
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
            cursor = conn.execute(
                """INSERT INTO support_tickets (customer_name, customer_email, issue_description, priority, status)
                   VALUES (?, ?, ?, ?, 'open')""",
                (customer_name, customer_email, issue_description, priority)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_support_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get support ticket details.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_support_tickets(self) -> List[Dict[str, Any]]:
        """Get all support tickets.
        
        Returns:
            List of ticket dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM support_tickets ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_ticket_status(self, ticket_id: int, status: str):
        """Update ticket status.
        
        Args:
            ticket_id: Ticket ID
            status: New status
        """
        with self.get_connection() as conn:
            if status == 'resolved':
                conn.execute(
                    """UPDATE support_tickets 
                       SET status = ?, updated_at = CURRENT_TIMESTAMP, resolved_at = CURRENT_TIMESTAMP 
                       WHERE id = ?""",
                    (status, ticket_id)
                )
            else:
                conn.execute(
                    "UPDATE support_tickets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
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
            # Get order total for refund calculation
            cursor = conn.execute("SELECT total_amount FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Order {order_id} not found")
            
            refund_amount = row['total_amount']
            
            cursor = conn.execute(
                """INSERT INTO returns (order_id, return_reason, status, refund_amount)
                   VALUES (?, ?, 'pending', ?)""",
                (order_id, return_reason, refund_amount)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_return(self, return_id: int) -> Optional[Dict[str, Any]]:
        """Get return details.
        
        Args:
            return_id: Return ID
            
        Returns:
            Return dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM returns WHERE id = ?", (return_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_returns(self) -> List[Dict[str, Any]]:
        """Get all returns.
        
        Returns:
            List of return dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM returns ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_return_status(self, return_id: int, status: str):
        """Update return status.
        
        Args:
            return_id: Return ID
            status: New status
        """
        with self.get_connection() as conn:
            if status == 'processed':
                conn.execute(
                    """UPDATE returns 
                       SET status = ?, updated_at = CURRENT_TIMESTAMP, processed_at = CURRENT_TIMESTAMP 
                       WHERE id = ?""",
                    (status, return_id)
                )
            else:
                conn.execute(
                    "UPDATE returns SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, return_id)
                )
            conn.commit()

