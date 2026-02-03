"""Streamlit page to view support tickets table."""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Support Tickets",
    page_icon="🎫",
    layout="wide"
)

st.title("🎫 Support Tickets")
st.caption("View all customer support tickets")

# Initialize database
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Filters
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All Statuses", "open", "in_progress", "resolved", "closed"]
    )

with col2:
    priority_filter = st.selectbox(
        "Filter by Priority",
        ["All Priorities", "low", "medium", "high", "urgent"]
    )

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# Fetch tickets
try:
    tickets = db.get_all_support_tickets()
    
    if tickets:
        # Apply filters
        if status_filter != "All Statuses":
            tickets = [t for t in tickets if t['status'] == status_filter]
        
        if priority_filter != "All Priorities":
            tickets = [t for t in tickets if t['priority'] == priority_filter]
        
        st.success(f"Found {len(tickets)} ticket(s)")
        
        # Convert to DataFrame
        df = pd.DataFrame(tickets)
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tickets", len(df))
        with col2:
            open_tickets = len(df[df['status'] == 'open']) if 'status' in df.columns else 0
            st.metric("Open Tickets", open_tickets)
        with col3:
            resolved_tickets = len(df[df['status'] == 'resolved']) if 'status' in df.columns else 0
            st.metric("Resolved Tickets", resolved_tickets)
        with col4:
            urgent_tickets = len(df[df['priority'] == 'urgent']) if 'priority' in df.columns else 0
            st.metric("Urgent Tickets", urgent_tickets)
        
        st.divider()
        
        # Display tickets table
        st.dataframe(
            df.sort_values('ticket_id', ascending=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ticket_id": st.column_config.NumberColumn("Ticket ID", format="%d"),
                "customer_name": st.column_config.TextColumn("Customer", width="medium"),
                "customer_email": st.column_config.TextColumn("Email", width="medium"),
                "product_id": st.column_config.NumberColumn("Product ID", format="%d"),
                "issue_description": st.column_config.TextColumn("Issue", width="large"),
                "priority": st.column_config.TextColumn("Priority", width="small"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "assigned_to": st.column_config.TextColumn("Assigned To", width="small"),
                "created_at": st.column_config.DatetimeColumn("Created", format="YYYY-MM-DD HH:mm"),
                "updated_at": st.column_config.DatetimeColumn("Updated", format="YYYY-MM-DD HH:mm"),
                "resolved_at": st.column_config.DatetimeColumn("Resolved", format="YYYY-MM-DD HH:mm")
            }
        )
        
        # Show detailed view for selected ticket
        st.divider()
        st.subheader("Ticket Details")
        ticket_ids = df['ticket_id'].tolist() if 'ticket_id' in df.columns else []
        if ticket_ids:
            selected_id = st.selectbox("Select a ticket to view details", ticket_ids)
            
            if selected_id:
                ticket = next((t for t in tickets if t['ticket_id'] == selected_id), None)
                if ticket:
                    # Priority badge color
                    priority_colors = {
                        'low': '🟢',
                        'medium': '🟡',
                        'high': '🟠',
                        'urgent': '🔴'
                    }
                    priority_icon = priority_colors.get(ticket.get('priority', 'medium'), '⚪')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Ticket ID:**", ticket['ticket_id'])
                        st.write("**Customer:**", ticket['customer_name'])
                        st.write("**Email:**", ticket['customer_email'])
                        st.write(f"**Priority:** {priority_icon} {ticket.get('priority', 'medium').upper()}")
                    with col2:
                        st.write("**Status:**", ticket['status'].upper())
                        st.write("**Product ID:**", ticket.get('product_id', 'N/A'))
                        st.write("**Assigned To:**", ticket.get('assigned_to') or 'Unassigned')
                        st.write("**Created:**", ticket['created_at'])
                    
                    st.write("**Issue Description:**")
                    st.info(ticket.get('issue_description', 'N/A'))
                    
                    if ticket.get('resolved_at'):
                        st.success(f"✅ Resolved on {ticket['resolved_at']}")
    else:
        st.info("No support tickets found")
        
except Exception as e:
    st.error(f"Error loading support tickets: {str(e)}")
    st.exception(e)

