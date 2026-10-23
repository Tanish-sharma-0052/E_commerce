import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Nassau Candy Distributor - Route Efficiency Analysis",
    page_icon="🍬",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv('Nassau Candy Distributor.csv')
    
    # Date cleaning & validation
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y', errors='coerce')
    
    # Calculate Lead Time
    df['Shipping Duration'] = (df['Ship Date'] - df['Order Date']).dt.days
    
    # Remove negative or invalid lead times[cite: 9]
    df = df[df['Shipping Duration'] >= 0].copy()
    
    # Factory Mapping & Coordinates based on project instructions[cite: 7]
    factory_coords = {
        "Lot's O Nuts": {"Lat": 32.881893, "Lon": -111.768036},
        "Wicked Choccy's": {"Lat": 32.076176, "Lon": 81.088371},
        "Sugar Shack": {"Lat": 48.11914, "Lon": -96.18115},
        "Secret Factory": {"Lat": 41.446333, "Lon": -90.565487},
        "The Other Factory": {"Lat": 35.1175, "Lon": 89.971107}
    }
    
    def assign_factory(prod_name):
        prod_lower = str(prod_name).lower()
        if "nutty crunch" in prod_lower or "fudge mallows" in prod_lower or "scrumdiddlyumptious" in prod_lower:
            return "Lot's O Nuts"
        elif "milk chocolate" in prod_lower or "triple dazzle" in prod_lower:
            return "Wicked Choccy's"
        elif "laffy taffy" in prod_lower or "sweetarts" in prod_lower or "nerds" in prod_lower or "fun dip" in prod_lower or "fizzy lifting" in prod_lower:
            return "Sugar Shack"
        elif "gobstopper" in prod_lower or "wallpaper" in prod_lower or "wonka gum" in prod_lower:
            return "Secret Factory"
        elif "hair toffee" in prod_lower or "kazookies" in prod_lower:
            return "The Other Factory"
        else:
            return "Sugar Shack"
            
    df['Factory'] = df['Product Name'].apply(assign_factory)
    df['Factory_Lat'] = df['Factory'].map(lambda x: factory_coords[x]['Lat'])
    df['Factory_Lon'] = df['Factory'].map(lambda x: factory_coords[x]['Lon'])
    
    # Route definition: Factory Location -> Customer State[cite: 9]
    df['Route'] = df['Factory'] + " -> " + df['State/Province']
    
    return df

df = load_data()

st.sidebar.title("🔍 Navigation & Filters")
module = st.sidebar.radio("Select Dashboard Module", [
    "Route Efficiency Overview",
    "Geographic Shipping Map",
    "Ship Mode Comparison",
    "Route Drill-Down & Timelines"
])

st.sidebar.markdown("---")
st.sidebar.subheader("Global Filters")

