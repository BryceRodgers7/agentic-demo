"""Streamlit page to view returns table."""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Returns",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Returns")
st.caption("View all return requests")

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
        ["All Statuses", "pending", "approved", "rejected", "processed", "refunded"]
    )

with col2:
    date_filter = st.selectbox(
        "Date Range",
        ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
    )

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# Fetch returns
try:
    returns = db.get_all_returns()
    
    if returns:
        # Apply filters
        if status_filter != "All Statuses":
            returns = [r for r in returns if r['status'] == status_filter]
        
        # Date filtering would require datetime parsing - simplified here
        # In production, you'd parse created_at and filter by date range
        
        st.success(f"Found {len(returns)} return(s)")
        
        # Convert to DataFrame
        df = pd.DataFrame(returns)
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Returns", len(df))
        with col2:
            pending_returns = len(df[df['status'] == 'pending']) if 'status' in df.columns else 0
            st.metric("Pending Returns", pending_returns)
        with col3:
            total_refunds = df['refund_total_amount'].sum() if 'refund_total_amount' in df.columns else 0
            st.metric("Total Refunds", f"${total_refunds:.2f}")
        with col4:
            processed_returns = len(df[df['status'] == 'processed']) if 'status' in df.columns else 0
            st.metric("Processed Returns", processed_returns)
        
        st.divider()
        
        # Display returns table (exclude items column from main view)
        display_df = df.drop(columns=['items']) if 'items' in df.columns else df
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("Return ID", format="%d"),
                "order_id": st.column_config.NumberColumn("Order ID", format="%d"),
                "return_reason": st.column_config.TextColumn("Reason", width="large"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "refund_total_amount": st.column_config.NumberColumn("Refund Amount", format="$%.2f"),
                "created_at": st.column_config.DatetimeColumn("Created", format="YYYY-MM-DD HH:mm"),
                "updated_at": st.column_config.DatetimeColumn("Updated", format="YYYY-MM-DD HH:mm"),
                "processed_at": st.column_config.DatetimeColumn("Processed", format="YYYY-MM-DD HH:mm")
            }
        )
        
        # Show detailed view for selected return
        st.divider()
        st.subheader("Return Details")
        return_ids = df['id'].tolist()
        selected_id = st.selectbox("Select a return to view details", return_ids)
        
        if selected_id:
            return_data = next((r for r in returns if r['id'] == selected_id), None)
            if return_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Return ID:**", return_data['id'])
                    st.write("**Order ID:**", return_data['order_id'])
                    st.write("**Status:**", return_data['status'].upper())
                    st.write("**Refund Amount:**", f"${return_data['refund_total_amount']:.2f}" if return_data['refund_total_amount'] else "N/A")
                with col2:
                    st.write("**Created:**", return_data['created_at'])
                    st.write("**Updated:**", return_data['updated_at'])
                    st.write("**Processed:**", return_data['processed_at'] or "Not yet processed")
                
                st.write("**Return Reason:**")
                st.info(return_data['return_reason'])
                
                # Display return items
                if 'items' in return_data and return_data['items']:
                    st.write("**Items Being Returned:**")
                    items_df = pd.DataFrame(return_data['items'])
                    st.dataframe(
                        items_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "product_id": st.column_config.NumberColumn("Product ID", format="%d"),
                            "product_name": st.column_config.TextColumn("Product Name"),
                            "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                            "price_at_purchase": st.column_config.NumberColumn("Price at Purchase", format="$%.2f")
                        }
                    )
                
                # Try to get order details
                try:
                    order = db.get_order(return_data['order_id'])
                    if order:
                        st.write("**Original Order Details:**")
                        st.write(f"- Customer: {order['customer_name']}")
                        st.write(f"- Order Total: ${order['total_amount']:.2f}")
                        st.write(f"- Order Status: {order['status']}")
                except Exception:
                    pass
    else:
        st.info("No returns found")
        
except Exception as e:
    st.error(f"Error loading returns: {str(e)}")
    st.exception(e)

