# Geographic helper functions

from math import radians, cos, sin, asin, sqrt, atan2, degrees

def haversine(lat1, lon1, lat2, lon2):
    """
    Source - https://stackoverflow.com/a/4913653␍
    Posted by Michael Dunn, modified by community. See post 'Timeline' for change history␍
    Retrieved 2026-05-08, License - CC BY-SA 4.0␍
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def get_bearing(lat1, lon1, lat2, lon2):
    """
    Source - https://stackoverflow.com/a/64747209
    Posted by aliff danial, modified by community. See post 'Timeline' for change history
    Retrieved 2026-05-08, License - CC BY-SA 4.0
    """
    dLon = (lon2 - lon1)
    x = cos(radians(lat2)) * sin(radians(dLon))
    y = cos(radians(lat1)) * sin(radians(lat2)) - sin(radians(lat1)) * cos(radians(lat2)) * cos(radians(dLon))
    bearing = atan2(x,y)
    bearing = degrees(bearing)

    return bearing
