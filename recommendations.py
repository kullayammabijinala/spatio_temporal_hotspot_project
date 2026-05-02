def generate_recommendations(df):
    recs = []

    high = df[df["Category"] == "High"]["Area"].unique()
    medium = df[df["Category"] == "Medium"]["Area"].unique()
    low = df[df["Category"] == "Low"]["Area"].unique()

    if len(high) > 0:
        recs.append(f"{', '.join(high)} is high-demand: Ideal for supermarkets & fashion stores")

    if len(medium) > 0:
        recs.append(f"{', '.join(medium)} is medium-demand: Suitable for cafes & restaurants")

    if len(low) > 0:
        recs.append(f"{', '.join(low)} is low-demand: Not recommended for new retail stores")

    return recs