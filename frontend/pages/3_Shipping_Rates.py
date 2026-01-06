"""Streamlit page to view shipping rates table."""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager

st.set_page_config(
    page_title="Shipping Rates",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Shipping Rates")
st.caption("View all shipping options and rates")

# Initialize database
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Filters
col1, col2 = st.columns([3, 1])

with col1:
    service_filter = st.selectbox(
        "Filter by Service Type",
        ["All Services", "standard", "express", "overnight"]
    )

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# Fetch shipping rates
try:
    service_type = None if service_filter == "All Services" else service_filter
    rates = db.get_shipping_rates(service_type=service_type)
    
    if rates:
        st.success(f"Found {len(rates)} shipping rate(s)")
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rates", len(rates))
        with col2:
            carriers = df['carrier'].nunique() if 'carrier' in df.columns else 0
            st.metric("Carriers", carriers)
        with col3:
            min_rate = df['base_rate'].min() if 'base_rate' in df.columns else 0
            st.metric("Lowest Base Rate", f"${min_rate:.2f}")
        with col4:
            max_days = df['estimated_days'].max() if 'estimated_days' in df.columns else 0
            st.metric("Max Delivery Days", int(max_days))
        
        st.divider()
        
        # Display shipping rates table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", format="%d"),
                "carrier": st.column_config.TextColumn("Carrier", width="medium"),
                "service_type": st.column_config.TextColumn("Service Type", width="medium"),
                "base_rate": st.column_config.NumberColumn("Base Rate", format="$%.2f"),
                "per_lb_rate": st.column_config.NumberColumn("Per Lb Rate", format="$%.2f"),
                "estimated_days": st.column_config.NumberColumn("Est. Days", format="%d"),
                "created_at": st.column_config.DatetimeColumn("Created At", format="YYYY-MM-DD HH:mm")
            }
        )
        
        # Shipping calculator
        st.divider()
        st.subheader("📊 Shipping Cost Calculator")
        
        col1, col2 = st.columns(2)
        with col1:
            calc_weight = st.number_input("Package Weight (lbs)", min_value=0.1, value=5.0, step=0.5)
        with col2:
            calc_service = st.selectbox("Service Level", ["standard", "express", "overnight"])
        
        if st.button("Calculate Shipping Cost"):
            estimate = db.estimate_shipping(weight_lbs=calc_weight, service_level=calc_service)
            if estimate:
                st.success(f"**Carrier:** {estimate['carrier']}")
                st.success(f"**Service:** {estimate['service_type']}")
                st.success(f"**Estimated Cost:** ${estimate['estimated_cost']:.2f}")
                st.success(f"**Estimated Delivery:** {estimate['estimated_days']} days")
            else:
                st.error(f"No rates found for {calc_service} service")
    else:
        st.info("No shipping rates found")
        st.warning("💡 Tip: Add shipping rates to the database to see them here")
        
except Exception as e:
    st.error(f"Error loading shipping rates: {str(e)}")
    st.exception(e)

