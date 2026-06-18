from math import asin, cos, radians, sin, sqrt

from ..regions import ADJACENCY, REGIONS

EARTH_RADIUS_KM = 6371.0

SAME_REGION_SCORE = 100.0
ADJACENT_REGION_SCORE = 60.0
FAR_REGION_SCORE = 20.0


def haversine_km(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return None
    rlat1, rlng1, rlat2, rlng2 = map(radians, (lat1, lng1, lat2, lng2))
    dlat = rlat2 - rlat1
    dlng = rlng2 - rlng1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def region_distance_km(region_a, region_b):
    a = REGIONS.get(region_a)
    b = REGIONS.get(region_b)
    if not a or not b:
        return None
    return haversine_km(a[0], a[1], b[0], b[1])


def score_candidate(pickup_region, pickup_lat, pickup_lng, vehicle):
    if vehicle.joriy_hudud == pickup_region:
        base = SAME_REGION_SCORE
    elif vehicle.joriy_hudud in ADJACENCY.get(pickup_region, set()):
        base = ADJACENT_REGION_SCORE
    else:
        base = FAR_REGION_SCORE

    distance = haversine_km(
        pickup_lat, pickup_lng, vehicle.joriy_lat, vehicle.joriy_lng
    )
    if distance is None:
        distance = region_distance_km(pickup_region, vehicle.joriy_hudud)

    proximity_bonus = 0.0
    if distance is not None:
        proximity_bonus = max(0.0, 40.0 - distance / 20.0)

    return base + proximity_bonus, distance
