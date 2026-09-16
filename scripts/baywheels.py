# Information on Bay Wheels rentals near BART stations.

import pandas as pd
from geo import haversine
from os import listdir
from zipfile import ZipFile

# Count total spaces near BART station
bw_stations_df = pd.read_csv('gis/bart_baywheels.csv')
print(bw_stations_df.capacity.sum(), 'total spaces')

ride_count = 0
total_distance = 0

# Approximate distance traveled as length of legs of right triangle connecting start and end
def trip_distance(row):
    return (haversine(row.start_lat, row.start_lng, row.end_lat, row.start_lng) + # Vertical leg
        haversine(row.end_lat, row.start_lng, row.end_lat, row.end_lng)) # Horizontal leg

for month in listdir('data/in/baywheels'):
    with ZipFile('data/in/baywheels/' + month) as zip:
        with zip.open((zip.namelist()[0])) as csv:
            # Count rides
            rides_df = pd.read_csv(csv, usecols=['start_station_name', 'end_station_name', 'start_lat', 'start_lng', 'end_lat', 'end_lng'])
            # Filter to rental stations near BART stations
            rides_df = rides_df.loc[rides_df.start_station_name.isin(bw_stations_df.name) | rides_df.end_station_name.isin(bw_stations_df.name)]
            ride_count += len(rides_df.index)

            # Calculate total distance
            total_distance += rides_df[['start_lat', 'start_lng', 'end_lat', 'end_lng']].apply(trip_distance, axis=1).sum()

print('Total rides:', ride_count)
print('Total distance (mi):', total_distance / 1.609344)
