"""Streamlit page showing all data views in tabs."""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="All Data Views",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar and page navigation
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 All Data Views")
st.caption("View all database tables in one place")

# Initialize database
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛍️ Products", 
    "📦 Orders", 
    "🚚 Shipping Rates", 
    "🎫 Support Tickets", 
    "↩️ Returns"
])

# Tab 1: Products
with tab1:
    st.subheader("Product List")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All Categories", "electronics", "clothing", "home", "toys", "sports"],
            key="products_category"
        )
    
    with col2:
        search_query = st.text_input("Search Products", "", key="products_search")
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True, key="products_refresh"):
            st.cache_resource.clear()
            st.rerun()
    
    try:
        category = None if category_filter == "All Categories" else category_filter
        search = search_query if search_query else None
        
        products = db.get_products(category=category, search_query=search)
        
        if products:
            st.success(f"Found {len(products)} product(s)")
            
            df = pd.DataFrame(products)
            
            # Ensure id is numeric for proper sorting
            if 'id' in df.columns:
                df['id'] = pd.to_numeric(df['id'], errors='coerce')
            
            # Sort by id ascending by default
            df = df.sort_values('id', ascending=True)
            
            # Display statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Products", len(products))
            with col2:
                avg_price = df['price'].mean() if 'price' in df.columns else 0
                st.metric("Average Price", f"${avg_price:.2f}")
            with col3:
                total_stock = df['stock_quantity'].sum() if 'stock_quantity' in df.columns else 0
                st.metric("Total Stock", int(total_stock))
            with col4:
                categories = df['category'].nunique() if 'category' in df.columns else 0
                st.metric("Categories", categories)
            
            st.divider()
            
            # Display products table
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", format="%d"),
                    "name": st.column_config.TextColumn("Product Name", width="medium"),
                    "description": st.column_config.TextColumn("Description", width="large"),
                    "price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "category": st.column_config.TextColumn("Category", width="small"),
                    "stock_quantity": st.column_config.NumberColumn("Stock", format="%d"),
                    "created_at": st.column_config.DatetimeColumn("Created At", format="YYYY-MM-DD HH:mm")
                }
            )
        else:
            st.info("No products found matching your criteria")
            
    except Exception as e:
        st.error(f"Error loading products: {str(e)}")

# Tab 2: Orders
with tab2:
    st.subheader("Orders")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        order_status_filter = st.selectbox(
            "Filter by Status",
            ["All Statuses", "pending", "confirmed", "shipped", "delivered", "cancelled"],
            key="orders_status"
        )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, key="orders_refresh"):
            st.cache_resource.clear()
            st.rerun()
    
    try:
        status = None if order_status_filter == "All Statuses" else order_status_filter
        orders = db.get_orders(status=status)
        
        if orders:
            st.success(f"Found {len(orders)} order(s)")
            
            # Fetch all order items with product names in a single query
            order_ids = [order['order_id'] for order in orders]
            items_by_order = db.get_order_items_bulk(order_ids)
            
            # Add item count and summary to orders
            for order in orders:
                order_id = order['order_id']
                if order_id in items_by_order:
                    items = items_by_order[order_id]
                    order['item_count'] = f"{len(items)} item(s)"
                else:
                    order['item_count'] = "0 items"
            
            df = pd.DataFrame(orders)
            
            # Ensure order_id is numeric for proper sorting
            if 'order_id' in df.columns:
                df['order_id'] = pd.to_numeric(df['order_id'], errors='coerce')
            
            # Sort by order_id ascending by default
            df = df.sort_values('order_id', ascending=True)
            
            # Display statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Orders", len(orders))
            with col2:
                total_revenue = df['total_amount'].sum() if 'total_amount' in df.columns else 0
                st.metric("Total Revenue", f"${total_revenue:.2f}")
            with col3:
                avg_order = df['total_amount'].mean() if 'total_amount' in df.columns else 0
                st.metric("Average Order", f"${avg_order:.2f}")
            with col4:
                statuses = df['status'].nunique() if 'status' in df.columns else 0
                st.metric("Unique Statuses", statuses)
            
            st.divider()
            
            # Display orders table
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    "order_id": st.column_config.NumberColumn("Order ID", format="%d"),
                    "customer_name": st.column_config.TextColumn("Customer", width="medium"),
                    "total_amount": st.column_config.NumberColumn("Total Amount", format="$%.2f"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "item_count": st.column_config.TextColumn("Items", width="small"),
                    "created_at": st.column_config.DatetimeColumn("Created At", format="YYYY-MM-DD HH:mm"),
                    "updated_at": st.column_config.DatetimeColumn("Updated At", format="YYYY-MM-DD HH:mm")
                }
            )
            
            # Add expandable section to view full item details
            with st.expander("🔍 View Detailed Item Information"):
                st.caption("Expand any order below to see full item details")
                for order in orders:
                    order_id = order['order_id']
                    if order_id in items_by_order:
                        items = items_by_order[order_id]
                        with st.expander(f"Order #{order_id} - {order['customer_name']} ({len(items)} items)"):
                            for item in items:
                                product_name = item.get('product_name', f"Product {item['product_id']}")
                                st.write(f"• **{product_name}** - Quantity: {item['quantity']}, Price: ${item['price_at_purchase']:.2f}")
        else:
            st.info("No orders found")
            
    except Exception as e:
        st.error(f"Error loading orders: {str(e)}")

