import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import os

def demand_prediction(df, city=None, area=None):
    try:
        # Filter by city and area
        if city and "City" in df.columns:
            df = df[df["City"] == city]

        if area and "Area" in df.columns:
            df = df[df["Area"] == area]

        # Ensure Date column exists
        if "Date" not in df.columns:
            return None, None

        # Convert Date to datetime
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        # Sort by time
        df = df.sort_values("Date")

        # Use Demand column (auto detect)
        demand_col = None
        for col in ["Demand", "Demand_Count", "Sales", "Orders"]:
            if col in df.columns:
                demand_col = col
                break

        if demand_col is None:
            return None, None

        # Create time index
        df["Time_Index"] = np.arange(len(df))

        if len(df) < 5:
            return None, None

        # Train ML Model
        X = df[["Time_Index"]]
        y = df[demand_col]

        model = LinearRegression()
        model.fit(X, y)

        # Predict next 5 future demands
        future_index = np.arange(len(df), len(df) + 5).reshape(-1, 1)
        predictions = model.predict(future_index)

        # Save prediction graph
        plt.figure(figsize=(8, 4))
        plt.plot(df["Time_Index"], y, label="Actual Demand", marker='o')
        plt.plot(future_index, predictions, label="Predicted Demand", linestyle="--")
        plt.title("Demand Prediction (Future Forecast)")
        plt.xlabel("Time")
        plt.ylabel("Demand")
        plt.legend()

        os.makedirs("static/graphs", exist_ok=True)
        graph_path = "static/graphs/demand_prediction.png"
        plt.savefig(graph_path)
        plt.close()

        predicted_value = round(float(predictions[0]), 2)

        return predicted_value, graph_path

    except Exception as e:
        print("Prediction Error:", e)
        return None, None