# Date range filter[cite: 8]
min_date = df['Order Date'].min().date()
max_date = df['Order Date'].max().date()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Region / State selector[cite: 8]
regions = ["All"] + sorted(df['Region'].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Filter by Region", regions)

states = ["All"] + sorted(df['State/Province'].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("Filter by State", states)

# Ship mode filter[cite: 8]
ship_modes = ["All"] + sorted(df['Ship Mode'].dropna().unique().tolist())
selected_ship_mode = st.sidebar.selectbox("Ship Mode Filter", ship_modes)

# Lead-time threshold slider[cite: 8]
default_threshold = int(df['Shipping Duration'].quantile(0.75))
delay_threshold = st.sidebar.slider("Delay Threshold (Days)", min_value=1, max_value=int(df['Shipping Duration'].max()), value=default_threshold)

# Apply filters
filtered_df = df.copy()
if len(date_range) == 2:
    filtered_df = filtered_df[(filtered_df['Order Date'].dt.date >= date_range[0]) & (filtered_df['Order Date'].dt.date <= date_range[1])]

if selected_region != "All":
    filtered_df = filtered_df[filtered_df['Region'] == selected_region]

if selected_state != "All":
    filtered_df = filtered_df[filtered_df['State/Province'] == selected_state]

if selected_ship_mode != "All":
    filtered_df = filtered_df[filtered_df['Ship Mode'] == selected_ship_mode]

filtered_df['Is_Delayed'] = filtered_df['Shipping Duration'] > delay_threshold

# Main title
st.title("🍬 Nassau Candy Distributor - Factory-to-Customer Shipping Route Efficiency Analytics")
st.markdown("Transforming raw order and shipment data into route-level operational intelligence[cite: 7].")

if module == "Route Efficiency Overview":
    st.header("📊 Route Efficiency Overview")
    
    # Aggregate Route KPIs[cite: 8, 9]
    route_kpis = filtered_df.groupby(['Factory', 'State/Province', 'Region']).agg(
        Route_Volume=('Sales', 'count'),
        Total_Sales=('Sales', 'sum'),
        Average_Lead_Time=('Shipping Duration', 'mean'),
        Delay_Frequency=('Is_Delayed', 'mean')
    ).reset_index()
    
    route_kpis['Route_Name'] = route_kpis['Factory'] + " → " + route_kpis['State/Province']
    max_lt = route_kpis['Average_Lead_Time'].max()
    route_kpis['Route_Efficiency_Score'] = 1 - (route_kpis['Average_Lead_Time'] / (max_lt if max_lt > 0 else 1))
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Shipments", f"{len(filtered_df):,}")
    col2.metric("Average Lead Time", f"{filtered_df['Shipping Duration'].mean():.1f} days")
    col3.metric("Delay Frequency", f"{filtered_df['Is_Delayed'].mean()*100:.1f}%")
    col4.metric("Active Routes", f"{len(route_kpis):,}")
    
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Top 10 Most Efficient Routes")
        top_10 = route_kpis.sort_values(by='Route_Efficiency_Score', ascending=False).head(10)
        fig_top = px.bar(top_10, x='Route_Efficiency_Score', y='Route_Name', orientation='h',
                         title="Top 10 Routes by Efficiency Score", labels={'Route_Efficiency_Score': 'Efficiency Score', 'Route_Name': 'Route'})
        st.plotly_chart(fig_top, use_container_width=True)
        
    with col_b:
        st.subheader("Bottom 10 Least Efficient Routes")
        bot_10 = route_kpis.sort_values(by='Route_Efficiency_Score', ascending=True).head(10)
        fig_bot = px.bar(bot_10, x='Route_Efficiency_Score', y='Route_Name', orientation='h',
                         title="Bottom 10 Routes (High Lead Time / Delays)", labels={'Route_Efficiency_Score': 'Efficiency Score', 'Route_Name': 'Route'})
        st.plotly_chart(fig_bot, use_container_width=True)
        
    st.subheader("Route Performance Leaderboard")
    st.dataframe(route_kpis[['Factory', 'State/Province', 'Region', 'Route_Volume', 'Average_Lead_Time', 'Delay_Frequency', 'Route_Efficiency_Score']].sort_values(by='Route_Efficiency_Score', ascending=False), use_container_width=True)

elif module == "Geographic Shipping Map":
    st.header("🗺️ Geographic Shipping Map & Regional Bottlenecks")
    
    reg_summary = filtered_df.groupby('Region').agg(
        Total_Orders=('Sales', 'count'),
        Average_Lead_Time=('Shipping Duration', 'mean'),
        Delay_Frequency=('Is_Delayed', 'mean')
    ).reset_index()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Regional Average Lead Time")
        fig_reg_lt = px.bar(reg_summary, x='Region', y='Average_Lead_Time', color='Average_Lead_Time',
                            color_continuous_scale='Reds', title="Average Lead Time by Region")
        st.plotly_chart(fig_reg_lt, use_container_width=True)
        
    with col2:
        st.subheader("Regional Delay Frequency (%)")
        fig_reg_del = px.bar(reg_summary, x='Region', y='Delay_Frequency', color='Delay_Frequency',
                             color_continuous_scale='Oranges', title="Delay Frequency by Region")
        fig_reg_del.update_yaxes(tickformat='.0%')
        st.plotly_chart(fig_reg_del, use_container_width=True)
        
    st.subheader("US Heatmap of Shipping Efficiency (State-Level)")
    state_summary = filtered_df.groupby('State/Province').agg(
        Average_Lead_Time=('Shipping Duration', 'mean'),
        Delay_Frequency=('Is_Delayed', 'mean'),
        Total_Orders=('Sales', 'count')
    ).reset_index()
    
    fig_map = px.choropleth(state_summary,
                            locations='State/Province',
                            locationmode='USA-states',
                            color='Average_Lead_Time',
                            scope='usa',
                            color_continuous_scale='Viridis',
                            title="US Heatmap: Average Lead Time by State")
    st.plotly_chart(fig_map, use_container_width=True)

elif module == "Ship Mode Comparison":
    st.header("🚢 Ship Mode Performance & Cost-Time Tradeoffs")
    
    ship_summary = filtered_df.groupby('Ship Mode').agg(
        Total_Shipments=('Sales', 'count'),
        Average_Lead_Time=('Shipping Duration', 'mean'),
        Median_Lead_Time=('Shipping Duration', 'median'),
        Delay_Frequency=('Is_Delayed', 'mean'),
        Average_Cost=('Cost', 'mean'),
        Average_Sales=('Sales', 'mean')
    ).reset_index()
    
    col1, col2 = st.columns(2)
    with col1:
        fig_box = px.box(filtered_df, x='Ship Mode', y='Shipping Duration', color='Ship Mode',
                         title="Lead Time Distribution by Ship Mode")
        st.plotly_chart(fig_box, use_container_width=True)
        
    with col2:
        fig_delay = px.bar(ship_summary, x='Ship Mode', y='Delay_Frequency', color='Ship Mode',
                           title="Delay Frequency by Shipping Method")
        fig_delay.update_yaxes(tickformat='.0%')
        st.plotly_chart(fig_delay, use_container_width=True)
        
    st.subheader("Ship Mode Summary Table & Cost-Time Tradeoffs")
    st.dataframe(ship_summary, use_container_width=True)

elif module == "Route Drill-Down & Timelines":
    st.header("🔍 Route Drill-Down & Order-Level Timelines")
    
    selected_factory = st.selectbox("Select Factory", sorted(filtered_df['Factory'].unique()))
    factory_df = filtered_df[filtered_df['Factory'] == selected_factory]
    
    selected_cust_state = st.selectbox("Select Customer State", sorted(factory_df['State/Province'].unique()))
    drill_df = factory_df[factory_df['State/Province'] == selected_cust_state]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Orders on Route", f"{len(drill_df):,}")
    col2.metric("Avg Lead Time", f"{drill_df['Shipping Duration'].mean():.1f} days")
    col3.metric("Delay Rate", f"{drill_df['Is_Delayed'].mean()*100:.1f}%")
    
    st.subheader(f"Order-Level Shipment Timelines for {selected_factory} → {selected_cust_state}")
    st.dataframe(drill_df[['Order ID', 'Order Date', 'Ship Date', 'Ship Mode', 'Product Name', 'Shipping Duration', 'Is_Delayed', 'Sales', 'Gross Profit']].sort_values(by='Order Date', ascending=False), use_container_width=True)
