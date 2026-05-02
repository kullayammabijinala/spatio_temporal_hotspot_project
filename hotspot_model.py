import pandas as pd
from sklearn.cluster import KMeans

def detect_hotspots(df):
    # Clean column names
    df.columns = df.columns.str.strip()

    # ---------- AUTO DETECT DEMAND COLUMN ----------
    cols_lower = {col.lower(): col for col in df.columns}

    possible_demand_names = [
        "demand",
        "demand_count",
        "demand count",
        "sales_amount",
        "sales",
        "count"
    ]

    demand_column = None
    for name in possible_demand_names:
        if name in cols_lower:
            demand_column = cols_lower[name]
            break

    if demand_column is None:
        raise ValueError(
            f"No demand column found. Available columns: {list(df.columns)}"
        )

    # Rename to standard name
    df.rename(columns={demand_column: "Demand"}, inplace=True)

    # Check required spatial columns
    if "Latitude" not in df.columns or "Longitude" not in df.columns:
        raise ValueError("Dataset must contain Latitude and Longitude columns")

    # ---------- HANDLE SMALL DATASET (VERY IMPORTANT FIX) ----------
    n_samples = len(df)

    if n_samples < 2:
        # If only 1 data point, assign default category
        df["Cluster"] = 0
        df["Hotspot_Level"] = "Low"
        return df

    # Dynamic cluster selection (prevents crash)
    n_clusters = min(3, n_samples)

    # Features for clustering
    X = df[["Latitude", "Longitude", "Demand"]]

    # Apply K-Means safely
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["Cluster"] = kmeans.fit_predict(X)

    # ---------- HOTSPOT LEVEL LOGIC ----------
    demand_mean = df.groupby("Cluster")["Demand"].mean()
    sorted_clusters = demand_mean.sort_values()

    category_labels = ["Low", "Medium", "High"]
    category_map = {}

    for i, cluster_id in enumerate(sorted_clusters.index):
        category_map[cluster_id] = category_labels[i]

    df["Hotspot_Level"] = df["Cluster"].map(category_map)

    return df