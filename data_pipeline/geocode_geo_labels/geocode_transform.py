import sys,os,pprint
import googlemaps
from dotenv import load_dotenv
from shapely.geometry import Point,Polygon
from shapely import wkb
import binascii
from math import radians, cos, sin, sqrt, atan2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def geocode_row(row):

    # rows only have one label because of the cross join in the extract_labels_for_geocoding function
    
    geom = get_geometry(row)

    if not geom: 
        print("No bounding polygon or center point found, skipping geocode. This message will come up every run until the geometry is added to the table, or the document is marked at non-geocodable")
        return None

    if not 'geocode_string_narrow' in row and not 'geocode_string_wide' in row:
        print("No bounding polygon or center point found, skipping geocode. This message will come up every run until the geometry is added to the table, or the document is marked at non-geocodable")
        return None    
    
    openai_geo_label = row['openai_geo_label']
    wide_string = row.get('geocode_string_wide', False)
    narrow_string = row.get('geocode_string_narrow', False)

    print("--------------------------------")
    print("geocoding row from document: " + row['title'])
    print("Sections: " + row['sections'][:100])
    print("Text: " + row['text'][:300])
    print('Openai topic labels: ' + str(row.get('openai_topic_labels', 'No openai geo labels')))
    print('Wide string: ' +  str(wide_string))
    print('Narrow string: ' +  str(narrow_string))
    print('\n')
    print("Geocoding label: " + openai_geo_label)    
    

    if wide_string and narrow_string:
        wide_and_narrow_string = openai_geo_label +", "+narrow_string+", " + wide_string +  ", UK" 
        wide_and_narrow_geocoded_results = geocode_string(wide_and_narrow_string, geom, row)
        for d in wide_and_narrow_geocoded_results: d['geocode_strategy'] = 'wide_and_narrow'
    else:
        wide_and_narrow_geocoded_results = []

    if narrow_string:
        only_narrow_string = openai_geo_label +", "+narrow_string +  ", UK" 
        only_narrow_geocoded_results = geocode_string(only_narrow_string, geom, row)
        for d in only_narrow_geocoded_results: d['geocode_strategy'] = 'narrow'
        
    else:
        only_narrow_geocoded_results = []

    if wide_string:
        wide_string = openai_geo_label +", "+wide_string +  ", UK" 
        wide_geocoded_results = geocode_string(wide_string, geom, row)
        for d in wide_geocoded_results: d['geocode_strategy'] = 'wide'
    else:
        wide_geocoded_results = []

    geocoded_results = (wide_and_narrow_geocoded_results or []) + (only_narrow_geocoded_results or []) + (wide_geocoded_results or [])
    
    if len(geocoded_results)==0:
        print("*** Geocoding failed ***")
        null_result = [{  
                'geocode_success': False,
                'chunk_id': row['chunk_id'],
                'openai_geo_label': row['openai_geo_label'],
                'formatted_address': None,
                'api_result_rank': None,
                'google_place_id': None,
                'geocode_string': None,
                'geom': None,
                'distance_from_document_geom': None,
                'bounding_box': None,
                'bounding_box_area': None,
                'document_geom_type': None,
                'types':None,
                'raw_result': None,
            }]         
        

        print("returning null result")
        return null_result
    
    
    print("number of results: " + str(len(geocoded_results)))
    
    ranked_geocoded_results = rank_geocoded_results(geocoded_results, wide_string, narrow_string)[:1]
    
    # remove raw_result from each candidate for printing to screen to make it more readable
    ranked_geocoded_results_without_raw = [
        {k: v for k, v in ranked_geocoded_result.items() if k != 'raw_result'}
        for ranked_geocoded_result in ranked_geocoded_results
    ]    

    print("Geocoding: ")
    pprint.pprint(ranked_geocoded_results_without_raw)

    return ranked_geocoded_results


def geocode_string(string, geom, row):

    try:
        
        gmaps = googlemaps.Client(key=os.getenv('GOOGLEMAPS_API_KEY'))
        geocode_results = gmaps.geocode(string)
        
        formatted_results = []

        
        
        for index, result in enumerate(geocode_results, start=1):
            point = Point(result['geometry']['location']['lng'], result['geometry']['location']['lat'])
            distance_from_document_geom = wgs84_distance_to_kilometers(point, geom)
            bounding_box =  extract_bounding_box_polygon(result['geometry'])
            bounding_box_area = get_area_of_bounding_box(bounding_box)   

            if geom.geom_type == 'Point':
                document_geom_type = "Point"
            else:
                document_geom_type = "Polygon"

            formatted_results.append({
                'geocode_success': True,
                'chunk_id': row['chunk_id'],
                'openai_geo_label': row['openai_geo_label'],
                'formatted_address': result['formatted_address'],
                'api_result_rank': index,
                'google_place_id': result['place_id'],
                'geocode_string': string,
                'geom': point,
                'distance_from_document_geom': round(distance_from_document_geom, 3),
                'bounding_box': bounding_box,
                'bounding_box_area': bounding_box_area,
                'document_geom_type': document_geom_type,
                'types':result['types'],
                'raw_result': result,
            })

        return formatted_results
        
    except Exception as e:
        print(f"Error geocoding string '{string}': {e}")
        return None

def dedupe_by_google_place_id(candidates):
    seen_ids = set()
    deduplicated_list = []
    
    for candidate in candidates:
        google_place_id = candidate.get('google_place_id')
        if google_place_id not in seen_ids:
            seen_ids.add(google_place_id)
            deduplicated_list.append(candidate)
    
    return deduplicated_list        

