
import requests
import json
from postgres import Postgres
import geojson 

pg = Postgres()

def geo_boundary_extract_from_url(url):
# Fetch GeoJSON data from URL
    response = requests.get(url)
    geojson_data = response.json()
    geometry_json = json.dumps(geojson_data)  # Convert the dictionary to a JSON string
    return geometry_json


def geo_boundary_extract_from_file(file_path):
    pg = Postgres()  # Create a new database connection
    # Read the GeoJSON file
    with open(file_path) as f:
        geojson_data = open(file_path).read()
    
    # Prepare the insert statement
    insert_query = """
        INSERT INTO geo_boundaries (name, properties, geom)
        VALUES (%s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
    """

    # Load or parse your GeoJSON data
    data = geojson.loads(geojson_data)  # or geojson.load() if reading from a file

    # Check if data is a FeatureCollection, which contains 'features'
    if isinstance(data, geojson.FeatureCollection):
        for feature in data.features:
            name = feature.get('properties', {}).get('Name', 'Unnamed')
            properties = feature.get('properties', {})
            geometry = geojson.dumps(feature.geometry)  # Convert geometry to GeoJSON string

            # Execute the insert statement with parameters
            pg.insert(insert_query, (name, json.dumps(properties), geometry))

    # Check if data is a single Feature
    elif isinstance(data, geojson.Feature):
        name = data.get('properties', {}).get('Name', 'Unnamed')
        properties = data.get('properties', {})
        geometry = geojson.dumps(data.geometry)  # Convert geometry to GeoJSON string

        # Execute the insert statement with parameters
        pg.insert(insert_query, (name, json.dumps(properties), geometry))

    # Check if data is a bare Geometry (Point, LineString, etc.)
    elif isinstance(data, (geojson.Point, geojson.LineString, geojson.Polygon,
                        geojson.MultiPoint, geojson.MultiLineString, geojson.MultiPolygon)):
        name = 'Unnamed'
        properties = {}  # No properties available for bare geometries
        geometry = geojson.dumps(data)  # Convert the geometry to a GeoJSON string

        # Execute the insert statement with parameters
        pg.insert(insert_query, (name, json.dumps(properties), geometry))
