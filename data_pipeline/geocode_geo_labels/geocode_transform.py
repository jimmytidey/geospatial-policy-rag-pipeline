import sys,os
import googlemaps
from shapely.geometry import Point
from shapely.wkb import loads
from shapely import wkb
import binascii
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres

def geocode_row_geo_labels(row):
    """Process each row with multiple geocoding attempts and boundary checking."""
    location_names = row['openai_geo_labels']
    geocode_string_wide = row['geocode_string_wide']
    geocode_string_narrow = row['geocode_string_narrow']
    boundary_geom = get_boundary_geom(row['geo_boundary_id'])
    
    if not boundary_geom:
        print(f"Warning: No boundary geometry found for boundary_id: {row['geo_boundary_id']}")
        return None
    
    results = []
    for location in location_names:
        matched_location = process_location(str(location).strip(), geocode_string_wide, geocode_string_narrow, boundary_geom)
        if matched_location:
            results.append(matched_location)
        else:
            print(f"Warning: No matching location found within or near boundary for {location}")
    
    return results

def process_location(location, geocode_string_wide, geocode_string_narrow, boundary_geom):
    """Process a single location name with multiple geocoding attempts."""
    # Define search attempts with priority (wide+narrow is preferred)
    search_attempts = [
        {
            'query': f"{geocode_string_wide}, {geocode_string_narrow}, {location}",
            'priority': 1,  # Higher priority
            'type': 'wide_and_narrow'
        },
        {
            'query': f"{geocode_string_wide}, {location}",
            'priority': 2,  # Lower priority
            'type': 'wide_only'
        }
    ]
    
    # Store all results with their search type
    all_results = []
    for attempt in search_attempts:
        geocoded_results = geocode(attempt['query'])
        for result in geocoded_results:
            result['search_type'] = attempt['type']
            result['search_priority'] = attempt['priority']
            all_results.append(result)
    
    # First try to find points inside the boundary
    inside_points = []
    for result in all_results:
        if check_point_in_boundary(result['lat'], result['lng'], boundary_geom):
            result['location_type'] = 'inside_boundary'
            inside_points.append(result)
    
    # If we found points inside boundary, return the one with highest priority (lowest priority number)
    if inside_points:
        best_result = min(inside_points, key=lambda x: x['search_priority'])
        print(f"Found location inside boundary using {best_result['search_type']}: {best_result}")
        return best_result
    
    # If no point inside, find the nearest point within distance limit
    MAX_DISTANCE_METERS = 2000  # 2km limit
    nearest_points = []
    
    for result in all_results:
        point = Point(result['lng'], result['lat'])
        distance = boundary_geom.distance(point) * 111000  # Convert degrees to approximate meters (1 degree ≈ 111km)
        
        if distance <= MAX_DISTANCE_METERS:
            result['distance_to_boundary'] = distance
            result['location_type'] = 'near_boundary'
            nearest_points.append(result)
    
    if nearest_points:
        # Sort by priority first, then by distance
        best_result = min(nearest_points, key=lambda x: (x['search_priority'], x['distance_to_boundary']))
        print(f"Found nearest location {best_result['distance_to_boundary']:.0f}m from boundary using {best_result['search_type']}: {best_result}")
        return best_result
    
    return None

def geocode(search_string, max_results=3):
    """Geocode a search string and return top results."""
    gmaps = googlemaps.Client(key=os.environ["GOOGLEMAPS_API_KEY"])
    geocode_results = gmaps.geocode(search_string)
    
    results = []
    for result in geocode_results[:max_results]:
        location = result['geometry']['location']
        results.append({
            'location_name': search_string,
            'lat': location['lat'],
            'lng': location['lng'],
            'formatted_address': result['formatted_address']
        })
    return results

def get_boundary_geom(boundary_id):
    """Fetch boundary geometry from PostgreSQL."""
    pg = Postgres()
    result = pg.query("""
        SELECT ST_AsText(geom) as geom FROM geo_boundaries WHERE geo_boundary_id = %s
    """, [boundary_id])
    if result and len(result) > 0:
        from shapely import wkt
        try:
            return wkt.loads(result[0]['geom'])
        except Exception as e:
            print(f"Error converting geometry: {e}")
            print(f"Raw geometry: {result[0]['geom'][:100]}...")  # Print first 100 chars for debugging
            return None
    return None

def check_point_in_boundary(lat, lng, boundary_geom):
    """Check if a point is within the boundary geometry."""
    point = Point(lng, lat)  # Note: WGS84 is lng,lat
    return boundary_geom.contains(point)