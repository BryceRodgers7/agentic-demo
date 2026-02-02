"""OpenAI function schemas for customer support tools."""

# Tool schemas for OpenAI function calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "draft_order",
            "description": "Draft an order and validate all required information before creating it. Use this FIRST before create_order to check what information is needed from the customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer (if provided)"
                    },
                    "customer_email": {
                        "type": "string",
                        "description": "Email address of the customer (if provided)"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Phone number of the customer (if provided)"
                    },
                    "shipping_address": {
                        "type": "string",
                        "description": "Complete shipping address including street, city, state, and ZIP (if provided)"
                    },
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of product IDs to order (if provided)"
                    },
                    "quantities": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of quantities for each product (if provided)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "Create a new customer order with products and shipping information. ONLY use this after draft_order confirms all information is complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer"
                    },
                    "customer_email": {
                        "type": "string",
                        "description": "Email address of the customer"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Phone number of the customer"
                    },
                    "shipping_address": {
                        "type": "string",
                        "description": "Complete shipping address including street, city, state, and ZIP"
                    },
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of product IDs to order"
                    },
                    "quantities": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of quantities for each product (must match length of product_ids)"
                    }
                },
                "required": ["customer_name", "customer_email", "customer_phone", "shipping_address", "product_ids", "quantities"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "order_status",
            "description": "Check the status of an existing order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The unique order ID"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "product_catalog",
            "description": "Browse the product catalog with optional filtering by category or search query",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter products by category (e.g., electronics, clothing, home)"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Search products by name or description"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check the current inventory/stock level for a specific product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The unique product ID"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_shipping",
            "description": "Estimate shipping cost and delivery time based on destination and package details",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_zip": {
                        "type": "string",
                        "description": "Destination ZIP/postal code"
                    },
                    "weight": {
                        "type": "number",
                        "description": "Package weight in pounds"
                    }
                },
                "required": ["destination_zip", "weight"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a new customer support ticket for issues or questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Name of the customer"
                    },
                    "customer_email": {
                        "type": "string",
                        "description": "Email address of the customer"
                    },
                    "issue_description": {
                        "type": "string",
                        "description": "Detailed description of the issue or question"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Priority level of the ticket"
                    }
                },
                "required": ["customer_name", "customer_email", "issue_description", "priority"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "initiate_return",
            "description": "Initiate a return request for a completed order. IMPORTANT: Use product_ids and quantities to return SPECIFIC items only. If these are not provided, the ENTIRE order will be returned.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID to return"
                    },
                    "return_reason": {
                        "type": "string",
                        "description": "Reason for the return (e.g., defective, wrong item, changed mind)"
                    },
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "REQUIRED for partial returns: List of specific product IDs to return. MUST be provided when customer wants to return only some items from a multi-item order. Example: [1, 3] to return products 1 and 3."
                    },
                    "quantities": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "REQUIRED for partial returns: Quantities for each product being returned (must match length of product_ids). Example: [2, 1] means return 2 units of the first product and 1 unit of the second."
                    }
                },
                "required": ["order_id", "return_reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the knowledge base for helpful articles and information using semantic similarity",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing what information is needed"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def get_tool_descriptions() -> dict:
    """Get human-readable descriptions of all available tools.
    
    Returns:
        Dictionary mapping tool names to descriptions
    """
    descriptions = {}
    for tool in TOOL_SCHEMAS:
        func = tool["function"]
        descriptions[func["name"]] = func["description"]
    return descriptions


def get_tool_by_name(name: str) -> dict:
    """Get tool schema by name.
    
    Args:
        name: Tool name
        
    Returns:
        Tool schema dictionary or None
    """
    for tool in TOOL_SCHEMAS:
        if tool["function"]["name"] == name:
            return tool
    return None

