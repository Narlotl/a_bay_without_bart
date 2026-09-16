# Information on how many bus-hours AC Transit ran in from July 6 2025 to July 6 2026.

from datetime import datetime
import pandas as pd
from os import listdir
from zipfile import ZipFile

# Constants to split bytes with
newline = bytes('\r\n', 'utf-8')
comma = bytes(',', 'utf-8')

# Order GTFS feed zips by date
file_dates = []
zips = listdir('data/in/act_gtfs')
for zip in zips:
    with ZipFile('data/in/act_gtfs/' + zip, 'r') as feed:
        with feed.open('calendar.txt', 'r') as calendar:
            # Get start_date column of first data row
            date = calendar.read() \
                .split(newline)[1] \
                .split(comma)[-2]
            date = datetime(int(date[0:4]), int(date[4:6]), int(date[6:]))

            file_dates.append({
                'date':  date,
                'file': zip
            })
file_dates.sort(key=lambda fd: fd['date'])

def gtfs_time_to_seconds(gtfs_time):
    gtfs_time = gtfs_time.split(':')
    return int(gtfs_time[0]) * 3600 + int(gtfs_time[1]) * 60 + int(gtfs_time[2])

bus_hours = 0
for i in range(len(file_dates)):
    schedule = file_dates[i]
    day_counts = [0] * 7
    start = datetime(2025, 7, 6) if i == 0 else schedule['date']
    end = datetime(2026, 7, 6) if i == len(file_dates) - 1 else file_dates[i + 1]['date']
    start_weekday = start.weekday()

    # Loop through each day in schedule period
    for i in range((end - start).days):
        day_counts[(start_weekday + i) % 7] += 1

    with ZipFile('data/in/act_gtfs/' + schedule['file'], 'r') as feed:
        trips_df = pd.read_csv(feed.open('trips.txt', 'r'), usecols=['service_id', 'trip_id'], dtype={'service_id': str})
        stop_times_df = pd.read_csv(feed.open('stop_times.txt', 'r'), usecols=['trip_id', 'departure_time'], dtype={'service_id': str})
        trips_df = stop_times_df.merge(trips_df, on='trip_id')
        del stop_times_df
        trips_df = trips_df.groupby('trip_id').aggregate({'departure_time': ['min', 'max'], 'service_id': 'max'})
        trips_df.insert(0, 'length', trips_df.departure_time['max'].map(gtfs_time_to_seconds) - trips_df.departure_time['min'].map(gtfs_time_to_seconds))

        with feed.open('calendar.txt', 'r') as calendar:
            services = calendar.read().split(newline)[1:]
            for service in services:
                if not service:
                    continue

                service = service.split(comma)
                # Count how many days service pattern runs
                total_days = 0
                for i in range(7):
                    total_days += day_counts[i] * (service[i + 1][0] - 0x30) # Subtract ascii 0 to convert to numeric value

                # Sum lengths of trips matching service
                bus_hours += trips_df.loc[trips_df.service_id['max'] == str(service[0], 'utf-8')].length.sum() / 3600 * total_days

print(bus_hours)
