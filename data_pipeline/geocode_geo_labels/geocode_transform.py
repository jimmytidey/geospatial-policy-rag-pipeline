import sys,os
import googlemaps
from shapely.geometry import Point
from shapely import wkt
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def geocode_row(row):
    
    results = []
    for label in row['openai_geo_labels']:
        best_location =geolocate_label(label, row)
        results.append(best_location)
    
    return results

def geolocate_label(label, row):
    geom = get_geometry(row)

    if not geom: 
        print("No bounding polygon or center point found, skipping geocode")
        return None

    if not row['narrow_geocode_string'] and not row['wide_geocode_string']:
        print("No geocode strings found, skipping geocode")
        return None

    if row['narrow_geocode_string']:
        narrow_string = row['wide_geocode_string']+", "+row['narrow_geocode_string']+", "+label
        narrow_candidates = geocode_string(wide_narrow_string, geom)
    else:
        narrow_candidates = []

    wide_string = row['wide_geocode_string']+", "+label
    wide_candidates = geocode_string(wide_string, geom)

    candidates = narrow_candidates + wide_candidates
    best_location = pick_best_location(candidates)

    return best_location


def geocode_string(string, geom):
    gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])
    
    try:
        # Attempt to geocode the string
        geocode_results = gmaps.geocode(string)
        
        if not geocode_results:
            return None
        
        formatted_results = []

        for result in geocode_results:
            point = Point(result['geometry']['location']['lng'], result['geometry']['location']['lat'])
            distance = point.distance(geom)
            if geom.geom_type == 'Point':
                is_point = True
            else:
                is_point = False

            formatted_results.append({
                'formatted_address': result['formatted_address'],
                'location_name': string,
                'geom': point,
                'distance': distance,
                'is_point': is_point
            })

        return formatted_results
        
    except Exception as e:
        print(f"Error geocoding string '{string}': {e}")
        return None

def pick_best_location(candidates):
    return min(candidates, key=lambda x: x['distance'])

def get_geometry(row):
    if row['geom']:
        try:
            geom = wkt.loads(row['geom'])
        except Exception as e:
            print(f"Error converting geometry: {e}")
            print(f"Raw geometry: {row['geom'][:100]}...")
         
    elif row['geom_center_point']:
        try:
            geom = wkt.loads(row['geom_center_point'])
        except Exception as e:
            print(f"Error converting geometry: {e}")
            print(f"Raw geometry: {row['geom_center_point'][:100]}...")
    else:
           geom = None

    return geom