# Tab 3: Shipping Rates
with tab3:
    st.subheader("Shipping Rates")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        carrier_filter = st.selectbox(
            "Filter by Carrier",
            ["All Carriers", "USPS", "FedEx", "UPS"],
            key="shipping_carrier"
        )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, key="shipping_refresh"):
            st.cache_resource.clear()
            st.rerun()
    
    try:
        carrier = None if carrier_filter == "All Carriers" else carrier_filter
        shipping_rates = db.get_shipping_rates(carrier=carrier)
        
        if shipping_rates:
            st.success(f"Found {len(shipping_rates)} shipping rate(s)")
            
            df = pd.DataFrame(shipping_rates)
            
            # Ensure id is numeric for proper sorting
            if 'id' in df.columns:
                df['id'] = pd.to_numeric(df['id'], errors='coerce')
            
            # Sort by id ascending by default
            df = df.sort_values('id', ascending=True)
            
            # Display statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rates", len(shipping_rates))
            with col2:
                avg_rate = df['rate'].mean() if 'rate' in df.columns else 0
                st.metric("Average Rate", f"${avg_rate:.2f}")
            with col3:
                carriers = df['carrier'].nunique() if 'carrier' in df.columns else 0
                st.metric("Carriers", carriers)
            
            st.divider()
            
            # Display shipping rates table
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", format="%d"),
                    "carrier": st.column_config.TextColumn("Carrier", width="small"),
                    "service_type": st.column_config.TextColumn("Service Type", width="medium"),
                    "rate": st.column_config.NumberColumn("Rate", format="$%.2f"),
                    "delivery_days": st.column_config.NumberColumn("Delivery Days", format="%d"),
                    "created_at": st.column_config.DatetimeColumn("Created At", format="YYYY-MM-DD HH:mm")
                }
            )
        else:
            st.info("No shipping rates found")
            
    except Exception as e:
        st.error(f"Error loading shipping rates: {str(e)}")

# Tab 4: Support Tickets
with tab4:
    st.subheader("Support Tickets")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ticket_status_filter = st.selectbox(
            "Filter by Status",
            ["All Statuses", "open", "in_progress", "resolved", "closed"],
            key="tickets_status"
        )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, key="tickets_refresh"):
            st.cache_resource.clear()
            st.rerun()
    
    try:
        status = None if ticket_status_filter == "All Statuses" else ticket_status_filter
        tickets = db.get_support_tickets(status=status)
        
        if tickets:
            st.success(f"Found {len(tickets)} ticket(s)")
            
            df = pd.DataFrame(tickets)
            
            # Ensure ticket_id is numeric for proper sorting
            if 'ticket_id' in df.columns:
                df['ticket_id'] = pd.to_numeric(df['ticket_id'], errors='coerce')
            
            # Sort by ticket_id ascending by default
            df = df.sort_values('ticket_id', ascending=True)
            
            # Display statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Tickets", len(tickets))
            with col2:
                open_tickets = len(df[df['status'] == 'open']) if 'status' in df.columns else 0
                st.metric("Open Tickets", open_tickets)
            with col3:
                resolved_tickets = len(df[df['status'] == 'resolved']) if 'status' in df.columns else 0
                st.metric("Resolved Tickets", resolved_tickets)
            with col4:
                priorities = df['priority'].nunique() if 'priority' in df.columns else 0
                st.metric("Priority Levels", priorities)
            
            st.divider()
            
            # Display support tickets table
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    "ticket_id": st.column_config.NumberColumn("Ticket ID", format="%d"),
                    "customer_name": st.column_config.TextColumn("Customer", width="medium"),
                    "product_id": st.column_config.NumberColumn("Product ID", format="%d"),
                    "issue_description": st.column_config.TextColumn("Description", width="large"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "priority": st.column_config.TextColumn("Priority", width="small"),
                    "created_at": st.column_config.DatetimeColumn("Created At", format="YYYY-MM-DD HH:mm"),
                    "updated_at": st.column_config.DatetimeColumn("Updated At", format="YYYY-MM-DD HH:mm")
                }
            )
        else:
            st.info("No support tickets found")
            
    except Exception as e:
        st.error(f"Error loading support tickets: {str(e)}")

