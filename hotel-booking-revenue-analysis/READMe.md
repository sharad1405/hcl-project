# Hotel Booking Revenue Analysis

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

- Average revenue was about ₹16,651.24; the middle value was ₹16,165.00.
- Revenue went from ₹1,500.00 to ₹45,980.00.
- Nights and room rate had the clearest connection with revenue.
- Suites earned the most on average at about ₹27,320.00.
- Goa had the highest city average at about ₹20,760.91.
- Travel agent bookings had the highest average channel revenue at about ₹17,813.84.
- Leisure bookings had the highest average guest-type revenue at about ₹16,961.42.
- 50 bookings (20.0% ) were below ₹10,000.
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
