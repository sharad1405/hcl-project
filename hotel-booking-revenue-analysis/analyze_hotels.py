import os
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat as nbf
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")

base = Path(__file__).resolve().parent
raw_file = base / "data" / "raw" / "hotel_data.csv"
charts = base / "charts"
clean_folder = base / "data" / "processed"
notebooks = base / "notebooks"

charts.mkdir(exist_ok=True)
clean_folder.mkdir(parents=True, exist_ok=True)
notebooks.mkdir(exist_ok=True)

# Load the original file. I will not change this file.
df = pd.read_csv(raw_file)
original_rows, original_columns = df.shape
missing_start = int(df.isna().sum().sum())
duplicates_start = int(df.duplicated().sum())

print("Original shape:", df.shape)
print("Missing values:", missing_start)
print("Duplicate rows:", duplicates_start)

# Fix the names of cities so all forms become one consistent value.
df["City"] = df["City"].astype(str).str.strip().str.lower()
df["City"] = df["City"].replace({
    "delhi": "Delhi",
    "mumbai": "Mumbai",
    "bengaluru": "Bengaluru",
    "jaipur": "Jaipur",
    "goa": "Goa",
})

# Remove exact repeated rows.
df = df.drop_duplicates().copy()

# Fill blanks in the channel column with the most common channel.
df["Booking_Channel"] = df["Booking_Channel"].fillna(df["Booking_Channel"].mode().iloc[0])

