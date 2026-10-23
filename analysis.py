import pandas as pd
import numpy as np

def run_analysis():
    print("=== NASSAU CANDY DISTRIBUTOR: SHIPPING ROUTE EFFICIENCY ANALYSIS ===")
    df = pd.read_csv('Nassau Candy Distributor.csv')
    
    # 1. Cleaning & Validation
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y', errors='coerce')
    df['Shipping Duration'] = (df['Ship Date'] - df['Order Date']).dt.days
    df = df[df['Shipping Duration'] >= 0].copy()
    
    # Factory Mapping
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
    df['Route'] = df['Factory'] + " -> " + df['State/Province']
    
    # Delay Threshold (75th percentile)
    threshold = df['Shipping Duration'].quantile(0.75)
    df['Is_Delayed'] = df['Shipping Duration'] > threshold
    print(f"Delay Threshold: {threshold:.1f} days")
    
    # Route KPIs
    route_kpis = df.groupby(['Factory', 'State/Province', 'Region']).agg(
        Route_Volume=('Sales', 'count'),
        Total_Sales=('Sales', 'sum'),
        Average_Lead_Time=('Shipping Duration', 'mean'),
        Delay_Frequency=('Is_Delayed', 'mean')
    ).reset_index()
    
    max_lt = route_kpis['Average_Lead_Time'].max()
    route_kpis['Route_Efficiency_Score'] = 1 - (route_kpis['Average_Lead_Time'] / max_lt)
    route_kpis['Route_Name'] = route_kpis['Factory'] + " → " + route_kpis['State/Province']
    
    print("\n--- TOP 5 MOST EFFICIENT ROUTES ---")
    print(route_kpis.sort_values(by='Route_Efficiency_Score', ascending=False)[['Route_Name', 'Route_Volume', 'Average_Lead_Time', 'Delay_Frequency', 'Route_Efficiency_Score']].head(5).to_string(index=False))
    
    print("\n--- TOP 5 LEAST EFFICIENT ROUTES ---")
    print(route_kpis.sort_values(by='Route_Efficiency_Score', ascending=True)[['Route_Name', 'Route_Volume', 'Average_Lead_Time', 'Delay_Frequency', 'Route_Efficiency_Score']].head(5).to_string(index=False))
    
    print("\n--- REGIONAL BOTTLENECK ANALYSIS ---")
    reg_summary = df.groupby('Region').agg(
        Total_Orders=('Sales', 'count'),
        Average_Lead_Time=('Shipping Duration', 'mean'),
        Delay_Frequency=('Is_Delayed', 'mean')
    ).reset_index()
    print(reg_summary.to_string(index=False))

if __name__ == '__main__':
    run_analysis()