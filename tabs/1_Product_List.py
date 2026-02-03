"""Streamlit page to view products table."""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Product List",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Product List")
st.caption("View all products in the database")

# Initialize database
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Filters
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    category_filter = st.selectbox(
        "Filter by Category",
        ["All Categories", "electronics", "clothing", "home", "toys", "sports"]
    )

with col2:
    search_query = st.text_input("Search Products", "")

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# Fetch products
try:
    category = None if category_filter == "All Categories" else category_filter
    search = search_query if search_query else None
    
    products = db.get_products(category=category, search_query=search)
    
    if products:
        st.success(f"Found {len(products)} product(s)")
        
        # Convert to DataFrame
        df = pd.DataFrame(products)
        
        # Sort by ID by default
        if 'id' in df.columns:
            df = df.sort_values('id').reset_index(drop=True)
        
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
            df.sort_values('id', ascending=True),
            use_container_width=True,
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
        
        # Show detailed view for selected product
        st.divider()
        st.subheader("Product Details")
        product_ids = [p['id'] for p in products]
        selected_id = st.selectbox("Select a product to view details", product_ids)
        
        if selected_id:
            selected_product = next((p for p in products if p['id'] == selected_id), None)
            if selected_product:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Name:**", selected_product['name'])
                    st.write("**Category:**", selected_product['category'])
                    st.write("**Price:**", f"${selected_product['price']:.2f}")
                with col2:
                    st.write("**Stock:**", selected_product['stock_quantity'])
                    st.write("**Created:**", selected_product['created_at'])
                    st.write("**ID:**", selected_product['id'])
                
                st.write("**Description:**")
                st.info(selected_product['description'] or "No description available")
    else:
        st.info("No products found matching your criteria")
        
except Exception as e:
    st.error(f"Error loading products: {str(e)}")
    st.exception(e)

