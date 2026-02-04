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
        """Test database connectivity."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT 1"
                    self._log_query(query, None)
                    cursor.execute(query)
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _prepare_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert non-JSON-serializable types for JSON serialization.
        
        Converts:
        - Decimal objects to float (for price, total_amount, refund_total_amount, etc.)
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
    
    @staticmethod
    def _log_query(query: str, params: Any = None):
        """Log SQL query with parameters for debugging.
        
        Args:
            query: SQL query string
            params: Query parameters (tuple, list, or dict)
        """
        logger.debug(f"SQL Query: {query}")
        if params:
            logger.debug(f"Parameters: {params}")
        else:
            logger.debug("Parameters: None")
    
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
                    query = "SELECT * FROM agent_products WHERE 1=1"
                    params = []
                    
                    if category:
                        query += " AND LOWER(category) = LOWER(%s)"
                        params.append(category)
                    
                    if search_query:
                        query += " AND (name ILIKE %s OR description ILIKE %s)"
                        params.extend([f"%{search_query}%", f"%{search_query}%"])
                    
                    query += " ORDER BY name"
                    
                    self._log_query(query, params)
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
                    query = "SELECT * FROM agent_products WHERE id = %s"
                    params = (product_id,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
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
                    query = "SELECT stock_quantity FROM agent_products WHERE id = %s"
                    params = (product_id,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
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
                    query = "UPDATE agent_products SET stock_quantity = stock_quantity + %s WHERE id = %s"
                    params = (quantity_change, product_id)
                    self._log_query(query, params)
                    cursor.execute(query, params)
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
                        query = "SELECT price FROM agent_products WHERE id = %s"
                        params = (product_id,)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                        row = cursor.fetchone()
                        if row:
                            price = row['price']
                            total_amount += float(price) * quantity
                            order_items.append((product_id, quantity, price))
                            logger.info(f"create_order: Retrieved price ${price} for product_id={product_id}")
                    
                    # Create order
                    query = """INSERT INTO agent_orders (customer_name, customer_email, customer_phone, 
                           shipping_address, total_amount, status) 
                           VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id"""
                    params = (customer_name, customer_email, customer_phone, shipping_address, total_amount)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    order_id = cursor.fetchone()['id']
                    logger.info(f"create_order: Created order_id={order_id} for customer={customer_name}, total_amount=${total_amount}")
                    
                    # Create order items
                    for product_id, quantity, price in order_items:
                        query = """INSERT INTO agent_order_items (order_id, product_id, quantity, price_at_purchase)
                               VALUES (%s, %s, %s, %s)"""
                        params = (order_id, product_id, quantity, price)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                        logger.info(f"create_order: Created order item for order_id={order_id}, product_id={product_id}, quantity={quantity}")
                        
                        # Update inventory
                        query = "UPDATE agent_products SET stock_quantity = stock_quantity - %s WHERE id = %s"
                        params = (quantity, product_id)
                        self._log_query(query, params)
                        cursor.execute(query, params)
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
                    # Get order with actual columns
                    query = """SELECT id as order_id, customer_name, customer_email, customer_phone,
                                  shipping_address, zip_code, city, state,
                                  status, total_amount, created_at, updated_at 
                           FROM agent_orders WHERE id = %s"""
                    params = (order_id,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    order_row = cursor.fetchone()
                    
                    if not order_row:
                        logger.info(f"get_order: No order found for order_id={order_id}")
                        return None
                    
                    order = dict(order_row)
                    logger.info(f"get_order: Retrieved order_id={order_id}, status={order.get('status')}")
                    
                    # Get order items with aliased columns
                    query = """SELECT oi.id as order_item_id, oi.order_id, oi.product_id, 
                                  oi.quantity, oi.price_at_purchase 
                           FROM agent_order_items oi 
                           WHERE oi.order_id = %s"""
                    params = (order_id,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    order['items'] = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_order: Retrieved {len(order['items'])} order items for order_id={order_id}")
                    
                    return self._prepare_for_json(order)
        except Exception as e:
            logger.error(f"Error in get_order for order_id={order_id}: {str(e)}", exc_info=True)
            raise
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get orders with optional status filter.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            List of order dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT id as order_id, customer_name, customer_email, customer_phone,
                                      shipping_address, zip_code, city, state,
                                      status, total_amount, created_at, updated_at 
                               FROM agent_orders WHERE 1=1"""
                    params = []
                    
                    if status:
                        query += " AND status = %s"
                        params.append(status)
                    
                    query += " ORDER BY created_at DESC"
                    
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_orders query returned {len(results)} orders (status={status})")
                    return results
        except Exception as e:
            logger.error(f"Error in get_orders: {str(e)}", exc_info=True)
            raise
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders.
        
        Returns:
            List of order dictionaries
        """
        return self.get_orders(status=None)
    
    def update_order_status(self, order_id: int, status: str):
        """Update order status.
        
        Args:
            order_id: Order ID
            status: New status
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = "UPDATE agent_orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                    params = (status, order_id)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"update_order_status updated {rows_affected} row(s) for order_id={order_id}, new status={status}")
        except Exception as e:
            logger.error(f"Error in update_order_status for order_id={order_id}, status={status}: {str(e)}", exc_info=True)
            raise
    
    def get_order_items_bulk(self, order_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        """Get order items for multiple orders in a single query.
        
        Args:
            order_ids: List of order IDs
            
        Returns:
            Dictionary mapping order_id to list of item dictionaries with product names
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT oi.order_id, oi.product_id, oi.quantity, oi.price_at_purchase,
                                      p.name as product_name
                               FROM agent_order_items oi
                               LEFT JOIN agent_products p ON oi.product_id = p.id
                               WHERE oi.order_id = ANY(%s)
                               ORDER BY oi.order_id, oi.id"""
                    params = (order_ids,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    
                    # Group items by order_id
                    items_by_order = {}
                    for row in cursor.fetchall():
                        order_id = row['order_id']
                        if order_id not in items_by_order:
                            items_by_order[order_id] = []
                        items_by_order[order_id].append(self._prepare_for_json(dict(row)))
                    
                    logger.info(f"get_order_items_bulk fetched items for {len(items_by_order)} orders")
                    return items_by_order
        except Exception as e:
            logger.error(f"Error in get_order_items_bulk: {str(e)}", exc_info=True)
            raise
    
    # Shipping operations
    def get_shipping_rates(self, carrier: Optional[str] = None, service_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get shipping rates.
        
        Args:
            carrier: Filter by carrier (optional)
            service_type: Filter by service type (optional)
            
        Returns:
            List of shipping rate dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT id, carrier, service_type, 
                                      base_rate as rate, 
                                      estimated_days as delivery_days, 
                                      per_lb_rate, zip_code, created_at 
                               FROM agent_shipping_rates WHERE 1=1"""
                    params = []
                    
                    if carrier:
                        query += " AND carrier = %s"
                        params.append(carrier)
                    
                    if service_type:
                        query += " AND service_type = %s"
                        params.append(service_type)
                    
                    query += " ORDER BY base_rate"
                    
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_shipping_rates query returned {len(results)} rates (carrier={carrier}, service_type={service_type})")
                    return results
        except Exception as e:
            logger.error(f"Error in get_shipping_rates for carrier={carrier}, service_type={service_type}: {str(e)}", exc_info=True)
            raise
    
    def estimate_shipping(self, destination_zip: str, weight_lbs: float) -> Optional[List[Dict[str, Any]]]:
        """Estimate shipping cost for all available service levels.
        
        Args:
            destination_zip: Destination ZIP code
            weight_lbs: Package weight in pounds
            
        Returns:
            List of shipping estimate dictionaries or None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT carrier, service_type, base_rate, per_lb_rate, estimated_days 
                           FROM agent_shipping_rates 
                           WHERE zip_code = %s 
                           ORDER BY estimated_days, base_rate"""
                    params = (destination_zip,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
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
                            'rate': round(total_cost, 2),
                            'delivery_days': rate['estimated_days']
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
                    query = """INSERT INTO agent_support_tickets (customer_name, customer_email, issue_description, priority, status)
                           VALUES (%s, %s, %s, %s, 'open') RETURNING id"""
                    params = (customer_name, customer_email, issue_description, priority)
                    self._log_query(query, params)
                    cursor.execute(query, params)
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
                    query = """SELECT id as ticket_id, customer_name, customer_email, product_id,
                                  issue_description, priority, status, assigned_to,
                                  created_at, updated_at, resolved_at 
                           FROM agent_support_tickets WHERE id = %s"""
                    params = (ticket_id,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    result = self._prepare_for_json(dict(row)) if row else None
                    logger.info(f"get_support_ticket: Query for ticket_id={ticket_id} returned: {'ticket found' if result else 'None'}")
                    return result
        except Exception as e:
            logger.error(f"Error in get_support_ticket for ticket_id={ticket_id}: {str(e)}", exc_info=True)
            raise
    
    def get_support_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get support tickets with optional status filter.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            List of ticket dictionaries
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT id as ticket_id, customer_name, customer_email, product_id,
                                      issue_description, priority, status, assigned_to,
                                      created_at, updated_at, resolved_at 
                               FROM agent_support_tickets WHERE 1=1"""
                    params = []
                    
                    if status:
                        query += " AND status = %s"
                        params.append(status)
                    
                    query += " ORDER BY created_at DESC"
                    
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_support_tickets query returned {len(results)} tickets (status={status})")
                    return results
        except Exception as e:
            logger.error(f"Error in get_support_tickets: {str(e)}", exc_info=True)
            raise
    
    def get_all_support_tickets(self) -> List[Dict[str, Any]]:
        """Get all support tickets.
        
        Returns:
            List of ticket dictionaries
        """
        return self.get_support_tickets(status=None)
    
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
                        query = """UPDATE agent_support_tickets 
                               SET status = %s, updated_at = CURRENT_TIMESTAMP, resolved_at = CURRENT_TIMESTAMP 
                               WHERE id = %s"""
                        params = (status, ticket_id)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                    else:
                        query = "UPDATE agent_support_tickets SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                        params = (status, ticket_id)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"update_ticket_status updated {rows_affected} row(s) for ticket_id={ticket_id}, new status={status}")
        except Exception as e:
            logger.error(f"Error in update_ticket_status for ticket_id={ticket_id}, status={status}: {str(e)}", exc_info=True)
            raise
    
    # Return operations
    def create_return(self, order_id: int, return_reason: str, 
                     product_ids: Optional[List[int]] = None,
                     quantities: Optional[List[int]] = None) -> int:
        """Create a return request.
        
        Args:
            order_id: Order ID
            return_reason: Reason for return
            product_ids: List of product IDs to return (optional - if None, returns entire order)
            quantities: List of quantities to return (optional - must match product_ids length)
            
        Returns:
            New return ID
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    # If no specific products provided, return entire order
                    if not product_ids:
                        # Get all items in the order
                        query = """SELECT oi.product_id, oi.quantity, oi.price_at_purchase
                               FROM agent_order_items oi
                               WHERE oi.order_id = %s"""
                        params = (order_id,)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                        items = cursor.fetchall()
                        
                        if not items:
                            logger.error(f"create_return: No items found for order {order_id}")
                            raise ValueError(f"No items found for order {order_id}")
                        
                        product_ids = [item['product_id'] for item in items]
                        quantities = [item['quantity'] for item in items]
                        logger.info(f"create_return: No specific products provided, returning all {len(items)} items from order {order_id}")
                    
                    # Calculate total refund amount based on specific items
                    refund_total_amount = 0
                    return_items_data = []
                    
                    for product_id, quantity in zip(product_ids, quantities):
                        # Get the price at purchase for this product
                        query = """SELECT oi.price_at_purchase, oi.quantity as ordered_quantity
                               FROM agent_order_items oi
                               WHERE oi.order_id = %s AND oi.product_id = %s"""
                        params = (order_id, product_id)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                        item = cursor.fetchone()
                        
                        if not item:
                            logger.error(f"create_return: Product {product_id} not found in order {order_id}")
                            raise ValueError(f"Product {product_id} not found in order {order_id}")
                        
                        # Calculate refund for this item
                        item_refund = float(item['price_at_purchase']) * quantity
                        refund_total_amount += item_refund
                        
                        # Store data for return items insert
                        return_items_data.append({
                            'product_id': product_id,
                            'quantity': quantity,
                            'price_at_purchase': item['price_at_purchase']
                        })
                        
                        logger.info(f"create_return: Planning return item for product_id={product_id}, quantity={quantity}, refund=${item_refund}")
                    
                    # Create the return order (single record)
                    query = """INSERT INTO agent_return_orders (order_id, return_reason, status, refund_total_amount)
                           VALUES (%s, %s, 'pending', %s) RETURNING id"""
                    params = (order_id, return_reason, refund_total_amount)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    return_id = cursor.fetchone()['id']
                    logger.info(f"create_return: Created return_id={return_id} for order_id={order_id}, total_refund=${refund_total_amount}")
                    
                    # Create return items (one for each product being returned)
                    for item_data in return_items_data:
                        query = """INSERT INTO agent_return_items (return_id, product_id, quantity, price_at_purchase)
                               VALUES (%s, %s, %s, %s)"""
                        params = (return_id, item_data['product_id'], item_data['quantity'], item_data['price_at_purchase'])
                        self._log_query(query, params)
                        cursor.execute(query, params)
                        logger.info(f"create_return: Created return item for return_id={return_id}, product_id={item_data['product_id']}, quantity={item_data['quantity']}")
                    
                    conn.commit()
                    logger.info(f"create_return: Successfully created return_id={return_id} with {len(return_items_data)} item(s), total_refund=${refund_total_amount}")
                    
                    return return_id
        except Exception as e:
            logger.error(f"Error in create_return for order_id={order_id}: {str(e)}", exc_info=True)
            raise
    
    def get_return(self, return_id: int) -> Optional[Dict[str, Any]]:
        """Get return details with items.
        
        Args:
            return_id: Return ID
            
        Returns:
            Return dictionary with items or None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    # Get return order with actual columns
                    query = """SELECT id as return_id, order_id,
                                  return_reason as reason, status, refund_total_amount,
                                  created_at, updated_at, processed_at
                           FROM agent_return_orders WHERE id = %s"""
                    params = (return_id,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    
                    if not row:
                        logger.info(f"get_return: No return found for return_id={return_id}")
                        return None
                    
                    return_order = dict(row)
                    logger.info(f"get_return: Retrieved return_id={return_id}, status={return_order.get('status')}")
                    
                    # Get return items with aliased columns
                    query = """SELECT ri.id as return_item_id, ri.return_id, ri.product_id,
                                  ri.quantity, ri.price_at_purchase as refund_amount,
                                  'Item return' as reason
                           FROM agent_return_items ri
                           WHERE ri.return_id = %s"""
                    params = (return_id,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    return_order['items'] = [self._prepare_for_json(dict(item_row)) for item_row in cursor.fetchall()]
                    logger.info(f"get_return: Retrieved {len(return_order['items'])} return items for return_id={return_id}")
                    
                    return self._prepare_for_json(return_order)
        except Exception as e:
            logger.error(f"Error in get_return for return_id={return_id}: {str(e)}", exc_info=True)
            raise
    
    def get_returns(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get returns with optional status filter.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            List of return dictionaries with items
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT id as return_id, order_id,
                                      return_reason as reason, status, refund_total_amount,
                                      created_at, updated_at, processed_at
                               FROM agent_return_orders WHERE 1=1"""
                    params = []
                    
                    if status:
                        query += " AND status = %s"
                        params.append(status)
                    
                    query += " ORDER BY created_at DESC"
                    
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    returns = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    
                    # Get items for each return
                    for return_order in returns:
                        query = """SELECT ri.id as return_item_id, ri.return_id, ri.product_id,
                                      ri.quantity, ri.price_at_purchase as refund_amount,
                                      'Item return' as reason
                               FROM agent_return_items ri
                               WHERE ri.return_id = %s"""
                        params = (return_order['return_id'],)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                        return_order['items'] = [self._prepare_for_json(dict(item_row)) for item_row in cursor.fetchall()]
                    
                    logger.info(f"get_returns query returned {len(returns)} returns (status={status})")
                    return returns
        except Exception as e:
            logger.error(f"Error in get_returns: {str(e)}", exc_info=True)
            raise
    
    def get_all_returns(self) -> List[Dict[str, Any]]:
        """Get all returns with their items.
        
        Returns:
            List of return dictionaries with items
        """
        return self.get_returns(status=None)
    
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
                        query = """UPDATE agent_return_orders 
                               SET status = %s, updated_at = CURRENT_TIMESTAMP, processed_at = CURRENT_TIMESTAMP 
                               WHERE id = %s"""
                        params = (status, return_id)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                    else:
                        query = "UPDATE agent_return_orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                        params = (status, return_id)
                        self._log_query(query, params)
                        cursor.execute(query, params)
                    rows_affected = cursor.rowcount
                conn.commit()
                logger.info(f"update_return_status updated {rows_affected} row(s) for return_id={return_id}, new status={status}")
        except Exception as e:
            logger.error(f"Error in update_return_status for return_id={return_id}, status={status}: {str(e)}", exc_info=True)
            raise
    
    def get_return_items_bulk(self, return_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        """Get return items for multiple returns in a single query.
        
        Args:
            return_ids: List of return IDs
            
        Returns:
            Dictionary mapping return_id to list of item dictionaries with product names
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT ri.return_id, ri.product_id, ri.quantity, ri.price_at_purchase,
                                      p.name as product_name
                               FROM agent_return_items ri
                               LEFT JOIN agent_products p ON ri.product_id = p.id
                               WHERE ri.return_id = ANY(%s)
                               ORDER BY ri.return_id, ri.id"""
                    params = (return_ids,)
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    
                    # Group items by return_id
                    items_by_return = {}
                    for row in cursor.fetchall():
                        return_id = row['return_id']
                        if return_id not in items_by_return:
                            items_by_return[return_id] = []
                        items_by_return[return_id].append(self._prepare_for_json(dict(row)))
                    
                    logger.info(f"get_return_items_bulk fetched items for {len(items_by_return)} returns")
                    return items_by_return
        except Exception as e:
            logger.error(f"Error in get_return_items_bulk: {str(e)}", exc_info=True)
            raise
    
    def get_returns_with_customer_info(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get returns with customer information from orders.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            List of return dictionaries with customer info
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    query = """SELECT ro.id as return_id, ro.order_id,
                                      ro.return_reason as reason, ro.status, ro.refund_total_amount,
                                      ro.created_at, ro.updated_at, ro.processed_at,
                                      o.customer_name, o.customer_email
                               FROM agent_return_orders ro
                               LEFT JOIN agent_orders o ON ro.order_id = o.id
                               WHERE 1=1"""
                    params = []
                    
                    if status:
                        query += " AND ro.status = %s"
                        params.append(status)
                    
                    query += " ORDER BY ro.created_at DESC"
                    
                    self._log_query(query, params)
                    cursor.execute(query, params)
                    results = [self._prepare_for_json(dict(row)) for row in cursor.fetchall()]
                    logger.info(f"get_returns_with_customer_info query returned {len(results)} returns (status={status})")
                    return results
        except Exception as e:
            logger.error(f"Error in get_returns_with_customer_info: {str(e)}", exc_info=True)
            raise