# Tab 5: Returns
with tab5:
    st.subheader("Returns")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        return_status_filter = st.selectbox(
            "Filter by Status",
            ["All Statuses", "pending", "approved", "rejected", "completed"],
            key="returns_status"
        )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, key="returns_refresh"):
            st.cache_resource.clear()
            st.rerun()
    
    try:
        status = None if return_status_filter == "All Statuses" else return_status_filter
        
        # Get returns with customer info
        returns = db.get_returns_with_customer_info(status=status)
        
        if returns:
            st.success(f"Found {len(returns)} return(s)")
            
            # Fetch all return items with product names in a single query
            return_ids = [r['return_id'] for r in returns]
            items_by_return = db.get_return_items_bulk(return_ids)
            
            # Add item count to returns
            for return_order in returns:
                return_id = return_order['return_id']
                if return_id in items_by_return:
                    items = items_by_return[return_id]
                    return_order['item_count'] = f"{len(items)} item(s)"
                else:
                    return_order['item_count'] = "0 items"
            
            df = pd.DataFrame(returns)
            
            # Ensure return_id is numeric for proper sorting
            if 'return_id' in df.columns:
                df['return_id'] = pd.to_numeric(df['return_id'], errors='coerce')
            
            # Sort by return_id ascending by default
            df = df.sort_values('return_id', ascending=True)
            
            # Display statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Returns", len(returns))
            with col2:
                total_refund = df['refund_total_amount'].sum() if 'refund_total_amount' in df.columns else 0
                st.metric("Total Refunds", f"${total_refund:.2f}")
            with col3:
                pending_returns = len(df[df['status'] == 'pending']) if 'status' in df.columns else 0
                st.metric("Pending Returns", pending_returns)
            with col4:
                approved_returns = len(df[df['status'] == 'approved']) if 'status' in df.columns else 0
                st.metric("Approved Returns", approved_returns)
            
            st.divider()
            
            # Display returns table
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                hide_index=True,
                column_config={
                    "return_id": st.column_config.NumberColumn("Return ID", format="%d"),
                    "order_id": st.column_config.NumberColumn("Order ID", format="%d"),
                    "reason": st.column_config.TextColumn("Reason", width="medium"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "item_count": st.column_config.TextColumn("Items", width="small"),
                    "refund_total_amount": st.column_config.NumberColumn("Refund Amount", format="$%.2f"),
                    "created_at": st.column_config.DatetimeColumn("Created At", format="YYYY-MM-DD HH:mm"),
                    "updated_at": st.column_config.DatetimeColumn("Updated At", format="YYYY-MM-DD HH:mm")
                }
            )
            
            # Add expandable section to view full item details
            with st.expander("🔍 View Detailed Item Information"):
                st.caption("Expand any return below to see full item details")
                for return_order in returns:
                    return_id = return_order['return_id']
                    if return_id in items_by_return:
                        items = items_by_return[return_id]
                        with st.expander(f"Return #{return_id} - Order #{return_order['order_id']} ({len(items)} items)"):
                            for item in items:
                                product_name = item.get('product_name', f"Product {item['product_id']}")
                                refund_amount = item['price_at_purchase'] * item['quantity']
                                st.write(f"• **{product_name}** - Quantity: {item['quantity']}, Refund: ${refund_amount:.2f}")
        else:[[
            st.info("No returns found")]]
            
    except Exception as e:
        st.error(f"Error loading returns: {str(e)}")
