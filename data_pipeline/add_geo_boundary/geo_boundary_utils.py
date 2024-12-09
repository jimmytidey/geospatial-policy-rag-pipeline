import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 
import pandas as pd

def get_info(): 

    pg = Postgres()
    # Query to fetch documents without geo-boundaries
    documents_without_geo_boundaries_query = """
    SELECT d.title, d.document_id
    FROM documents d
    LEFT JOIN document_geo_boundary dgb ON d.document_id = dgb.document_id
    WHERE dgb.document_id IS NULL
    ORDER BY d.title;
    """

    # Query to fetch all geo-boundaries
    all_geo_boundaries_query = """
    SELECT name, geo_boundary_id  FROM geo_boundaries ORDER BY name;
    """

    # Run the queries and fetch the results
    try:
        # Fetch documents without geo-boundaries
        documents_without_geo_boundaries = pg.query(documents_without_geo_boundaries_query)
        
        # Fetch all geo-boundaries
        all_geo_boundaries = pg.query(all_geo_boundaries_query)

        # Convert results to pandas DataFrames
        documents_df = pd.DataFrame(documents_without_geo_boundaries)
        geo_boundaries_df = pd.DataFrame(all_geo_boundaries)
        pd.set_option('display.max_colwidth', None)
        # Display the DataFrames
        print("Documents Without Geo Boundaries:")
        display(documents_df)  # Use Jupyter's display for nice table formatting
        
        print("\nAll Geo Boundaries:")
        display(geo_boundaries_df)  # Use Jupyter's display for nice table formatting

    except Exception as e:
        print(f"An error occurred: {e}")