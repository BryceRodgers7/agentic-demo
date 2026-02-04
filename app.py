"""Streamlit main chat interface for customer support chatbot."""
import streamlit as st
import streamlit.components.v1 as components
import os
import logging
from datetime import datetime
from chatbot.agent import CustomerSupportAgent
from chatbot.prompts import WELCOME_MESSAGE
from tools.schemas import get_tool_descriptions

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enable query logging if DEBUG_QUERIES environment variable is set
# if os.getenv("DEBUG_QUERIES", "").lower() in ("true", "1", "yes"):
logging.getLogger('database.db_manager').setLevel(logging.DEBUG)
logger.info("Query logging enabled (DEBUG level)")


# Page configuration
st.set_page_config(
    page_title="Customer Support Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .tool-call-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .success-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.85em;
    }
    .error-badge {
        background-color: #f8d7da;
        color: #721c24;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.85em;
    }
    /* Hide page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "agent" not in st.session_state:
        st.session_state.agent = CustomerSupportAgent()
    
    if "tool_usage" not in st.session_state:
        st.session_state.tool_usage = []
    
    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = True


def render_sidebar():
    """Render the sidebar with tool information and usage tracking."""
    with st.sidebar:
        st.title("🔧 Available Tools")
        
        # Button to open all data views in a new browser tab
        components.html("""
            <button onclick="window.open('/All_Data_Views', '_blank')" style="
                width: 100%;
                padding: 0.5rem 1rem;
                background-color: #FF4B4B;
                color: white;
                border: none;
                border-radius: 0.5rem;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 500;
            ">
                📊 View All Data Tables (New Tab)
            </button>
        """, height=50)
        
        st.divider()
        
        # Get tool descriptions
        tool_descriptions = get_tool_descriptions()
        
        st.markdown("### Tool Reference")
        for tool_name, description in tool_descriptions.items():
            with st.expander(f"📌 {tool_name}"):
                st.write(description)
        
        st.divider()
        
        # Tool usage statistics
        st.markdown("### 📊 Tool Usage (This Session)")
        if st.session_state.tool_usage:
            tool_counts = {}
            for usage in st.session_state.tool_usage:
                tool_name = usage['tool']
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            
            for tool_name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
                st.metric(tool_name, count)
        else:
            st.info("No tools used yet")
        
        st.divider()
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.session_state.tool_usage = []
            st.session_state.show_welcome = True
            st.rerun()


def render_tool_calls(tool_calls):
    """Render tool calls in an expandable section.
    
    Args:
        tool_calls: List of tool call dictionaries
    """
    if not tool_calls:
        logger.debug("No tool calls to render")
        return
    
    logger.info(f"Rendering tool calls section with {len(tool_calls)} calls")
    
    with st.expander(f"🔧 Tools Used ({len(tool_calls)})", expanded=False):
        for i, call in enumerate(tool_calls, 1):
            tool_name = call['tool']
            arguments = call['arguments']
            result = call['result']
            success = result.get('success', False)
            
            logger.debug(f"Rendering tool call {i}: {tool_name} (success={success})")
            
            st.markdown(f"**{i}. {tool_name}**")
            
            # Arguments
            with st.container():
                st.caption("Arguments:")
                st.json(arguments)
            
            # Result
            if success:
                st.markdown(f'<span class="success-badge">✅ Success</span>', unsafe_allow_html=True)
                if 'message' in result:
                    st.success(result['message'])
            else:
                st.markdown(f'<span class="error-badge">❌ Error</span>', unsafe_allow_html=True)
                if 'error' in result:
                    st.error(result['error'])
            
            if i < len(tool_calls):
                st.divider()


def main():
    """Main application logic."""
    initialize_session_state()
    
    # Header
    st.title("🤖 Customer Support Chatbot")
    st.caption("Powered by OpenAI GPT-4 with function calling")
    
    # Sidebar
    render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Chat")
    
    with col2:
        # API key status
        api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
        if api_key_configured:
            st.success("✅ API Key Configured")
        else:
            st.error("❌ API Key Missing")
    
    # Display welcome message
    if st.session_state.show_welcome:
        with st.chat_message("assistant"):
            st.markdown(WELCOME_MESSAGE)
        st.session_state.show_welcome = False
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show tool calls if present
            if "tool_calls" in message and message["tool_calls"]:
                render_tool_calls(message["tool_calls"])
    
    # Chat input
    if prompt := st.chat_input("How can I help you today?"):
        # Check API key
        if not api_key_configured:
            st.error("⚠️ Please configure OPENAI_API_KEY environment variable to use the chatbot.")
            return
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history.append({"role": "user", "content": prompt})
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, tool_calls = st.session_state.agent.chat(
                    prompt,
                    st.session_state.conversation_history
                )
            
            # Log response summary
            logger.info(f"\n{'='*80}")
            logger.info(f"USER QUERY: {prompt}")
            logger.info(f"TOOLS USED: {len(tool_calls)}")
            if tool_calls:
                for idx, tool_call in enumerate(tool_calls, 1):
                    logger.info(f"  {idx}. {tool_call['tool']}")
            logger.info(f"{'='*80}\n")
            
            # Display response
            st.markdown(response)
            
            # Display tool calls
            if tool_calls:
                logger.info(f"Rendering {len(tool_calls)} tool call(s) in UI")
                render_tool_calls(tool_calls)
                
                # Update tool usage tracking
                st.session_state.tool_usage.extend(tool_calls)
                logger.info(f"Total tools used in session: {len(st.session_state.tool_usage)}")
        
        # Add assistant message to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "tool_calls": tool_calls
        })
        st.session_state.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Rerun to update the UI
        st.rerun()


if __name__ == "__main__":
    main()

