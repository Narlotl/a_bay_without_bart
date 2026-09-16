# Information on routes that service a BART station

import pandas as pd
from geo import haversine

# Get trip_id for stops at BART
stops_df = pd.read_csv('data/in/near_station_stops.csv', dtype={'stop_id': str})
stop_times_df = pd.read_csv('data/in/regional_gtfs/stop_times.txt', usecols=['trip_id', 'stop_id'], dtype=str)
trips = stop_times_df.loc[stop_times_df.stop_id.isin(stops_df.stop_id)].trip_id
del stops_df
del stop_times_df

# Get trips for BART station stops
trips_df = pd.read_csv('data/in/regional_gtfs/trips.txt', usecols=['trip_id', 'route_id', 'shape_id'], dtype=str)
trips_df = trips_df.loc[trips_df.trip_id.isin(trips)].drop_duplicates(subset='route_id')
routes = set(trips_df.route_id)

# Get routes for BART-connnecting trips
routes_df = pd.read_csv('data/in/regional_gtfs/routes.txt', usecols=['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_color', 'route_text_color'], dtype=str)
# Filter to connecting routes not operated by BART
routes_df = routes_df.loc[(routes_df.agency_id != 'BA') & routes_df.route_id.isin(routes)]
# Get shapes for selected routes
shapes = set(trips_df.loc[trips_df.route_id.isin(routes_df.route_id)].shape_id)

# Add agency name and save to file
agency_df = pd.read_csv('data/in/regional_gtfs/agency.txt', usecols=['agency_id', 'agency_name'])
routes_df = routes_df.merge(agency_df, on='agency_id')
routes_df.to_csv('data/out/connecting_routes.csv', index=False, columns=['route_short_name', 'route_long_name', 'agency_name', 'route_color', 'route_text_color'])
del trips_df, routes_df, agency_df

# Calculate total route length
shapes_df = pd.read_csv('data/in/regional_gtfs/shapes.txt', usecols=['shape_id', 'shape_pt_lat', 'shape_pt_lon'])
shapes = shapes_df.loc[shapes_df.shape_id.isin(shapes)].groupby('shape_id')
total_length = 0
for shape in shapes:
    shape = shape[1]
    for i in range(1, len(shape.index)):
        points = shape.iloc[[i - 1, i]]
        total_length += haversine(points.shape_pt_lat.iloc[0], points.shape_pt_lon.iloc[0], points.shape_pt_lat.iloc[1], points.shape_pt_lon.iloc[1])
print('Total length:', total_length, 'km')
