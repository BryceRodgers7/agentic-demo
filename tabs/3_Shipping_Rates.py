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
    carrier_filter = st.selectbox(
        "Filter by Carrier",
        ["All Carriers", "USPS", "FedEx", "UPS"]
    )

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# Fetch shipping rates
try:
    carrier = None if carrier_filter == "All Carriers" else carrier_filter
    rates = db.get_shipping_rates(carrier=carrier)
    
    if rates:
        st.success(f"Found {len(rates)} shipping rate(s)")
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rates", len(rates))
        with col2:
            avg_rate = df['rate'].mean() if 'rate' in df.columns else 0
            st.metric("Average Rate", f"${avg_rate:.2f}")
        with col3:
            carriers = df['carrier'].nunique() if 'carrier' in df.columns else 0
            st.metric("Carriers", carriers)
        
        st.divider()
        
        # Display shipping rates table
        st.dataframe(
            df.sort_values('id', ascending=True),
            use_container_width=True,
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
        
        # Shipping calculator
        st.divider()
        st.subheader("📊 Shipping Cost Estimator")
        
        col1, col2 = st.columns(2)
        with col1:
            calc_zip = st.text_input("Destination ZIP Code", value="90210")
        with col2:
            calc_weight = st.number_input("Package Weight (lbs)", min_value=0.1, value=5.0, step=0.5)
        
        if st.button("Get Shipping Estimates"):
            estimates = db.estimate_shipping(destination_zip=calc_zip, weight_lbs=calc_weight)
            if estimates:
                st.success(f"Found {len(estimates)} shipping options:")
                estimates_df = pd.DataFrame(estimates)
                st.dataframe(
                    estimates_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "carrier": "Carrier",
                        "service_type": "Service Type",
                        "rate": st.column_config.NumberColumn("Rate", format="$%.2f"),
                        "delivery_days": st.column_config.NumberColumn("Delivery Days", format="%d")
                    }
                )
            else:
                st.error(f"No shipping rates found for ZIP code {calc_zip}")
    else:
        st.info("No shipping rates found")
        st.warning("💡 Tip: Add shipping rates to the database to see them here")
        
except Exception as e:
    st.error(f"Error loading shipping rates: {str(e)}")
    st.exception(e)

