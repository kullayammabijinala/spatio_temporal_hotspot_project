import folium
from folium.plugins import HeatMap

def create_heatmap(df):
    center_lat = df["Latitude"].mean()
    center_lon = df["Longitude"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    for _, row in df.iterrows():
        color = "green"

        if row["Hotspot_Level"] == "High":
            color = "red"
        elif row["Hotspot_Level"] == "Medium":
            color = "orange"

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            popup=f"Demand: {row['Demand']} | Level: {row['Hotspot_Level']}"
        ).add_to(m)

    path = "static/maps/heatmap.html"
    m.save(path)
    return path