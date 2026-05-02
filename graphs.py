import matplotlib.pyplot as plt

def create_graphs(df):
    graph_paths = []

    # Demand by Hour (Spatio-Temporal Analysis)
    plt.figure(figsize=(6,4))
    df.groupby("Hour")["Demand"].mean().plot(marker='o')
    plt.title("Demand Trends Over Time (Hourly)")
    plt.xlabel("Hour")
    plt.ylabel("Average Demand")
    path1 = "static/graphs/hourly_demand.png"
    plt.savefig(path1)
    plt.close()
    graph_paths.append(path1)

    # Demand by Area (Retail Planning Insight)
    plt.figure(figsize=(6,4))
    df.groupby("Area")["Demand"].sum().plot(kind='bar')
    plt.title("Demand by Area")
    plt.xlabel("Area")
    plt.ylabel("Total Demand")
    path2 = "static/graphs/area_demand.png"
    plt.savefig(path2)
    plt.close()
    graph_paths.append(path2)

    return graph_paths