import os,sys
import pytest
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 
from helpers import chunk_pdf

pg=Postgres()
load_dotenv()
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

# Sample metadata and URL
url = "https://www.leeds.gov.uk/Local%20Plans/Site%20Allocations%20Plan/12%20Outer%20West%20HMCA%202024.pdf"
metadata = {
    "category": "test_category",
    "sub_category": "test_sub_category",
    "lpa": "test_lpa",
    "council type": "test_council_type",
    "title": "test_title",
    "start_year": "2014",
    "end_year": "2033",
    "url": url,
}

file_name = metadata["category"] + "-" + metadata["sub_category"] + "-" + metadata["lpa"] + ".pdf"
metadata["file"] = file_name

def test_chunk_pdf_and_row_count():
    # Step 1: Run chunk_pdf function
    chunk_pdf(url, file_name, metadata)

    # Step 2: Query langchain_pg_embedding to check the row count
    row_count_query = "SELECT COUNT(*) FROM langchain_pg_embedding;"
    row_count_result = pg.query(row_count_query)
    row_count = row_count_result[0][0] if row_count_result else 0

    # Assert there are more than 400 rows in the table
    assert row_count > 400, f"Expected more than 400 rows, but found {row_count}."

    # Step 3: Empty langchain_pg_embedding table
    delete_query = """
    DO $$
    BEGIN
        IF (SELECT COUNT(*) FROM langchain_pg_embedding) < 500 THEN
            DELETE FROM langchain_pg_embedding;
        END IF;
    END $$;
    """
    pg.query(delete_query)

   
