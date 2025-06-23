import pandas as pd
import matplotlib.pyplot as plt

# Load your dataset
df = pd.read_csv("/mnt/data/dailysummary.csv")

# Define Recommended Daily Allowances (RDAs)
rda_values = {
    "Vitamin A (IU)": 3000,
    "Vitamin C (mg)": 90,
    "Vitamin D (IU)": 600,
    "Vitamin E (mg)": 15,
    "Vitamin K (mcg)": 120,
    "Calcium (mg)": 1000,
    "Iron (mg)": 8,
    "Magnesium (mg)": 420,
    "Phosphorus (mg)": 700,
    "Potassium (mg)": 3400,
    "Sodium (mg)": 2300,
    "Zinc (mg)": 11,
    "Copper (mg)": 0.9,
    "Manganese (mg)": 2.3,
    "Selenium (mcg)": 55,
    "B1 (Thiamine) (mg)": 1.2,
    "B2 (Riboflavin) (mg)": 1.3,
    "B3 (Niacin) (mg)": 16,
    "B5 (Pantothenic Acid) (mg)": 5,
    "B6 (Pyridoxine) (mg)": 1.3,
    "B12 (Cobalamin) (mcg)": 2.4,
    "Folate (DFE) (mcg)": 400,
    "Choline (mg)": 550
}

# Filter nutrients that are present in your dataset
available_micros = {k: v for k, v in rda_values.items() if k in df.columns}
avg_intake = df[list(available_micros.keys())].mean()

# Create a DataFrame comparing intake to RDA
comparison_df = pd.DataFrame({
    "Average Intake": avg_intake,
    "Recommended Daily Value": pd.Series(available_micros)
})
comparison_df["Percent of RDA"] = (comparison_df["Average Intake"] /
                                   comparison_df["Recommended Daily Value"]) * 100
comparison_df_sorted = comparison_df.sort_values("Percent of RDA")

# Split the nutrients into ≤200% and >200%
below_or_equal_200 = comparison_df_sorted[comparison_df_sorted["Percent of RDA"] <= 200]
above_200 = comparison_df_sorted[comparison_df_sorted["Percent of RDA"] > 200]

# Clean labels
labels_cleaned = [label.split(" (")[0] for label in below_or_equal_200.index]
intake_filtered = below_or_equal_200["Percent of RDA"]
colors_filtered = ["red" if val < 100 else "green" for val in intake_filtered]

# Plot
plt.figure(figsize=(14, 7))
bars = plt.bar(labels_cleaned, intake_filtered, color=colors_filtered)
plt.axhline(100, color='black', linestyle='--', linewidth=1.5)

# Annotate bars
for bar, val in zip(bars, intake_filtered):
    label = f"{int(val)}%"
    y_offset = 5
    plt.text(bar.get_x() + bar.get_width() / 2, val + y_offset,
             label, ha='center', va='bottom', fontsize=9)

# Add high-RDA nutrients on the right
x_offset = len(labels_cleaned) + 0.1
y_start = max(intake_filtered) + 10
line_spacing = 14
for i, (name, row) in enumerate(above_200.iterrows()):
    nutrient_name = name.split(" (")[0]
    y_pos = y_start + i * line_spacing
    plt.text(x_offset, y_pos, f"{nutrient_name}:", fontsize=14,
             fontweight='bold', ha='left', color='black')
    plt.text(x_offset + 1.0, y_pos, f"{int(row['Percent of RDA'])}%", fontsize=14,
             fontweight='bold', ha='left', color='green')

# Final formatting
plt.xticks(ticks=range(len(labels_cleaned)), labels=labels_cleaned, rotation=0, fontsize=9)
plt.ylabel("Percent of RDA", fontsize=11)
plt.title("Micronutrient Intake\n≤ 200% of RDA (Bar Chart) | > 200% of RDA (Text Right)", fontsize=13)
plt.ylim(0, y_start + len(above_200) * line_spacing + 10)
plt.tight_layout()
plt.show()
