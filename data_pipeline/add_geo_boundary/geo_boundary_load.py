import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 

def link_document_to_geo_boundary(document_id, geo_boundary_id):
    pg = Postgres()
    ensure_geo_boundary_tables_exist()

    """
    Links a document to a geo_boundary by updating the geo_boundary_id in the documents table.

    Args:
        document_id (str): The ID of the document.
        geo_boundary_id (int): The ID of the geo boundary.
    """
    # SQL query to update the geo_boundary_id in the documents table
    update_query = """
    UPDATE documents
    SET geo_boundary_id = %s
    WHERE document_id = %s;
    """
    
    # Parameters for the query
    values = (geo_boundary_id, document_id)
    
    try:
        # Execute the query
        pg.insert(update_query, values)  # Assuming `pg.update` is the method to execute UPDATE queries
        print(f"Successfully linked document_id: {document_id} to geo_boundary_id: {geo_boundary_id}.")
    except Exception as e:
        print(f"Error linking document_id: {document_id} to geo_boundary_id: {geo_boundary_id}: {e}")


def add_geo_boundary(document_id, geo_boundary_name, geometry_json):
    pg = Postgres()
    ensure_geo_boundary_tables_exist()

    #check this name doesn't already exist 
    results = pg.query("SELECT * FROM geo_boundaries WHERE name = %s", (geo_boundary_name,))
    if results:
        print(f"Geo boundary with name '{geo_boundary_name}' already exists.")
        return

    
    insert_query = """
    INSERT INTO geo_boundaries (name, geom)
    VALUES (%s, ST_GeomFromGeoJSON(%s, 4324))
    """
    pg.insert(insert_query, (geo_boundary_name, geometry_json))
    result = pg.query("SELECT * FROM geo_boundaries WHERE name = %s", (geo_boundary_name,))
    geo_boundary_id = result[0]['geo_boundary_id']
    link_document_to_geo_boundary(document_id, geo_boundary_id)

def ensure_geo_boundary_tables_exist(): 

    pg = Postgres()
    junction_table_query= """
        CREATE TABLE IF NOT EXISTS document_geo_boundary (
        document_id TEXT REFERENCES documents(document_id) ON DELETE CASCADE, -- References TEXT document_id
        geo_boundary_id INT REFERENCES geo_boundaries(geo_boundary_id) ON DELETE CASCADE, -- References geo_boundaries
        PRIMARY KEY (document_id, geo_boundary_id) -- Ensures unique pairings
    );"""

    pg.insert(junction_table_query)

    create_documents_table_query = """
        CREATE EXTENSION IF NOT EXISTS postgis;
        CREATE TABLE IF NOT EXISTS geo_boundaries (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            properties JSONB,
            geom GEOMETRY(Geometry, 4326)
        );
    """
    pg.insert(create_documents_table_query)
