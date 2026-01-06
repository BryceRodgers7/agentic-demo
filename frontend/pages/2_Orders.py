"""Streamlit page to view orders table."""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Orders",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Orders")
st.caption("View all customer orders")

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
        ["All Statuses", "pending", "processing", "shipped", "delivered", "cancelled"]
    )

with col2:
    sort_by = st.selectbox(
        "Sort by",
        ["created_at (newest)", "created_at (oldest)", "total_amount (high to low)", "total_amount (low to high)"]
    )

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# Fetch orders
try:
    orders = db.get_all_orders()
    
    if orders:
        # Filter by status
        if status_filter != "All Statuses":
            orders = [o for o in orders if o['status'] == status_filter]
        
        st.success(f"Found {len(orders)} order(s)")
        
        # Convert to DataFrame
        df = pd.DataFrame(orders)
        
        # Sort
        if "created_at (newest)" in sort_by:
            df = df.sort_values('created_at', ascending=False)
        elif "created_at (oldest)" in sort_by:
            df = df.sort_values('created_at', ascending=True)
        elif "total_amount (high to low)" in sort_by:
            df = df.sort_values('total_amount', ascending=False)
        elif "total_amount (low to high)" in sort_by:
            df = df.sort_values('total_amount', ascending=True)
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Orders", len(df))
        with col2:
            total_revenue = df['total_amount'].sum() if 'total_amount' in df.columns else 0
            st.metric("Total Revenue", f"${total_revenue:.2f}")
        with col3:
            avg_order = df['total_amount'].mean() if 'total_amount' in df.columns else 0
            st.metric("Average Order", f"${avg_order:.2f}")
        with col4:
            pending_orders = len(df[df['status'] == 'pending']) if 'status' in df.columns else 0
            st.metric("Pending Orders", pending_orders)
        
        st.divider()
        
        # Display orders table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("Order ID", format="%d"),
                "customer_name": st.column_config.TextColumn("Customer", width="medium"),
                "customer_email": st.column_config.TextColumn("Email", width="medium"),
                "customer_phone": st.column_config.TextColumn("Phone", width="small"),
                "shipping_address": st.column_config.TextColumn("Address", width="large"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "total_amount": st.column_config.NumberColumn("Total", format="$%.2f"),
                "created_at": st.column_config.DatetimeColumn("Created", format="YYYY-MM-DD HH:mm"),
                "updated_at": st.column_config.DatetimeColumn("Updated", format="YYYY-MM-DD HH:mm")
            }
        )
        
        # Show detailed view for selected order
        st.divider()
        st.subheader("Order Details")
        order_ids = df['id'].tolist()
        selected_id = st.selectbox("Select an order to view details", order_ids)
        
        if selected_id:
            order = db.get_order(selected_id)
            if order:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Order ID:**", order['id'])
                    st.write("**Customer:**", order['customer_name'])
                    st.write("**Email:**", order['customer_email'])
                    st.write("**Phone:**", order['customer_phone'])
                with col2:
                    st.write("**Status:**", order['status'])
                    st.write("**Total Amount:**", f"${order['total_amount']:.2f}")
                    st.write("**Created:**", order['created_at'])
                    st.write("**Updated:**", order['updated_at'])
                
                st.write("**Shipping Address:**")
                st.info(order['shipping_address'])
                
                if 'items' in order and order['items']:
                    st.write("**Order Items:**")
                    items_df = pd.DataFrame(order['items'])
                    st.dataframe(
                        items_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "product_name": "Product",
                            "quantity": "Quantity",
                            "price_at_purchase": st.column_config.NumberColumn("Price", format="$%.2f")
                        }
                    )
    else:
        st.info("No orders found")
        
except Exception as e:
    st.error(f"Error loading orders: {str(e)}")
    st.exception(e)

