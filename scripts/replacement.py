# Information on what would be needed to fully replace BART service.

import pandas as pd
from ridership import full_ridership_df, ridership_df, ridership_days, peak_hour
from math import ceil

print('Work days:', ridership_days)
print()

# Load station agency data
station_df = pd.read_csv('data/out/station_agencies.csv')
west_bay_stations = station_df.loc[(station_df.agency == 'SF Muni') | (station_df.agency == 'SamTrans')].station

# Calculate average transbay rides per day
transbay_df = ridership_df.loc[ridership_df.entry.isin(west_bay_stations) != ridership_df.exit.isin(west_bay_stations)]
transbay_rides = round(transbay_df['count'].sum() / ridership_days)
print('Daily transbay rides:', transbay_rides)

# Load ferry fleet data
ferry_df = pd.read_csv('data/in/ferry_fleet.csv')

# Print information about ferries needed to replace BART transbay service

# Number of additional trips per day needed
mean_capacity = ferry_df.capacity.mean()
print('Additional transbay ferry trips needed:', ceil(transbay_rides / mean_capacity))
# Count how many trips ferries already make per day
with open('data/in/sf_bay_ferry_gtfs_trips.txt', 'r') as trips:
    # Exclude header
    trip_count = -1
    for line in trips:
        # Exclude Oakland-Alameda shuttle trips
        if not line.startswith('77075'):
            trip_count += 1
    print('Current transbay ferry trips:', trip_count)

# Number of ferries needed to satisfy peak hour demand
peak_hour_transbay_rides = transbay_df.groupby('hour').sum(numeric_only=True).max()['count'] / ridership_days
# A single vessel can make two trips from each side in an hour
peak_west_east = transbay_df.loc[ridership_df.entry.isin(west_bay_stations)].groupby('hour').sum(numeric_only=True).max()['count'] / ridership_days
peak_single_direction = max(peak_west_east, peak_hour_transbay_rides - peak_west_east)
print('Peak hour transbay rides:', round(peak_hour_transbay_rides))
print('Peah hour single-direction rides:', round(peak_single_direction))
peak_hour_ferries_needed = peak_single_direction / mean_capacity / 2
print('Peak hour ferries needed:', ceil(peak_hour_ferries_needed))
print('Peak hour fleets needed:', round(peak_hour_ferries_needed / len(ferry_df.index) * 100) / 100)

# Cost of peak hour fleet
newest_vessel = ferry_df.iloc[ferry_df.year.idxmax()]
newest_vessels_needed = peak_single_direction / newest_vessel.capacity / 2
print(newest_vessel.vessel, 'vessels needed:', ceil(newest_vessels_needed))
print(newest_vessel.vessel, 'vessels cost (millions of dollars):', ceil(newest_vessels_needed) * newest_vessel.cost)

print()
del ferry_df
del transbay_df

# Information on how many riders each agency would need to take on.

# Map which agencies connect each other
agency_connections = {
    'AC Transit': ['County Connection', 'SF Muni', 'SamTrans', 'VTA', 'Wheels'],
    'County Connection': ['AC Transit', 'Tri Delta Transit', 'Wheels'],
    'SF Muni': ['AC Transit', 'SamTrans'],
    'SamTrans': ['AC Transit', 'SF Muni', 'VTA'],
    'Tri Delta Transit': ['County Connection'],
    'VTA': ['AC Transit', 'SamTrans'],
    'Wheels': ['AC Transit', 'County Connection']
}

# Initialize counts
additional_agency_count = {}
for agency in agency_connections:
    additional_agency_count[agency] = 0
# Adds to the count of every agency between a start and end agency (inclusive)
def add_to_agency_count(start, end, count):
    if start == end:
        additional_agency_count[start] += count
        return

    # If an end only has one connection, move forward on that end
    start_connections = agency_connections[start]
    if len(start_connections) == 1:
        additional_agency_count[start] += count
        add_to_agency_count(start_connections[0], end, count)
        return
    end_connections = agency_connections[end]
    if len(end_connections) == 1:
        additional_agency_count[end] += count
        add_to_agency_count(start, end_connections[0], count)
        return

    # Otherwise find matching connection between them
    for connection in start_connections:
        if connection in end_connections:
            additional_agency_count[start] += count
            additional_agency_count[connection] += count
            additional_agency_count[end] += count

# Count ridership for each agency pairing by hour
# Create start/end agency pairs
ridership_df = ridership_df.merge(station_df, left_on='entry', right_on='station').rename(columns={'agency': 'start'})
ridership_df = ridership_df.merge(station_df, left_on='exit', right_on='station').rename(columns={'agency': 'end'})
ridership_df.drop(columns=['entry', 'exit', 'station_x', 'station_y'], inplace=True)

# Calculate total replacement riderhsip
total_ridership = ridership_df.groupby(['start', 'end']).sum() / ridership_days
total_ridership.drop(columns='hour', inplace=True)
for pair, count in total_ridership.iterrows():
    add_to_agency_count(pair[0], pair[1], count['count'])
# Compare to existing riderhsip
agency_ridership_df = pd.read_csv('data/out/agency_ridership.csv')
print("Total weekday ridership increase:")
for agency in additional_agency_count:
    current_ridership = agency_ridership_df.loc[agency_ridership_df.agency == agency, 'ridership'].iloc[0]
    print(agency, current_ridership, '+' + str(round(additional_agency_count[agency])), '(' + str(round(100 * additional_agency_count[agency] / current_ridership)) + '%)')
    # Reset count
    additional_agency_count[agency] = 0
print()

# Calculate peak hour replacement numbers
bus_capacity = 52 + 73 # New Flyer Xcelsior 60' seated and standing capacity, respectively (https://www.newflyer.com/site-content/uploads/2023/08/Xcelsior-CHARGE-FC.pdf)
# https://www.actransit.org/sites/default/files/2025-10/FY2025-26%20District%20Adopted%20Budget%20Book.pdf#page=54
bus_cost = 20.349973 / 9 # millions of dollars
peak_hour_pairs = ridership_df.loc[ridership_df.hour == peak_hour].groupby(['start', 'end']).sum() / ridership_days
peak_hour_pairs.drop(columns='hour', inplace=True)
# Add to counts
for pair, count in peak_hour_pairs.iterrows():
    add_to_agency_count(pair[0], pair[1], count['count'])
# Print results
print('Peak hour ridership increase:')
for agency in additional_agency_count:
    bus_count = ceil(additional_agency_count[agency] / bus_capacity)
    print(agency, round(additional_agency_count[agency]), '(' + str(bus_count) + ' buses / $' + str(round(bus_count * bus_cost * 10) / 10) + ' million)')
print()

# Calculate how many bus-hours AC Transit would need to run to cover all BART riders in its operating area
act_stations = station_df.loc[station_df.agency == 'AC Transit'].station
print('AC Transit annual bus-hours', full_ridership_df.loc[full_ridership_df.entry.isin(act_stations) | full_ridership_df.exit.isin(act_stations)]['count'].sum() / bus_capacity)
