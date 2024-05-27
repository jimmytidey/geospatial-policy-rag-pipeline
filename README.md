# Data analysis for local plans

## Running Locally

python -m venv venv

## Setting up the postgres DB

-- !!!! Installing the vector extension took nearly two hours.  
-- !!!! It would probably be best to run it from Heroku dataclips
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS text_fragments (
id SERIAL PRIMARY KEY,
metadata JSONB,
vector VECTOR(384),
plain_text TEXT,
full_text tsvector,
hash TEXT,
filename TEXT

);

-- Create a text search configuration for English
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS english_simple_config ( COPY = simple );

ALTER TEXT SEARCH CONFIGURATION english_simple_config
ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, word, hword, hword_part
WITH english_stem;

-- Alter the text column to use the English full-text search configuration
ALTER TABLE text_fragments
ALTER COLUMN full_text
SET DATA TYPE tsvector
USING to_tsvector('english_simple_config', text);

-- Create an index on the tsvector column for faster full-text searches
CREATE INDEX IF NOT EXISTS text_tsvector_index
ON text_fragments
USING gin(full_text);

# Making Llama Sherpa work

https://stackoverflow.com/questions/51925384/unable-to-get-local-issuer-certificate-when-using-requests
Run Install Certificates.command in your MacOS finder (weird one... )

possibly required during initialisation:
try:
\_create_unverified_https_context = ssl.\_create_unverified_context
except AttributeError:
pass
else:
ssl.\_create_default_https_context = \_create_unverified_https_context

nltk.download('punkt')
