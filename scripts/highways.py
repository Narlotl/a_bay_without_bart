# Information on which highway segments will be most affected by loss of service.

import pandas as pd

# Calculate average car occupancy
carpool_df = pd.read_csv('data/ACSDT5Y2024.B08301-Data.csv', usecols=[
    'B08301_003E', # Drove alone
    'B08301_005E', # 2-person carpool
    'B08301_006E', # 3-person carpool
    'B08301_007E', # 4-person carpool
    'B08301_008E', # 5- or 6-person carpool
    'B08301_009E', # 7-or-more-person carpool
],
    skiprows=[1] # Skip second header
)
sums = carpool_df.sum()
print('Average occupancy:', (sums * [1, 2, 3, 4, 5.5, 7] / sums.sum()).sum()) # Weight counts by occupancy and divide by total

# Calculate ridership for each station pair by hour

from ridership import full_ridership_df, is_workday
from geo import get_bearing

# Map station codes to ther cat ID in the paths
stations = ['MLPT', 'BERY', 'CIVC', 'CONC', 'COLM', 'PLZA', 'DALY', 'NCON', 'FRMT', 'GLEN', 'HAYW', 'DELN', 'COLS', 'DBRK', 'BAYF', 'BALB', 'SBRN', 'SHAY', 'WCRK', 'NBRK', 'ORIN', 'WOAK', 'SANL', '16TH', '24TH', '12TH', 'UCTY', 'WDUB', 'MLBR', 'MONT', 'DUBL', 'LAKE', 'PHIL', 'MCAR', 'POWL', 'RICH', 'ROCK', 'EMBR', 'PITT', 'CAST', 'LAFY', 'SSAN', '19TH', 'ASHB', 'FTVL', 'WARM', 'PCTR', 'ANTC']
station_cats = {}
for i in range(len(stations)):
    station_cats[stations[i]] = i + 1

# Load station geographic information
station_df = pd.read_csv('gis/station_highway_points.csv')

# Get total ridership for each pair to calculate emissions

# Convert station codes to numerical IDs
full_ridership_df.entry = full_ridership_df.entry.map(station_cats)
full_ridership_df.exit = full_ridership_df.exit.map(station_cats)
# Filter to unique origin-destination pairs
full_ridership_df = full_ridership_df.loc[(full_ridership_df.entry != full_ridership_df.exit) & full_ridership_df.entry.notna() & full_ridership_df.exit.notna()].astype({'entry': int, 'exit': int})
# Add pair column in "entry-exit" form
full_ridership_df.insert(2, 'pair', full_ridership_df.entry.astype(str).str.cat(full_ridership_df.exit.astype(str), sep='-'))
# Write data and clear from memory
full_ridership_df.groupby(['entry', 'exit', 'pair']).sum(numeric_only=True).drop(columns='hour').to_csv('gis/station_pair_totals.csv')
ridership_df = full_ridership_df.copy().loc[full_ridership_df.date.map(is_workday)].drop(columns='date')
del full_ridership_df

# Get ridership between each station pair for each hour

def index_with_direction(entry, exit, series):
    # Adds direction to the index of a series representing pair ridership
    # Back is south/west, ahead is north/east
    # https://dot.ca.gov/-/media/dot-media/programs/traffic-operations/documents/back-and-ahead-leg-traffic-count-diagram-a11y.pdf
    entry = station_df.iloc[entry - 1]
    exit = station_df.iloc[exit - 1]
    bearing = get_bearing(entry.Y, entry.X, exit.Y, exit.X)
    direction = 'ahead' if bearing > -45 and bearing <= 135 else 'back'

    series.index = series.index.map(lambda hour: str(hour) + '_' + direction)
    return series

pairs = ridership_df.groupby(['entry', 'exit', 'pair'])
# Create a column for each hour in each direction
hour_columns = [str(hour) + '_' + direction for hour in range(24) for direction in ('back', 'ahead')]
pair_df = pd.DataFrame(columns=['entry', 'exit', 'pair'] + hour_columns, data=[
    {'entry': pair[0], 'exit': pair[1], 'pair': pair[2]} |
        # Get average riders for each hour as dict
        index_with_direction(pair[0], pair[1], df.groupby('hour').mean(numeric_only=True)['count']).to_dict()
        for pair, df in pairs
]).fillna(0)

pair_df.to_csv('gis/station_pair_ridership.csv', index=False)
