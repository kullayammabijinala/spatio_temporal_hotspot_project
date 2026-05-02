from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import folium
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "hotspot_secret_key"

UPLOAD_FOLDER = "static/uploads"
REPORT_FOLDER = "static/reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

global_df = None


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid Username or Password")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html",
                           cities=[],
                           areas=[],
                           table=None,
                           map_file=None,
                           graph_file=None,
                           best_area=None,
                           message=None)


# ---------------- DEMAND CLASSIFICATION ----------------
def classify_demand_level(demand):
    if demand >= 200:
        return "High"
    elif demand >= 100:
        return "Medium"
    else:
        return "Low"


def suggest_retail_type(demand, peak_hour):
    if demand >= 200 and 17 <= peak_hour <= 22:
        return "Mall"
    elif demand >= 120:
        return "Supermarket"
    else:
        return "Cafe"


# ---------------- UPLOAD DATASET ----------------
@app.route("/upload", methods=["POST"])
def upload_data():
    global global_df

    if "user" not in session:
        return redirect(url_for("login"))

    file = request.files.get("file")

    if not file:
        return render_template("dashboard.html",
                               cities=[],
                               areas=[],
                               message="No file selected!")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    df = pd.read_csv(filepath)

    # Clean column names
    df.columns = df.columns.str.strip()

    required_columns = ["City", "Area", "Latitude", "Longitude", "Demand_Count"]

    for col in required_columns:
        if col not in df.columns:
            return render_template("dashboard.html",
                                   cities=[],
                                   areas=[],
                                   message=f"Missing required column: {col}")

    # Convert numeric columns safely
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df["Demand_Count"] = pd.to_numeric(df["Demand_Count"], errors="coerce")

    # Handle Time column
    if "Time" in df.columns:
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        df["Demand_Hour"] = df["Time"].dt.hour
    else:
        df["Demand_Hour"] = 0

    df = df.dropna()

    global_df = df

    cities = sorted(df["City"].unique())

    return render_template("dashboard.html",
                           cities=cities,
                           areas=[],
                           table=None,
                           map_file=None,
                           graph_file=None,
                           best_area=None,
                           message="Dataset Uploaded Successfully!")


# ---------------- GET AREAS ----------------
@app.route("/get_areas/<city>")
def get_areas(city):
    global global_df

    if global_df is None:
        return {"areas": []}

    areas = sorted(global_df[global_df["City"] == city]["Area"].unique())
    return {"areas": areas}


# ---------------- ANALYZE AREA ----------------
@app.route("/analyze_area", methods=["POST"])
def analyze_area():
    global global_df

    if "user" not in session:
        return redirect(url_for("login"))

    if global_df is None:
        return render_template("dashboard.html",
                               cities=[],
                               areas=[],
                               message="Please upload dataset first!")

    city = request.form.get("city")
    area = request.form.get("area")

    if not city or not area:
        return render_template("dashboard.html",
                               cities=sorted(global_df["City"].unique()),
                               areas=[],
                               message="Please select both City and Area!")

    city_df = global_df[global_df["City"] == city]

    if city_df.empty:
        return render_template("dashboard.html",
                               cities=[],
                               areas=[],
                               message="Selected city not found!")

    df = city_df[city_df["Area"] == area].copy()

    if df.empty:
        return render_template("dashboard.html",
                               cities=sorted(global_df["City"].unique()),
                               areas=sorted(city_df["Area"].unique()),
                               message="Selected area has no data!")

    # ---------------- BEST AREA ----------------
    area_rank = city_df.groupby("Area")["Demand_Count"].sum().reset_index()
    area_rank = area_rank.sort_values(by="Demand_Count", ascending=False)
    best_area = area_rank.iloc[0]["Area"]

    # ---------------- DEMAND LEVEL ----------------
    df["Demand_Level"] = df["Demand_Count"].apply(classify_demand_level)

    peak_hour = df["Demand_Hour"].mode()[0]

    df["Retail_Suggestion"] = df.apply(
        lambda row: suggest_retail_type(row["Demand_Count"], peak_hour),
        axis=1
    )

    # ---------------- MAP ----------------
    center_lat = df["Latitude"].mean()
    center_lon = df["Longitude"].mean()

    hotspot_map = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=7,
            popup=f"Demand: {row['Demand_Count']} | Hour: {row['Demand_Hour']}",
            color="red",
            fill=True
        ).add_to(hotspot_map)

    map_file = "static/area_map.html"
    hotspot_map.save(map_file)

    # ---------------- TIME BASED DEMAND GRAPH ----------------
    hourly_demand = df.groupby("Demand_Hour")["Demand_Count"].sum()

    plt.figure()
    hourly_demand.plot(kind="bar")
    plt.xlabel("Hour of Day")
    plt.ylabel("Total Demand")
    plt.title(f"Time-Based Demand Analysis - {area}")

    graph_file = os.path.join(REPORT_FOLDER, "time_demand.png")
    plt.savefig(graph_file)
    plt.close()

    # ---------------- TABLE ----------------
    display_columns = [
        "City",
        "Area",
        "Latitude",
        "Longitude",
        "Demand_Count",
        "Demand_Level",
        "Demand_Hour",
        "Retail_Suggestion"
    ]

    table_html = df[display_columns].to_html(
        classes="table table-striped table-bordered",
        index=False
    )

    cities = sorted(global_df["City"].unique())
    areas = sorted(city_df["Area"].unique())

    return render_template("dashboard.html",
                           cities=cities,
                           areas=areas,
                           table=table_html,
                           map_file=map_file,
                           graph_file=graph_file,
                           best_area=best_area,
                           message="Analysis Completed Successfully!")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)