def rank_geocoded_results(geocoded_results, wide_string, narrow_string):

    gmaps = googlemaps.Client(key=os.getenv('GOOGLEMAPS_API_KEY'))
    exclude_results = gmaps.geocode(f"{narrow_string}, {wide_string}, UK")
    exclude_place_id = exclude_results[0]['place_id']

    pprint.pprint(geocoded_results)

    print("exlcude place id: " + exclude_place_id)

    for result in geocoded_results[:]:
        if result['google_place_id'] == exclude_place_id:
            print("Removing result with place id: " + result['google_place_id'])
            geocoded_results.remove(result)
    
    # this to do for later... 

    # return top wide_and_narrow_geocoded_result if there is a perfect string match 

    # return wide_and_narrow_geocoded_results if there are multiple wide matches

    # return wide_geocoded_results if there is only one wide match and its a better string match that wide_and_narrow_geocoded_result

    # if all of the above fail, return the top ranked geocoded result for whole uk, if there is only one result 


    return geocoded_results


def get_geometry(row):
    geom = None
    
    if row['geom']:
        try:
            # Convert hex string to binary and load as WKB
            binary = binascii.unhexlify(row['geom'])
            geom = wkb.loads(binary)
        except Exception as e:
            print(f"Error converting geometry: {e}")
            print(f"Raw geometry: {row['geom'][:100]}...")
            geom = None
    
    if not geom and row['geom_center_point']:
        try:
            # Convert hex string to binary and load as WKB
            binary = binascii.unhexlify(row['geom_center_point'])
            geom = wkb.loads(binary)
        except Exception as e:
            print(f"Error converting geometry: {e}")
            print(f"Raw geometry: {row['geom_center_point'][:100]}...")
            geom = None
    
    return geom



def wgs84_distance_to_kilometers(geometry1, geometry2):
    """
    Calculate the distance between two geometries in WGS84 using the Haversine formula.
    Handles Point-to-Polygon, Polygon-to-Point, and Point-to-Point cases.

    Args:
        geometry1 (shapely.geometry.Point or shapely.geometry.Polygon): First geometry.
        geometry2 (shapely.geometry.Point or shapely.geometry.Polygon): Second geometry.

    Returns:
        float: Distance between the two geometries in kilometers.
                 Returns 0 if the point is inside the polygon.
    """
    # Check if point is inside the polygon
    if isinstance(geometry1, Point) and isinstance(geometry2, Polygon) and geometry2.contains(geometry1):
        return 0.0
    if isinstance(geometry2, Point) and isinstance(geometry1, Polygon) and geometry1.contains(geometry2):
        return 0.0

    # Find the nearest points on the geometries
    if isinstance(geometry1, Polygon):
        point1 = geometry1.exterior.interpolate(geometry1.exterior.project(Point(geometry2.x, geometry2.y)))
    else:
        point1 = geometry1

    if isinstance(geometry2, Polygon):
        point2 = geometry2.exterior.interpolate(geometry2.exterior.project(Point(geometry1.x, geometry1.y)))
    else:
        point2 = geometry2

    # Calculate the Haversine distance between the two points
    lon1, lat1 = point1.x, point1.y
    lon2, lat2 = point2.x, point2.y

    return haversine(lon1, lat1, lon2, lat2)

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points
    on the Earth (specified in decimal degrees).

    Args:
        lon1, lat1: Longitude and latitude of point 1.
        lon2, lat2: Longitude and latitude of point 2.

    Returns:
        Distance in kilometers.
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a)) 
    r = 6371.0  # Radius of Earth in kilometers
    return c * r    


def extract_bounding_box_polygon(geometry_data, box_type='bounds'):
    """
    Extracts a bounding box from Google Maps Geocoding API response and converts it to a Shapely Polygon.

    Args:
        geometry_data (dict): The 'geometry' field from the Google Maps Geocoding API response.
        box_type (str): Either 'viewport' or 'bounds' to specify the type of bounding box to extract.

    Returns:
        Polygon: A Shapely Polygon object representing the bounding box, or None if the box is not available.
    """
    try:
        # Get the desired bounding box
        bounding_box = geometry_data.get(box_type)
        
        # If bounding box doesn't exist, return None
        if not bounding_box:
            print("*** Bounding box not found ***")
            return None
        
        # Extract coordinates
        northeast = bounding_box['northeast']
        southwest = bounding_box['southwest']
        
        # Define the corner points of the bounding box
        coordinates = [
            (southwest['lng'], southwest['lat']),  # Bottom-left
            (northeast['lng'], southwest['lat']),  # Bottom-right
            (northeast['lng'], northeast['lat']),  # Top-right
            (southwest['lng'], northeast['lat']),  # Top-left
            (southwest['lng'], southwest['lat'])   # Close the polygon
        ]
        
        # Create and return a Shapely Polygon
        return Polygon(coordinates)
    except KeyError as e:
        raise ValueError(f"Invalid geometry data format. Missing key: {e}")

def get_area_of_bounding_box(bounding_box):

    if not bounding_box:
        return None
    
    """
    Calculate the approximate area of a bounding box in square kilometers.
    Uses WGS84 distances to account for the Earth's curvature.

    Args:
        bounding_box (shapely.geometry.Polygon): The bounding box polygon

    Returns:
        float: Area of the bounding box in square kilometers
    """
    # Get the coordinates of the bounding box
    minx, miny, maxx, maxy = bounding_box.bounds
    
    # Create points for the width and height calculations
    southwest = Point(minx, miny)
    southeast = Point(maxx, miny)
    northwest = Point(minx, maxy)
    
    # Calculate width and height using WGS84 distances
    width = wgs84_distance_to_kilometers(southwest, southeast)
    height = wgs84_distance_to_kilometers(southwest, northwest)
    
    # Return the area
    return round(width * height, 5)
    