# Fill blank numbers with the median for that column.
for col in ["Guests", "Lead_Time_Days", "Guest_Age"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df[col] = df[col].fillna(df[col].median())

# Guest ages outside 18 to 80 do not look realistic.
valid_age = df.loc[df["Guest_Age"].between(18, 80), "Guest_Age"].median()
df.loc[~df["Guest_Age"].between(18, 80), "Guest_Age"] = valid_age

df["Check_In_Date"] = pd.to_datetime(df["Check_In_Date"], errors="coerce")

number_columns = [
    "Nights", "Guests", "Lead_Time_Days", "Room_Rate_INR",
    "Guest_Age", "Total_Revenue_INR"
]
df[number_columns] = df[number_columns].round().astype(int)

# A few extra columns used in the notebook.
df["Expected_Revenue_INR"] = df["Nights"] * df["Room_Rate_INR"]
df["Revenue_per_Guest_INR"] = df["Total_Revenue_INR"] / df["Guests"]

df["Revenue_Status"] = "Average"
df.loc[df["Total_Revenue_INR"] < 10000, "Revenue_Status"] = "At Risk"
df.loc[df["Total_Revenue_INR"] >= 20000, "Revenue_Status"] = "High Value"

df["Stay_Length_Band"] = pd.cut(
    df["Nights"],
    bins=[0, 2, 5, 10],
    labels=["Short", "Medium", "Long"]
)
df["At_Risk"] = df["Total_Revenue_INR"] < 10000

clean_file = clean_folder / "hotel_data_clean.csv"
df.to_csv(clean_file, index=False)
print("Cleaned shape:", df.shape)

# --- numbers used in the report ---
revenue = df["Total_Revenue_INR"]
at_risk = df[df["At_Risk"]]

print("Average revenue:", round(revenue.mean(), 2))
print("Median revenue:", round(revenue.median(), 2))
print("Minimum revenue:", revenue.min())
print("Maximum revenue:", revenue.max())
print("At-risk count:", len(at_risk))
print("At-risk percentage:", round(len(at_risk) / len(df) * 100, 1))

# Keeping only a few useful charts.
plt.figure(figsize=(8, 4.5))
plt.hist(revenue, bins=18, color="#84a8c4", edgecolor="white")
plt.title("How booking revenue is spread")
plt.xlabel("Total revenue (INR)")
plt.ylabel("Bookings")
plt.tight_layout()
plt.savefig(charts / "revenue_distribution.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
ax[0].scatter(df["Nights"], revenue, s=18, color="#7896b3", alpha=0.7)
ax[0].set_title("Nights and revenue")
ax[0].set_xlabel("Nights")
ax[0].set_ylabel("Revenue (INR)")

ax[1].scatter(df["Room_Rate_INR"], revenue, s=18, color="#d18d62", alpha=0.7)
ax[1].set_title("Room rate and revenue")
ax[1].set_xlabel("Room rate (INR)")
ax[1].set_ylabel("Revenue (INR)")
plt.tight_layout()
plt.savefig(charts / "nights_and_room_rate.png", dpi=150)
plt.close()

# One chart for room category averages.
room_avg = df.groupby("Room_Type")["Total_Revenue_INR"].mean().sort_values()
plt.figure(figsize=(7.5, 4.2))
room_avg.plot(kind="bar", color=["#8db1c7", "#d1a35c", "#b87867"])
plt.title("Average revenue by room type")
plt.xlabel("Room type")
plt.ylabel("Average revenue (INR)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(charts / "revenue_by_room_type.png", dpi=150)
plt.close()

# One chart for city averages.
city_avg = df.groupby("City")["Total_Revenue_INR"].mean().sort_values()
plt.figure(figsize=(8, 4.2))
city_avg.plot(kind="bar", color="#78a1b5")
plt.title("Average revenue in each city")
plt.xlabel("City")
plt.ylabel("Average revenue (INR)")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(charts / "revenue_by_city.png", dpi=150)
plt.close()

# A small count chart for at-risk bookings.
at_risk_by_city = at_risk["City"].value_counts().sort_values()
plt.figure(figsize=(7.5, 4.2))
at_risk_by_city.plot(kind="barh", color="#c47b72")
plt.title("At-risk bookings by city")
plt.xlabel("Number of bookings")
plt.ylabel("City")
plt.tight_layout()
plt.savefig(charts / "at_risk_by_city.png", dpi=150)
plt.close()

# --- notebook text and code ---
cells = [
    nbf.v4.new_markdown_cell(
        "# Hotel Booking Revenue Analysis\n\n"
        "I am using the hotel booking file to understand which bookings make more revenue "
        "and which bookings may need attention. In this study, a booking is **At Risk** "
        "if `Total_Revenue_INR` is below ₹10,000."
    ),
    nbf.v4.new_markdown_cell("## 1. Reading the file"),
    nbf.v4.new_code_cell(
        "import pandas as pd\nimport matplotlib.pyplot as plt\n\n"
        "df = pd.read_csv('../data/raw/hotel_data.csv')\n"
        "print(df.shape)\ndf.head()"
    ),
    nbf.v4.new_markdown_cell(
        "The file has 255 rows and 12 columns. I checked the last few rows, column types "
        "and basic counts before cleaning."
    ),
    nbf.v4.new_code_cell(
        "df.tail()\n"
        "print(df.dtypes)\n"
        "print('\\nMissing values:')\n"
        "print(df.isna().sum())\n"
        "print('\\nDuplicate rows:', df.duplicated().sum())"
    ),
    nbf.v4.new_markdown_cell(
        "## 2. Problems I found\n\n"
        "- 5 duplicate rows\n"
        "- City names were written in different ways\n"
        "- 5 missing booking-channel values\n"
        "- 5 missing guest counts\n"
        "- 5 missing lead-time values\n"
        "- 5 missing ages\n"
        "- 2 impossible ages: -27 and 212"
    ),
    nbf.v4.new_markdown_cell(
        "## 3. Cleaning\n\n"
        "I removed repeated rows and made city names consistent. Blank values were filled "
        "with the most common or middle value. For the two strange ages, I used the median "
        "of the valid ages instead of deleting the whole bookings."
    ),
    nbf.v4.new_code_cell(
        "df['City'] = df['City'].str.strip().str.lower()\n"
        "df['City'] = df['City'].replace({\n"
        "    'delhi':'Delhi', 'mumbai':'Mumbai', 'bengaluru':'Bengaluru',\n"
        "    'jaipur':'Jaipur', 'goa':'Goa'\n"
        "})\n"
        "df = df.drop_duplicates()\n"
        "df['Booking_Channel'] = df['Booking_Channel'].fillna(df['Booking_Channel'].mode()[0])\n"
        "for c in ['Guests', 'Lead_Time_Days', 'Guest_Age']:\n"
        "    df[c] = pd.to_numeric(df[c], errors='coerce')\n"
        "    df[c] = df[c].fillna(df[c].median())\n"
        "valid_median = df[df['Guest_Age'].between(18,80)]['Guest_Age'].median()\n"
        "df.loc[~df['Guest_Age'].between(18,80), 'Guest_Age'] = valid_median\n"
        "df['Check_In_Date'] = pd.to_datetime(df['Check_In_Date'])\n"
        "print('Cleaned shape:', df.shape)\n"
        "print('Missing values:', df.isna().sum().sum())\n"
        "print('Duplicate rows:', df.duplicated().sum())"
    ),
    nbf.v4.new_markdown_cell(
        "## 4. Extra columns\n\n"
        "I also calculated expected revenue, revenue per guest, a broad revenue status "
        "and a short/medium/long stay label."
    ),
    nbf.v4.new_code_cell(
        "df['Expected_Revenue_INR'] = df['Nights'] * df['Room_Rate_INR']\n"
        "df['Revenue_per_Guest_INR'] = df['Total_Revenue_INR'] / df['Guests']\n"
        "df['Revenue_Status'] = 'Average'\n"
        "df.loc[df['Total_Revenue_INR'] < 10000, 'Revenue_Status'] = 'At Risk'\n"
        "df.loc[df['Total_Revenue_INR'] >= 20000, 'Revenue_Status'] = 'High Value'\n"
        "df['Stay_Length_Band'] = pd.cut(df['Nights'], [0,2,5,10], labels=['Short','Medium','Long'])\n"
        "df['At_Risk'] = df['Total_Revenue_INR'] < 10000\n"
        "df.to_csv('../data/processed/hotel_data_clean.csv', index=False)\n"
        "df.head()"
    ),
    nbf.v4.new_markdown_cell("## 5. Question 1: What does revenue look like?"),
    nbf.v4.new_code_cell(
        "revenue = df['Total_Revenue_INR']\n"
        "print('Average:', round(revenue.mean(), 2))\n"
        "print('Median:', revenue.median())\n"
        "print('Lowest:', revenue.min())\n"
        "print('Highest:', revenue.max())"
    ),
    nbf.v4.new_code_cell(
        "plt.figure(figsize=(8,4.5))\n"
        "plt.hist(revenue, bins=18, color='#84a8c4', edgecolor='white')\n"
        "plt.title('How booking revenue is spread')\n"
        "plt.xlabel('Revenue (INR)')\n"
        "plt.ylabel('Bookings')\n"
        "plt.tight_layout()\n"
        "plt.savefig('../charts/revenue_distribution.png', dpi=150)\n"
        "plt.show()"
    ),
    nbf.v4.new_markdown_cell(
        "The average is ₹16,651.24 and the middle value is ₹16,165. "
        "The chart is uneven and slightly stretched towards high revenue."
    ),
    nbf.v4.new_markdown_cell("## 6. Question 2: Do nights or room rate affect revenue?"),
    nbf.v4.new_code_cell(
        "print('Correlations:')\n"
        "print(df[['Nights','Room_Rate_INR','Guests','Lead_Time_Days','Guest_Age','Total_Revenue_INR']].corr()['Total_Revenue_INR'])"
    ),
    nbf.v4.new_code_cell(
        "fig, ax = plt.subplots(1,2, figsize=(11,4.2))\n"
        "ax[0].scatter(df['Nights'], revenue, s=18, color='#7896b3', alpha=.7)\n"
        "ax[0].set(title='Nights and revenue', xlabel='Nights', ylabel='Revenue (INR)')\n"
        "ax[1].scatter(df['Room_Rate_INR'], revenue, s=18, color='#d18d62', alpha=.7)\n"
        "ax[1].set(title='Room rate and revenue', xlabel='Room rate (INR)', ylabel='Revenue (INR)')\n"
        "plt.tight_layout()\n"
        "plt.savefig('../charts/nights_and_room_rate.png', dpi=150)\n"
        "plt.show()"
    ),
    nbf.v4.new_markdown_cell(
        "Nights and room rate have the strongest positive connections in this table. "
        "Guest count, lead time and age do not show much of a pattern."
    ),
    nbf.v4.new_markdown_cell("## 7. Question 3: Which groups have higher revenue?"),
    nbf.v4.new_code_cell(
        "for col in ['City','Room_Type','Booking_Channel','Guest_Type']:\n"
        "    print('\\nAverage by', col)\n"
        "    print(df.groupby(col)['Total_Revenue_INR'].mean().round(2).sort_values(ascending=False))"
    ),
    nbf.v4.new_code_cell(
        "room_avg = df.groupby('Room_Type')['Total_Revenue_INR'].mean().sort_values()\n"
        "room_avg.plot(kind='bar', color=['#8db1c7','#d1a35c','#b87867'], figsize=(7.5,4.2))\n"
        "plt.title('Average revenue by room type')\n"
        "plt.xlabel('Room type')\n"
        "plt.ylabel('Average revenue (INR)')\n"
        "plt.xticks(rotation=0)\n"
        "plt.tight_layout()\n"
        "plt.savefig('../charts/revenue_by_room_type.png', dpi=150)\n"
        "plt.show()"
    ),
    nbf.v4.new_markdown_cell(
        "Suites have the highest average revenue at ₹27,320. Standard rooms are lowest "
        "at ₹12,977. Among the categories checked, room type has the largest spread."
    ),
    nbf.v4.new_markdown_cell("## 8. Question 4: Which bookings need attention?"),
    nbf.v4.new_code_cell(
        "at_risk = df[df['At_Risk']].copy()\n"
        "print('At-risk count:', len(at_risk))\n"
        "print('Percentage:', round(len(at_risk)/len(df)*100, 1), '%')\n"
        "print('\\nBy city:\\n', at_risk['City'].value_counts())\n"
        "print('\\nBy room type:\\n', at_risk['Room_Type'].value_counts())\n"
        "print('\\nBy channel:\\n', at_risk['Booking_Channel'].value_counts())"
    ),
    nbf.v4.new_code_cell(
        "counts = at_risk['City'].value_counts().sort_values()\n"
        "counts.plot(kind='barh', color='#c47b72', figsize=(7.5,4.2))\n"
        "plt.title('At-risk bookings by city')\n"
        "plt.xlabel('Number of bookings')\n"
        "plt.ylabel('City')\n"
        "plt.tight_layout()\n"
        "plt.savefig('../charts/at_risk_by_city.png', dpi=150)\n"
        "plt.show()\n"
        "\n"
        "at_risk[['Booking_ID','City','Room_Type','Booking_Channel','Nights','Room_Rate_INR','Total_Revenue_INR']].head(10)"
    ),
    nbf.v4.new_markdown_cell(
        "### Short conclusion\n\n"
        "There are 50 at-risk bookings, which is 20% of the cleaned file. Jaipur has "
        "the most, followed by the pattern in the table. Standard rooms and Mobile app "
        "bookings appear particularly often in this low-revenue group.\n\n"
        "The data is synthetic and small, so these are useful patterns to investigate "
        "rather than proof that one factor caused higher revenue."
    ),
]

nb = nbf.v4.new_notebook(cells=cells)
nb["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nbf.write(nb, notebooks / "hotel_analysis.ipynb")

subprocess.run([
    sys.executable, "-m", "nbconvert",
    "--to", "notebook",
    "--execute", str(notebooks / "hotel_analysis.ipynb"),
    "--output", str(notebooks / "hotel_analysis.ipynb"),
    "--ExecutePreprocessor.timeout=180",
], check=True)

city_avg = df.groupby("City")["Total_Revenue_INR"].mean().sort_values(ascending=False)
room_avg = df.groupby("Room_Type")["Total_Revenue_INR"].mean().sort_values(ascending=False)
channel_avg = df.groupby("Booking_Channel")["Total_Revenue_INR"].mean().sort_values(ascending=False)
guest_avg = df.groupby("Guest_Type")["Total_Revenue_INR"].mean().sort_values(ascending=False)

readme = f"""# Hotel Booking Revenue Analysis

## About this project

I looked at 250 hotel bookings and tried to understand why some bookings bring in more revenue than others.
For this study, I marked a booking as At Risk if it earned less than ₹10,000.

## Dataset

The original file had 255 rows and 12 columns. It contains booking details such as city, room type,
booking channel, number of nights, room rate and total revenue.

## Cleaning

I removed 5 duplicate rows. I also:

- made the city names consistent
- filled 5 missing booking channels
- filled missing guest, lead-time and age values
- replaced two ages that looked wrong
- changed the check-in column to a date
- created a few extra fields for analysis

The cleaned file has 250 rows and no missing or duplicate values.

## Questions checked

1. What does revenue look like overall?
2. Do nights and room rate affect revenue?
3. Do different cities or room categories earn different average revenue?
4. Which bookings need attention?

## Main findings

- Average revenue was about ₹{revenue.mean():,.2f}; the middle value was ₹{revenue.median():,.2f}.
- Revenue went from ₹{revenue.min():,.2f} to ₹{revenue.max():,.2f}.
- Nights and room rate had the clearest connection with revenue.
- Suites earned the most on average at about ₹{room_avg.iloc[0]:,.2f}.
- Goa had the highest city average at about ₹{city_avg.iloc[0]:,.2f}.
- Travel agent bookings had the highest average channel revenue at about ₹{channel_avg.iloc[0]:,.2f}.
- Leisure bookings had the highest average guest-type revenue at about ₹{guest_avg.iloc[0]:,.2f}.
- {len(at_risk)} bookings ({len(at_risk)/len(df)*100:.1f}% ) were below ₹10,000.
- Jaipur had the most At Risk bookings.

## Charts

I kept the charts simple and only used them for the analysis:

- revenue histogram
- nights and room rate scatter plots
- average revenue by room type
- average revenue by city
- at-risk bookings by city

They are saved in the `charts` folder.

## What I would suggest

- Check Suite availability and pricing because this room type earns the most.
- Review Jaipur bookings and Standard rooms more closely.
- Compare room rate and stay length together when making pricing decisions.

## Note

The data is synthetic and small. The results are useful for practice, but they do not prove that
one booking feature caused another result.

## Folder

```text
hotel-booking-revenue-analysis/
├── data/raw/hotel_data.csv
├── data/processed/hotel_data_clean.csv
├── notebooks/hotel_analysis.ipynb
├── charts/
├── analyze_hotels.py
└── READMe.md
```

## Run again

```bash
python -m pip install -r requirement.txt
python analyze_hotels.py
```
"""

(base / "READMe.md").write_text(readme, encoding="utf-8")

print("Done.")
