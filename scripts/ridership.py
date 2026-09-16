# Shared file to get workday ridership data.

import pandas as pd
from sys import argv
from datetime import date as Date

year = 2025

# Load ridership data
rows = int(argv[1]) if len(argv) > 1 else None
full_ridership_df = pd.read_csv('data/in/ridership.csv', names=['date', 'hour', 'entry', 'exit', 'count'], nrows=rows)

# Check if date in YYYY-MM-dd format is a non-holiday weekday
holidays = ['2025-01-01', '2025-01-20', '2025-02-17', '2025-05-26', '2025-06-19', '2025-07-04', '2025-09-01', '2025-10-13', '2025-11-11', '2025-11-27', '2025-12-15']
def is_workday(date):
    if date in holidays:
        return False

    date = date.split('-')
    return Date(int(date[0]), int(date[1]), int(date[2])).weekday() < 5

# Filter to workdays
ridership_df = full_ridership_df.copy().loc[full_ridership_df.date.map(is_workday)]

# Count how many days are in riderhsip count
ridership_days = len(set(ridership_df.date))
ridership_df.drop(columns='date', inplace=True)

# Find which hour has the most riders
peak_hour = ridership_df.groupby('hour').sum(numeric_only=True)['count'].idxmax()
