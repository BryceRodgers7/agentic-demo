"""PostgreSQL database manager for customer support system."""
import psycopg2
import psycopg2.extras
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

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
        
        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                conn.commit()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database schema: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _prepare_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert non-JSON-serializable types for JSON serialization.
        
        Converts:
        - Decimal objects to float (for price, refund_amount, etc.)
        - datetime objects to ISO format strings (for created_at, updated_at, etc.)
        
        Args:
            data: Dictionary potentially containing Decimal or datetime values
            
        Returns:
            Dictionary with all values JSON-serializable
        """
        converted = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                converted[key] = float(value)
            elif isinstance(value, datetime):
                converted[key] = value.isoformat()
            else:
                converted[key] = value
        return converted
    
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
        try:
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
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_products query returned {len(results)} products (category={category}, search_query={search_query})")
                    return results
        except Exception as e:
            logger.error(f"Error in get_products: {str(e)}", exc_info=True)
            raise
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a single product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product dictionary or None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM agent_products WHERE id = %s", (product_id,))
                    row = cursor.fetchone()
                    result = self._prepare_for_json(dict(row)) if row else None
                    logger.info(f"get_product_by_id query for product_id={product_id} returned: {'product found' if result else 'None'}")
                    return result
        except Exception as e:
            logger.error(f"Error in get_product_by_id for product_id={product_id}: {str(e)}", exc_info=True)
            raise
    
    def check_inventory(self, product_id: int) -> Optional[int]:
        """Check inventory for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Stock quantity or None if product not found
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT stock_quantity FROM agent_products WHERE id = %s", (product_id,))
                    row = cursor.fetchone()
                    result = row['stock_quantity'] if row else None
                    logger.info(f"check_inventory query for product_id={product_id} returned stock_quantity: {result}")
                    return result
        except Exception as e:
            logger.error(f"Error in check_inventory for product_id={product_id}: {str(e)}", exc_info=True)
            raise
    
    def update_inventory(self, product_id: int, quantity_change: int):
        """Update product inventory.
        
        Args:
            product_id: Product ID
            quantity_change: Change in quantity (positive or negative)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE agent_products SET stock_quantity = stock_quantity + %s WHERE id = %s",
                        (quantity_change, product_id)
                    )
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"update_inventory updated {rows_affected} row(s) for product_id={product_id}, quantity_change={quantity_change}")
        except Exception as e:
            logger.error(f"Error in update_inventory for product_id={product_id}, quantity_change={quantity_change}: {str(e)}", exc_info=True)
            raise
    
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
        try:
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
                            logger.info(f"create_order: Retrieved price ${price} for product_id={product_id}")
                    
                    # Create order
                    cursor.execute(
                        """INSERT INTO agent_orders (customer_name, customer_email, customer_phone, 
                           shipping_address, total_amount, status) 
                           VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id""",
                        (customer_name, customer_email, customer_phone, shipping_address, total_amount)
                    )
                    order_id = cursor.fetchone()['id']
                    logger.info(f"create_order: Created order_id={order_id} for customer={customer_name}, total_amount=${total_amount}")
                    
                    # Create order items
                    for product_id, quantity, price in order_items:
                        cursor.execute(
                            """INSERT INTO agent_order_items (order_id, product_id, quantity, price_at_purchase)
                               VALUES (%s, %s, %s, %s)""",
                            (order_id, product_id, quantity, price)
                        )
                        logger.info(f"create_order: Created order item for order_id={order_id}, product_id={product_id}, quantity={quantity}")
                        
                        # Update inventory
                        cursor.execute(
                            "UPDATE agent_products SET stock_quantity = stock_quantity - %s WHERE id = %s",
                            (quantity, product_id)
                        )
                        logger.info(f"create_order: Updated inventory for product_id={product_id}, reduced by {quantity}")
                    
                    conn.commit()
                    logger.info(f"create_order: Successfully committed order_id={order_id}")
                    return order_id
        except Exception as e:
            logger.error(f"Error in create_order: {str(e)}", exc_info=True)
            raise
    
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order dictionary with items or None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    # Get order
                    cursor.execute("SELECT * FROM agent_orders WHERE id = %s", (order_id,))
                    order_row = cursor.fetchone()
                    
                    if not order_row:
                        logger.info(f"get_order: No order found for order_id={order_id}")
                        return None
                    
                    order = dict(order_row)
                    logger.info(f"get_order: Retrieved order_id={order_id}, status={order.get('status')}")
                    
                    # Get order items
                    cursor.execute(
                        """SELECT oi.*, p.name as product_name 
                           FROM agent_order_items oi 
                           JOIN agent_products p ON oi.product_id = p.id 
                           WHERE oi.order_id = %s""",
                        (order_id,)
                    )
                    order['items'] = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_order: Retrieved {len(order['items'])} order items for order_id={order_id}")
                    
                    return self._prepare_for_json(order)
        except Exception as e:
            logger.error(f"Error in get_order for order_id={order_id}: {str(e)}", exc_info=True)
            raise
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders.
        
        Returns:
            List of order dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM agent_orders ORDER BY created_at DESC")
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_all_orders query returned {len(results)} orders")
                    return results
        except Exception as e:
            logger.error(f"Error in get_all_orders: {str(e)}", exc_info=True)
            raise
    
    def update_order_status(self, order_id: int, status: str):
        """Update order status.
        
        Args:
            order_id: Order ID
            status: New status
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE agent_orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (status, order_id)
                    )
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"update_order_status updated {rows_affected} row(s) for order_id={order_id}, new status={status}")
        except Exception as e:
            logger.error(f"Error in update_order_status for order_id={order_id}, status={status}: {str(e)}", exc_info=True)
            raise
    
    # Shipping operations
    def get_shipping_rates(self, service_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get shipping rates.
        
        Args:
            service_type: Filter by service type
            
        Returns:
            List of shipping rate dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    if service_type:
                        cursor.execute(
                            "SELECT * FROM agent_shipping_rates WHERE service_type = %s ORDER BY base_rate",
                            (service_type,)
                        )
                    else:
                        cursor.execute("SELECT * FROM agent_shipping_rates ORDER BY base_rate")
                    
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_shipping_rates query returned {len(results)} rates (service_type={service_type})")
                    return results
        except Exception as e:
            logger.error(f"Error in get_shipping_rates for service_type={service_type}: {str(e)}", exc_info=True)
            raise
    
    def estimate_shipping(self, destination_zip: str, weight_lbs: float) -> Optional[List[Dict[str, Any]]]:
        """Estimate shipping cost for all available service levels.
        
        Args:
            destination_zip: Destination ZIP code
            weight_lbs: Package weight in pounds
            service_level: Service level (deprecated - all levels are returned)
            
        Returns:
            List of shipping estimate dictionaries or None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM agent_shipping_rates WHERE zip_code = %s ORDER BY estimated_days, base_rate",
                        (destination_zip,)
                    )
                    rows = cursor.fetchall()
                    
                    if not rows:
                        logger.info(f"estimate_shipping: No shipping rates found for zip_code={destination_zip}")
                        return None
                    
                    estimates = []
                    for row in rows:
                        rate = dict(row)
                        total_cost = float(rate['base_rate']) + (float(rate['per_lb_rate']) * weight_lbs)
                        
                        estimates.append({
                            'carrier': rate['carrier'],
                            'service_type': rate['service_type'],
                            'estimated_cost': round(total_cost, 2),
                            'estimated_days': rate['estimated_days']
                        })
                    
                    logger.info(f"estimate_shipping: Calculated {len(estimates)} estimates for zip_code={destination_zip}, weight_lbs={weight_lbs}")
                    return estimates
        except Exception as e:
            logger.error(f"Error in estimate_shipping for destination_zip={destination_zip}, weight_lbs={weight_lbs}: {str(e)}", exc_info=True)
            raise
    
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
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(
                        """INSERT INTO agent_support_tickets (customer_name, customer_email, issue_description, priority, status)
                           VALUES (%s, %s, %s, %s, 'open') RETURNING id""",
                        (customer_name, customer_email, issue_description, priority)
                    )
                    ticket_id = cursor.fetchone()['id']
                    conn.commit()
                    logger.info(f"create_support_ticket: Created ticket_id={ticket_id} for customer={customer_name}, priority={priority}")
                    return ticket_id
        except Exception as e:
            logger.error(f"Error in create_support_ticket: {str(e)}", exc_info=True)
            raise
    
    def get_support_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get support ticket details.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket dictionary or None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM agent_support_tickets WHERE id = %s", (ticket_id,))
                    row = cursor.fetchone()
                    result = self._prepare_for_json(dict(row)) if row else None
                    logger.info(f"get_support_ticket: Query for ticket_id={ticket_id} returned: {'ticket found' if result else 'None'}")
                    return result
        except Exception as e:
            logger.error(f"Error in get_support_ticket for ticket_id={ticket_id}: {str(e)}", exc_info=True)
            raise
    
    def get_all_support_tickets(self) -> List[Dict[str, Any]]:
        """Get all support tickets.
        
        Returns:
            List of ticket dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM agent_support_tickets ORDER BY created_at DESC")
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_all_support_tickets query returned {len(results)} tickets")
                    return results
        except Exception as e:
            logger.error(f"Error in get_all_support_tickets: {str(e)}", exc_info=True)
            raise
    
    def update_ticket_status(self, ticket_id: int, status: str):
        """Update ticket status.
        
        Args:
            ticket_id: Ticket ID
            status: New status
        """
        try:
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
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"update_ticket_status updated {rows_affected} row(s) for ticket_id={ticket_id}, new status={status}")
        except Exception as e:
            logger.error(f"Error in update_ticket_status for ticket_id={ticket_id}, status={status}: {str(e)}", exc_info=True)
            raise
    
    # Return operations
    def create_return(self, order_id: int, return_reason: str) -> int:
        """Create a return request.
        
        Args:
            order_id: Order ID
            return_reason: Reason for return
            
        Returns:
            New return ID
        """
        try:
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
                        logger.error(f"create_return: Order {order_id} not found")
                        raise ValueError(f"Order {order_id} not found")
                    
                    refund_amount = row['total_amount']
                    product_id = row['product_id'] or 1  # Default to 1 if no items
                    logger.info(f"create_return: Retrieved order_id={order_id}, refund_amount=${refund_amount}")
                    
                    cursor.execute(
                        """INSERT INTO agent_return_orders (order_id, return_reason, status, refund_amount, product_id)
                           VALUES (%s, %s, 'pending', %s, %s) RETURNING id""",
                        (order_id, return_reason, refund_amount, product_id)
                    )
                    return_id = cursor.fetchone()['id']
                    conn.commit()
                    logger.info(f"create_return: Created return_id={return_id} for order_id={order_id}, refund_amount=${refund_amount}")
                    return return_id
        except Exception as e:
            logger.error(f"Error in create_return for order_id={order_id}: {str(e)}", exc_info=True)
            raise
    
    def get_return(self, return_id: int) -> Optional[Dict[str, Any]]:
        """Get return details.
        
        Args:
            return_id: Return ID
            
        Returns:
            Return dictionary or None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM agent_return_orders WHERE id = %s", (return_id,))
                    row = cursor.fetchone()
                    result = self._prepare_for_json(dict(row)) if row else None
                    logger.info(f"get_return: Query for return_id={return_id} returned: {'return found' if result else 'None'}")
                    return result
        except Exception as e:
            logger.error(f"Error in get_return for return_id={return_id}: {str(e)}", exc_info=True)
            raise
    
    def get_all_returns(self) -> List[Dict[str, Any]]:
        """Get all returns.
        
        Returns:
            List of return dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM agent_return_orders ORDER BY created_at DESC")
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_all_returns query returned {len(results)} returns")
                    return results
        except Exception as e:
            logger.error(f"Error in get_all_returns: {str(e)}", exc_info=True)
            raise
    
    def update_return_status(self, return_id: int, status: str):
        """Update return status.
        
        Args:
            return_id: Return ID
            status: New status
        """
        try:
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
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"update_return_status updated {rows_affected} row(s) for return_id={return_id}, new status={status}")
        except Exception as e:
            logger.error(f"Error in update_return_status for return_id={return_id}, status={status}: {str(e)}", exc_info=True)
            raise

