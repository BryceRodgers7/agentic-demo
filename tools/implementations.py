"""Tool implementations for customer support chatbot."""
import json
import logging
from typing import Dict, Any, List, Optional
from database.db_manager import DatabaseManager
from qdrant.vector_store import VectorStore

# Configure logging
logger = logging.getLogger(__name__)


class ToolImplementations:
    """Implementations of all customer support tools."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None, 
                 vector_store: Optional[VectorStore] = None):
        """Initialize tool implementations.
        
        Args:
            db_manager: Database manager instance
            vector_store: Vector store instance
        """
        self.db = db_manager or DatabaseManager()
        self.vector_store = vector_store or VectorStore()
    
    def draft_order(self, customer_name: Optional[str] = None, customer_email: Optional[str] = None,
                   customer_phone: Optional[str] = None, shipping_address: Optional[str] = None,
                   product_ids: Optional[List[int]] = None, quantities: Optional[List[int]] = None) -> Dict[str, Any]:
        """Draft an order and validate all required information.
        
        Args:
            customer_name: Customer name (optional)
            customer_email: Customer email (optional)
            customer_phone: Customer phone (optional)
            shipping_address: Shipping address (optional)
            product_ids: List of product IDs (optional)
            quantities: List of quantities (optional)
            
        Returns:
            Result dictionary with validation status and missing fields
        """
        try:
            # Track missing and provided fields
            missing_fields = []
            provided_fields = {}
            
            # Check customer name
            if not customer_name:
                missing_fields.append("customer_name")
            else:
                provided_fields["customer_name"] = customer_name
            
            # Check customer email
            if not customer_email:
                missing_fields.append("customer_email")
            else:
                provided_fields["customer_email"] = customer_email
            
            # Check customer phone
            if not customer_phone:
                missing_fields.append("customer_phone")
            else:
                provided_fields["customer_phone"] = customer_phone
            
            # Check shipping address
            if not shipping_address:
                missing_fields.append("shipping_address")
            else:
                provided_fields["shipping_address"] = shipping_address
            
            # Check product IDs and quantities
            if not product_ids or len(product_ids) == 0:
                missing_fields.append("product_ids")
            elif not quantities or len(quantities) == 0:
                missing_fields.append("quantities")
            elif len(product_ids) != len(quantities):
                return {
                    "success": False,
                    "ready_to_order": False,
                    "error": "Number of products and quantities must match",
                    "missing_fields": missing_fields,
                    "provided_fields": provided_fields
                }
            else:
                # Validate products exist and check inventory
                products_info = []
                total_cost = 0
                total_weight = 0
                
                for product_id, quantity in zip(product_ids, quantities):
                    product = self.db.get_product_by_id(product_id)
                    if not product:
                        return {
                            "success": False,
                            "ready_to_order": False,
                            "error": f"Product ID {product_id} not found",
                            "missing_fields": missing_fields,
                            "provided_fields": provided_fields
                        }
                    
                    # Check inventory
                    if product['stock_quantity'] < quantity:
                        return {
                            "success": False,
                            "ready_to_order": False,
                            "error": f"Insufficient stock for {product['name']}. Requested: {quantity}, Available: {product['stock_quantity']}",
                            "missing_fields": missing_fields,
                            "provided_fields": provided_fields
                        }
                    
                    item_total = product['price'] * quantity
                    item_weight = product.get('weight', 0) * quantity  # Default to 0 if weight not available
                    total_cost += item_total
                    total_weight += item_weight
                    
                    products_info.append({
                        "product_id": product_id,
                        "name": product['name'],
                        "quantity": quantity,
                        "unit_price": product['price'],
                        "item_total": item_total,
                        "stock_available": product['stock_quantity']
                    })
                
                provided_fields["products"] = products_info
                provided_fields["total_cost"] = total_cost
                provided_fields["total_weight"] = total_weight
            
            # Determine if order is ready
            ready_to_order = len(missing_fields) == 0
            
            if ready_to_order:
                return {
                    "success": True,
                    "ready_to_order": True,
                    "message": "All required information collected. Ready to create order.",
                    "order_summary": provided_fields,
                    "next_step": "Call create_order with the complete information to finalize the order."
                }
            else:
                # Build helpful message about what's missing
                field_names = {
                    "customer_name": "customer's full name",
                    "customer_email": "customer's email address",
                    "customer_phone": "customer's phone number",
                    "shipping_address": "shipping address",
                    "product_ids": "products to order",
                    "quantities": "quantities for products"
                }
                
                missing_descriptions = [field_names.get(f, f) for f in missing_fields]
                
                return {
                    "success": True,
                    "ready_to_order": False,
                    "message": f"Missing required information: {', '.join(missing_descriptions)}",
                    "missing_fields": missing_fields,
                    "provided_fields": provided_fields,
                    "next_step": "Ask the customer for the missing information."
                }
                
        except Exception as e:
            return {
                "success": False,
                "ready_to_order": False,
                "error": str(e)
            }
    
    def create_order(self, customer_name: str, customer_email: str, customer_phone: str,
                    shipping_address: str, product_ids: List[int], quantities: List[int]) -> Dict[str, Any]:
        """Create a new order.
        
        Args:
            customer_name: Customer name
            customer_email: Customer email
            customer_phone: Customer phone
            shipping_address: Shipping address
            product_ids: List of product IDs
            quantities: List of quantities
            
        Returns:
            Result dictionary with order details
        """
        try:
            # Validate inputs
            if len(product_ids) != len(quantities):
                return {
                    "success": False,
                    "error": "Product IDs and quantities must have the same length"
                }
            
            # Create order
            order_id = self.db.create_order(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address=shipping_address,
                product_ids=product_ids,
                quantities=quantities
            )
            
            # Get created order details
            order = self.db.get_order(order_id)
            
            return {
                "success": True,
                "order_id": order_id,
                "order": order,
                "message": f"Order #{order_id} created successfully for {customer_name}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def order_status(self, order_id: int) -> Dict[str, Any]:
        """Get order status.
        
        Args:
            order_id: Order ID
            
        Returns:
            Result dictionary with order status
        """
        try:
            order = self.db.get_order(order_id)
            
            if not order:
                return {
                    "success": False,
                    "error": f"Order #{order_id} not found"
                }
            
            return {
                "success": True,
                "order_id": order_id,
                "status": order['status'],
                "order_details": order,
                "message": f"Order #{order_id} status: {order['status']}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def product_catalog(self, category: Optional[str] = None, 
                       search_query: Optional[str] = None) -> Dict[str, Any]:
        """Get product catalog.
        
        Args:
            category: Filter by category
            search_query: Search query
            
        Returns:
            Result dictionary with products
        """
        try:
            # Normalize category to singular lowercase form
            if category:
                category = category.lower().strip()
                # Convert plural to singular
                if category.endswith('s') and category not in ['accessories']:
                    category = category[:-1]  # Remove trailing 's'
            
            products = self.db.get_products(category=category, search_query=search_query)
            
            return {
                "success": True,
                "count": len(products),
                "products": products,
                "message": f"Found {len(products)} product(s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_inventory(self, product_id: int) -> Dict[str, Any]:
        """Check inventory for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Result dictionary with inventory info
        """
        try:
            product = self.db.get_product_by_id(product_id)
            
            if not product:
                return {
                    "success": False,
                    "error": f"Product #{product_id} not found"
                }
            
            stock_quantity = product['stock_quantity']
            in_stock = stock_quantity > 0
            
            return {
                "success": True,
                "product_id": product_id,
                "product_name": product['name'],
                "stock_quantity": stock_quantity,
                "in_stock": in_stock,
                "message": f"{product['name']}: {stock_quantity} units in stock" if in_stock else f"{product['name']}: Out of stock"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def estimate_shipping(self, destination_zip: str, weight: float) -> Dict[str, Any]:
        """Estimate shipping cost for all available service levels.
        
        Args:
            destination_zip: Destination ZIP code
            weight: Package weight in pounds
            service_level: Service level (parameter accepted but all levels returned)
            
        Returns:
            Result dictionary with all shipping estimates
        """
        try:
            estimates = self.db.estimate_shipping(destination_zip=destination_zip, weight_lbs=weight)
            
            if not estimates:
                return {
                    "success": False,
                    "error": f"No shipping rates found for ZIP code: {destination_zip}"
                }
            
            # Format message showing all options
            options_text = "\n".join([
                f"  - {est['carrier']} {est['service_type']}: ${est['estimated_cost']} ({est['estimated_days']} days)"
                for est in estimates
            ])
            
            return {
                "success": True,
                "destination_zip": destination_zip,
                "weight_lbs": weight,
                "estimates": estimates,
                "count": len(estimates),
                "message": f"Shipping options to {destination_zip} for {weight} lbs:\n{options_text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_support_ticket(self, customer_name: str, customer_email: str,
                             issue_description: str, priority: str) -> Dict[str, Any]:
        """Create a support ticket.
        
        Args:
            customer_name: Customer name
            customer_email: Customer email
            issue_description: Issue description
            priority: Priority level
            
        Returns:
            Result dictionary with ticket details
        """
        try:
            ticket_id = self.db.create_support_ticket(
                customer_name=customer_name,
                customer_email=customer_email,
                issue_description=issue_description,
                priority=priority
            )
            
            ticket = self.db.get_support_ticket(ticket_id)
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "ticket": ticket,
                "message": f"Support ticket #{ticket_id} created with {priority} priority"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def initiate_return(self, order_id: int, return_reason: str, 
                       product_ids: Optional[List[int]] = None, 
                       quantities: Optional[List[int]] = None) -> Dict[str, Any]:
        """Initiate a return.
        
        Args:
            order_id: Order ID
            return_reason: Reason for return
            product_ids: List of product IDs to return (optional)
            quantities: List of quantities to return (optional)
            
        Returns:
            Result dictionary with return details
        """
        try:
            # Check if order exists
            order = self.db.get_order(order_id)
            if not order:
                return {
                    "success": False,
                    "error": f"Order #{order_id} not found"
                }
            
            # Validate product_ids and quantities if provided
            if product_ids and quantities:
                if len(product_ids) != len(quantities):
                    return {
                        "success": False,
                        "error": "Number of products and quantities must match"
                    }
                
                # Verify products exist in the order
                order_product_map = {item['product_id']: item for item in order.get('items', [])}
                for product_id, quantity in zip(product_ids, quantities):
                    if product_id not in order_product_map:
                        return {
                            "success": False,
                            "error": f"Product ID {product_id} was not in order #{order_id}"
                        }
                    
                    order_item = order_product_map[product_id]
                    if quantity > order_item['quantity']:
                        return {
                            "success": False,
                            "error": f"Cannot return {quantity} units of {order_item['product_name']}. Order only contained {order_item['quantity']} units."
                        }
            elif product_ids or quantities:
                # One provided but not the other
                return {
                    "success": False,
                    "error": "Both product_ids and quantities must be provided together, or neither"
                }
            
            # Create return
            return_id = self.db.create_return(
                order_id=order_id,
                return_reason=return_reason,
                product_ids=product_ids,
                quantities=quantities
            )
            
            return_info = self.db.get_return(return_id)
            
            # Build a descriptive message
            if product_ids:
                # Get product names for the message
                order_product_map = {item['product_id']: item for item in order.get('items', [])}
                returned_items = []
                for pid, qty in zip(product_ids, quantities):
                    if pid in order_product_map:
                        product_name = order_product_map[pid]['product_name']
                        returned_items.append(f"{qty}x {product_name}")
                items_text = ", ".join(returned_items)
                message = f"Return request #{return_id} created for {items_text} from order #{order_id}. Refund amount: ${return_info['refund_total_amount']}"
            else:
                # For full order return, return all items
                items_text = ", ".join([f"{item['product_name']} x {item['quantity']}" for item in order.get('items', [])])
                message = f"Return request #{return_id} created for entire order #{order_id}. Refund amount: ${return_info['refund_total_amount']}"
            
            logger.info(f"initiate_return: {message}")
            
            return {
                "success": True,
                "return_id": return_id,
                "order_id": order_id,
                "return_info": return_info,
                "returned_items": product_ids if product_ids else "all items",
                "message": message
            }
        except Exception as e:
            logger.error(f"initiate_return error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_knowledge_base(self, query: str) -> Dict[str, Any]:
        """Search the knowledge base.
        
        Args:
            query: Search query
            
        Returns:
            Result dictionary with search results
        """
        try:
            logger.info(f"Searching knowledge base with query: '{query}'")
            results = self.vector_store.search_by_text(query, limit=5)
            logger.info(f"Knowledge base returned {len(results)} results")
            
            # Format results for display
            articles = []
            for result in results:
                payload = result.get('payload', {})
                articles.append({
                    'title': payload.get('title', 'Untitled'),
                    'content': payload.get('content', ''),
                    'category': payload.get('category', ''),
                    'relevance_score': result.get('score', 0),
                    'url': payload.get('url', '')
                })
            
            logger.info(f"Formatted {len(articles)} articles for display")
            
            return {
                "success": True,
                "query": query,
                "count": len(articles),
                "articles": articles,
                "message": f"Found {len(articles)} relevant article(s)"
            }
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        logger.info(f"Executing tool: {tool_name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
        
        # Map tool names to methods
        tool_map = {
            "draft_order": self.draft_order,
            "create_order": self.create_order,
            "order_status": self.order_status,
            "product_catalog": self.product_catalog,
            "check_inventory": self.check_inventory,
            "estimate_shipping": self.estimate_shipping,
            "create_support_ticket": self.create_support_ticket,
            "initiate_return": self.initiate_return,
            "search_knowledge_base": self.search_knowledge_base,
        }
        
        if tool_name not in tool_map:
            logger.error(f"Unknown tool requested: {tool_name}")
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            tool_func = tool_map[tool_name]
            result = tool_func(**arguments)
            logger.info(f"Tool {tool_name} completed with success={result.get('success', False)}")
            return result
        except TypeError as e:
            logger.error(f"Invalid arguments for {tool_name}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Invalid arguments for {tool_name}: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error executing {tool_name}: {str(e)}"
            }

