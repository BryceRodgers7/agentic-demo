"""OpenAI agent for customer support chatbot."""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from tools.schemas import TOOL_SCHEMAS
from tools.implementations import ToolImplementations
from chatbot.prompts import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CustomerSupportAgent:
    """OpenAI-powered customer support agent with function calling."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize the agent.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.tools = ToolImplementations()
        
        # Cache for SOPs to avoid repeated searches
        self.sop_cache = {}
        
        if not self.client:
            print("Warning: OpenAI API key not configured. Agent will not function properly.")
    
    def _detect_likely_tools(self, user_message: str) -> List[str]:
        """Detect which tools are likely needed based on user message.
        
        Args:
            user_message: User's message
            
        Returns:
            List of likely tool names
        """
        message_lower = user_message.lower()
        likely_tools = []
        
        # Order-related keywords
        if any(word in message_lower for word in ['order', 'place order', 'buy', 'purchase', 'want to order']):
            likely_tools.extend(['draft_order', 'create_order'])
        
        # Order status keywords
        if any(word in message_lower for word in ['order status', 'track', 'where is my', 'order #', 'order number']):
            likely_tools.append('order_status')
        
        # Return keywords
        if any(word in message_lower for word in ['return', 'refund', 'send back', 'defective']):
            likely_tools.extend(['order_status', 'initiate_return'])
        
        # Product browsing keywords
        if any(word in message_lower for word in ['browse', 'show me', 'looking for', 'available', 'products', 'catalog']):
            likely_tools.append('product_catalog')
        
        # Shipping keywords
        if any(word in message_lower for word in ['shipping', 'delivery', 'ship to', 'how much to ship']):
            likely_tools.append('estimate_shipping')
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(likely_tools))
    
    def _inject_relevant_sops(self, messages: List[Dict[str, Any]], user_message: str) -> List[Dict[str, Any]]:
        """Inject relevant SOPs from knowledge base based on likely tools needed.
        
        Args:
            messages: Current conversation messages
            user_message: User's latest message
            
        Returns:
            Messages with SOPs injected
        """
        likely_tools = self._detect_likely_tools(user_message)
        
        if not likely_tools:
            return messages
        
        # Search for SOPs for each likely tool
        sop_contents = []
        for tool_name in likely_tools:
            # Check cache first
            if tool_name in self.sop_cache:
                sop_contents.append(self.sop_cache[tool_name])
                logger.info(f"Using cached SOP for {tool_name}")
                continue
            
            # Search knowledge base
            search_query = f"agent-sop-{tool_name}"
            try:
                results = self.tools.vector_store.search_by_text(search_query, limit=1)
                
                if results and len(results) > 0:
                    payload = results[0].get('payload', {})
                    if payload.get('audience') == 'agent' and payload.get('doc_type') == 'sop':
                        sop_content = payload.get('content', '')
                        sop_title = payload.get('title', f'{tool_name} SOP')
                        
                        formatted_sop = f"=== {sop_title} ===\n{sop_content}"
                        sop_contents.append(formatted_sop)
                        
                        # Cache the SOP
                        self.sop_cache[tool_name] = formatted_sop
                        logger.info(f"Found and cached SOP for {tool_name}")
            except Exception as e:
                logger.warning(f"Could not retrieve SOP for {tool_name}: {str(e)}")
        
        # If we found SOPs, inject them as a system message after the main prompt
        if sop_contents:
            sop_message = {
                "role": "system",
                "content": "RELEVANT PROCEDURES:\n\n" + "\n\n".join(sop_contents)
            }
            # Insert after system prompt (position 1)
            messages.insert(1, sop_message)
            logger.info(f"Injected {len(sop_contents)} SOP(s) into conversation")
        
        return messages
    
    def chat(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """Process a user message and return response with tool usage.
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            
        Returns:
            Tuple of (assistant_response, tool_calls_made)
        """
        if not self.client:
            return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.", []
        
        # Initialize conversation history
        if conversation_history is None:
            conversation_history = []
        
        # Build messages for API call
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        # Inject relevant SOPs based on user message
        messages = self._inject_relevant_sops(messages, user_message)
        
        tool_calls_made = []
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                )
                
                assistant_message = response.choices[0].message
                
                # Check if assistant wants to call tools
                if assistant_message.tool_calls:
                    # Add assistant message to history
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # Log tool call initiation
                        logger.info(f"=" * 80)
                        logger.info(f"TOOL CALL: {function_name}")
                        logger.info(f"Parameters: {json.dumps(function_args, indent=2)}")
                        
                        # Execute the tool
                        result = self.tools.execute_tool(function_name, function_args)
                        
                        # Log tool result
                        logger.info(f"Result: {json.dumps(result, indent=2)}")
                        logger.info(f"Success: {result.get('success', False)}")
                        logger.info(f"=" * 80)
                        
                        # Track tool call
                        tool_calls_made.append({
                            "tool": function_name,
                            "arguments": function_args,
                            "result": result
                        })
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(result)
                        })
                    
                    # Continue loop to get final response
                    continue
                else:
                    # No more tool calls, return final response
                    return assistant_message.content or "I apologize, but I'm having trouble generating a response.", tool_calls_made
            
            except Exception as e:
                return f"Error: {str(e)}", tool_calls_made
        
        # Max iterations reached
        return "I apologize, but I'm having trouble completing this request. Let me create a support ticket for you.", tool_calls_made
    
    def get_streaming_response(self, user_message: str, conversation_history: Optional[List[Dict[str, Any]]] = None):
        """Get streaming response (generator).
        
        Note: Streaming with function calling is complex. This is a simplified version
        that returns the full response after tool execution.
        
        Args:
            user_message: User's message
            conversation_history: Previous conversation messages
            
        Yields:
            Response chunks
        """
        # For simplicity, we'll use the non-streaming version and yield the full response
        # In production, you'd implement proper streaming with tool calls
        response, tool_calls = self.chat(user_message, conversation_history)
        
        # Yield in chunks to simulate streaming
        words = response.split()
        for i, word in enumerate(words):
            if i == len(words) - 1:
                yield word
            else:
                yield word + " "
    
    def format_tool_calls_for_display(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Format tool calls for user-friendly display.
        
        Args:
            tool_calls: List of tool call dictionaries
            
        Returns:
            Formatted string
        """
        if not tool_calls:
            return "No tools used"
        
        output = []
        for i, call in enumerate(tool_calls, 1):
            tool_name = call['tool']
            args = call['arguments']
            result = call['result']
            
            output.append(f"**{i}. {tool_name}**")
            output.append(f"   - Arguments: {json.dumps(args, indent=2)}")
            
            if result.get('success'):
                output.append(f"   - ✅ Success: {result.get('message', 'Completed')}")
            else:
                output.append(f"   - ❌ Error: {result.get('error', 'Unknown error')}")
            
            output.append("")
        
        return "\n".join(output)

