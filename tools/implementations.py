"""Tool implementations for customer support chatbot."""
import json
from typing import Dict, Any, List, Optional
from database.db_manager import DatabaseManager
from qdrant.vector_store import VectorStore


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
    
    def estimate_shipping(self, destination_zip: str, weight: float, 
                         service_level: str) -> Dict[str, Any]:
        """Estimate shipping cost.
        
        Args:
            destination_zip: Destination ZIP code
            weight: Package weight in pounds
            service_level: Service level (standard, express, overnight)
            
        Returns:
            Result dictionary with shipping estimate
        """
        try:
            estimate = self.db.estimate_shipping(weight_lbs=weight, service_level=service_level)
            
            if not estimate:
                return {
                    "success": False,
                    "error": f"No shipping rates found for service level: {service_level}"
                }
            
            return {
                "success": True,
                "destination_zip": destination_zip,
                "weight_lbs": weight,
                "service_level": service_level,
                "estimate": estimate,
                "message": f"Shipping to {destination_zip}: ${estimate['estimated_cost']} ({estimate['estimated_days']} days)"
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
    
    def initiate_return(self, order_id: int, return_reason: str) -> Dict[str, Any]:
        """Initiate a return.
        
        Args:
            order_id: Order ID
            return_reason: Reason for return
            
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
            
            # Create return
            return_id = self.db.create_return(
                order_id=order_id,
                return_reason=return_reason
            )
            
            return_info = self.db.get_return(return_id)
            
            return {
                "success": True,
                "return_id": return_id,
                "order_id": order_id,
                "return_info": return_info,
                "message": f"Return request #{return_id} created for order #{order_id}"
            }
        except Exception as e:
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
            results = self.vector_store.search_by_text(query, limit=5)
            
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
            
            return {
                "success": True,
                "query": query,
                "count": len(articles),
                "articles": articles,
                "message": f"Found {len(articles)} relevant article(s)"
            }
        except Exception as e:
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
        # Map tool names to methods
        tool_map = {
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
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            tool_func = tool_map[tool_name]
            result = tool_func(**arguments)
            return result
        except TypeError as e:
            return {
                "success": False,
                "error": f"Invalid arguments for {tool_name}: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing {tool_name}: {str(e)}"
            }

