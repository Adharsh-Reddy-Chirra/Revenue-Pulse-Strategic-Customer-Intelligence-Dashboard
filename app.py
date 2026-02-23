import pandas as pd
import streamlit as st
import plotly.express as px
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Revenue Intelligence Dashboard", layout="wide")

#  Executive Summary 
st.title("📊 Strategic Revenue & Customer Intelligence")

with st.expander("📄 PROJECT EXECUTIVE SUMMARY (Business Logic & ROI)", expanded=True):
    st.markdown("""
    **Project Objective:** I built this end-to-end pipeline to quantify individual customer contribution and segment the customer base using mathematical tiers.
    
    **Technical Process:**
    * **Data Integrity:** I processed 500k+ records, dropping null IDs and filtering returns ('C' invoices) to ensure 100% financial accuracy.
    * **Statistical Segmentation:** I used **Revenue Quantiles** to create standardized performance tiers (High-Value, Core, At-Risk).
    * **Outcome:** This dashboard identifies high-value individual contributors and visualizes total market share by segment.
    
    **Color-Coded Segment Logic:**
    * 🟢 <span style='color:#00CC96'>**High-Value (VIP)**</span>: Top 10% of spenders. Focus: Retention.
    * 🔵 <span style='color:#636EFA'>**Core-Growth**</span>: 50th to 90th percentile. Focus: Upselling.
    * 🔴 <span style='color:#EF553B'>**At-Risk / Low Value**</span>: Bottom 50% of spenders. Focus: Re-activation.
    """, unsafe_allow_html=True)

# --- DATA INGESTION & CLEANING ---
@st.cache_data
def get_data():
    # Loading my local source file
    path = "Online Retail.xlsx"
    if not os.path.exists(path):
        st.error(f"Missing source file at: {os.getcwd()}")
        st.stop()
    
    # Cleaning: I'm removing null IDs and returns to get 'true' revenue
    df = pd.read_excel(path, engine='openpyxl')
    df = df.dropna(subset=['CustomerID']).copy()
    
    # Filtering out cancellations (Invoice starts with C) and bad price data
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    
    df['CustomerID'] = df['CustomerID'].astype(int)
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    return df

df = get_data()

# --- SEGMENTATION LOGIC ---
# I'm grouping by ID to see exactly what 'n1' brings to the company
customer_rev = df.groupby('CustomerID').agg({
    'Revenue': 'sum',
    'InvoiceNo': 'nunique'
}).reset_index()

customer_rev.columns = ['customer_id', 'total_revenue', 'order_count']

# I'm using Quantiles (90th and 50th) to define my segments mathematically
q90 = customer_rev['total_revenue'].quantile(0.90)
q50 = customer_rev['total_revenue'].quantile(0.50)

def set_segment(rev):
    if rev >= q90: return "High-Value (VIP)"
    if rev >= q50: return "Core-Growth"
    return "At-Risk / Low Value"

customer_rev['segment'] = customer_rev['total_revenue'].apply(set_segment)
customer_rev = customer_rev.sort_values('total_revenue', ascending=False).reset_index(drop=True)

# Professional Color Map for my visuals
segment_colors = {
    "High-Value (VIP)": "#00CC96",      # Green
    "Core-Growth": "#636EFA",           # Blue
    "At-Risk / Low Value": "#EF553B"    # Red
}

# --- EXECUTIVE KPI METRICS ---
c1, c2, c3 = st.columns(3)
c1.metric("Total Platform Revenue", f"${customer_rev['total_revenue'].sum():,.0f}")
c2.metric("Total Active Customers", f"{len(customer_rev):,}")
c3.metric("Avg Spend / Customer", f"${customer_rev['total_revenue'].mean():,.2f}")

st.divider()

# --- HIGH-IMPACT VISUALIZATIONS ---
tab1, tab2 = st.tabs(["Market Share (Donut)", "Individual Contribution (Bar)"])

with tab1:
    st.subheader("Total Revenue Share by Segment")
    # I'm using a Donut Chart to show the 80/20 distribution
    fig_pie = px.pie(
        customer_rev, names='segment', values='total_revenue',
        color='segment', color_discrete_map=segment_colors, hole=0.5,
        title="Revenue Contribution by Customer Tier"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("Top Individual Contributors")
    top_x = st.slider("Select Top N Customers to view:", 5, 50, 15)
    
    # Bar Chart showing individual contribution by Customer ID
    fig_bar = px.bar(
        customer_rev.head(top_x), x='customer_id', y='total_revenue',
        color='segment', color_discrete_map=segment_colors,
        labels={'customer_id': 'Customer ID', 'total_revenue': 'Total Sales ($)'},
        template="plotly_white"
    )
    fig_bar.update_xaxes(type='category') # Ensures IDs don't get treated as numbers
    st.plotly_chart(fig_bar, use_container_width=True)

# --- DETAILED LEDGER & EXPORT ---
st.divider()
st.subheader("Individual Customer Profitability Ledger")

# I'm adding a download button to export results
csv = customer_rev.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Full Revenue Report (CSV)",
    data=csv,
    file_name='final_revenue_segments.csv',
    mime='text/csv',
)

# I'm color-coding the rows so the tier is instantly visible in the table
def apply_colors(row):
    color = segment_colors.get(row.segment)
    return [f'background-color: {color}; color: white' for _ in row]

st.dataframe(
    customer_rev.style.apply(apply_colors, axis=1).format({"total_revenue": "${:,.2f}"})
)

# Saving the file locally automatically every time the app runs
customer_rev.to_csv('final_revenue_segments.csv', index=False)
