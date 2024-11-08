import os
import json
import geojson  # Ensure geojson library is installed
from postgres import Postgres  # Replace with your actual module name


# Step 1: Set up the geo_boundaries table if it doesn't already exist
def create_geo_boundaries_table():
    pg = Postgres()  # Create a new database connection
    create_table_query = """
        CREATE EXTENSION IF NOT EXISTS postgis;
        CREATE TABLE IF NOT EXISTS geo_boundaries (
            id SERIAL PRIMARY KEY,
            name TEXT,
            properties JSONB,
            geom GEOMETRY(Geometry, 4326)
        );
    """
    pg.insert(create_table_query)
   

# Step 2: Load a single GeoJSON file into the database
def load_geojson_file(file_path):
    pg = Postgres()  # Create a new database connection
    # Read the GeoJSON file
    with open(file_path) as f:
        geojson_data = json.load(f)
    
    # Prepare the insert statement
    insert_query = """
        INSERT INTO geo_boundaries (name, properties, geom)
        VALUES (%s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
    """
    
    # Iterate over each feature in the GeoJSON
    for feature in geojson_data['features']:
        name = feature.get('properties', {}).get('name', 'Unnamed')
        properties = feature.get('properties', {})
        geometry = json.dumps(feature['geometry'])  # Convert geometry to GeoJSON string
        
        # Execute the insert statement with parameters
        pg.insert(insert_query, (name, json.dumps(properties), geometry))
    
    

# Step 3: Loop through all GeoJSON files in the folder
def load_all_geojson_files(geo_boundaries_folder):
    # Iterate over each file in the geojson_folder
    for filename in os.listdir(geo_boundaries_folder):
        if filename.endswith(".geojson"):
            file_path = os.path.join(geo_boundaries_folder, filename)
            print(f"Loading file: {filename}")
            load_geojson_file(file_path)
    print("All GeoJSON files have been loaded into geo_boundaries.")

# Run the functions
def import_geo_boundaries(geo_boundaries_folder):
    create_geo_boundaries_table()
    load_all_geojson_files(geo_boundaries_folder)
    print("GeoJSON data loaded successfully into geo_boundaries.")
