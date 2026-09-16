# Information on which Census tracts are most affected by loss of service.

import pandas as pd
import numpy as np
import geojson
import shapely.wkt as wkt

# Load means of transportation data
means_df = pd.read_csv('data/in/ACSDT5Y2024.B08301-Data.csv', skiprows=[1], usecols=[
    'GEO_ID',
    'B08301_010E', # Estimate!!Total:!!Public transportation:
    'B08301_012E', # Estimate!!Total:!!Public transportation:!!Subway or elevated rail
])
# Create and calculate proportion column
means_df.insert(3, 'proportion', means_df.B08301_012E / means_df.B08301_010E)
# Drop unneeded data columns
means_df.drop('B08301_010E', axis=1, inplace=True)
means_df.drop('B08301_012E', axis=1, inplace=True)
# Turn NaN to 0
means_df.replace(np.nan, 0, inplace=True)

# Load departure time data
time_columns = ['B08132_0' + str(i) + 'E' for i in range(47, 61)] # Departure time rows for public transportation
times_df = pd.read_csv('data/in/ACSDT5Y2024.B08132-Data.csv', skiprows=[1], usecols=(['GEO_ID'] + time_columns))

# Load tract geography data
geo_df = pd.read_csv('data/in/tract_geography.csv')
geo_df.rename(columns={'GEOIDFQ': 'GEO_ID'}, inplace=True)

# Merge dataframes
df = geo_df.merge(means_df, on='GEO_ID').merge(times_df, on='GEO_ID')
del means_df
del times_df
del geo_df

# Multiply all counts by proportion of transit riders taking BART
for column in time_columns:
    df[column] = round(df[column] * df.proportion)
# Drop unneeded proportion column
df.drop('proportion', axis=1, inplace=True)

# Total ridership in each tract
df.insert(1, 'total', df.sum(numeric_only=True, axis=1).astype(int))

# Generate geojson data
features = []
def create_feature(row):
    shape = wkt.loads(row.WKT)
    feature = geojson.Feature(geometry=shape, properties={'total': row.total})
    features.append(feature)
df.apply(create_feature, axis=1)
feature_collection = geojson.FeatureCollection(features)

with open('data/out/data_acs.geojson', 'w') as f:
    f.write(geojson.dumps(feature_collection))
