"""OpenAI agent for customer support chatbot."""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from tools.schemas import TOOL_SCHEMAS
from tools.implementations import ToolImplementations
from chatbot.prompts import SYSTEM_PROMPT


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
        
        if not self.client:
            print("Warning: OpenAI API key not configured. Agent will not function properly.")
    
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
                        
                        # Execute the tool
                        result = self.tools.execute_tool(function_name, function_args)
                        
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

