# Local Plans Geospatial RAG prototype

View this code running: https://localplans-ai-map-61938e5fe7bf.herokuapp.com

This project explores using AI to process and combine policy documents that refer to specific locations (locations, buildings, parks, etc). The goal is to decompose a corpus of policy documents into the locations they are talking about, then recombine what each policy document says about a locattion into a summaries per location of all the policies that apply.

It uses planning policy in England as an example, a topic where its easy to find lots of publicly available policy documents.

Planning in England is guided by the The National Planning Policy Framework - the national guide to built environment policy.

Local PLans are the key document that guides built environment policy in Local Authorities. Local Plans follow the guidances in the NPPF.

In turn, Neighbourhood Plans are informed by Local Plans, and are for smaller areas within Local Authorities.

This prototype investigates building a RAG that has features to support:

- Hierarchical sets of policy documents (NPPF->Local Plans->Neighbourhood Plans)
- Documents with geospatial inforation - policys about locations and areas.

# Structure

- This repo is the data processing pipeline
- Frontend: https://github.com/jimmytidey/geospatial-policy-rag-frontend
- API: https://github.com/jimmytidey/geospatial-policy-rag-api

## DB Architecture

There are four important tables:

- langchain_pg_embedding - which contains embeddings, and topic lables and geo-labels
- geo_boundaries - which has geographic boundaries for each document
- text_chunks - which is my nicer to query than langchain_pg_embedding, but contains the same information
- locations - whcih is a list of every geolocated location, plus the text it was located from. A sinlge location may have multiple rows, if it is mentioned in multiple places

## Steps of the pipeline

- add the pdfs (add_pdfs.ipynb), which adds to the document details to the documents table, and adds chunks to the langchain_pg_embedding table
- add a geo_boundary if required
- run the topic coding (1_add_topic_lables/topic_labels_run.ipynb)
- run the geocoding (2_add_geo_lables/geo_lables_run.ipynb)
- run the migration to text_chunks
-

## Running Locally

`python -m venv venv` - set the virtual environment up

`pip install -r requirements.txt` - install pip packages

`python app.py` - will run the Flask server locally

When chunking, two algorithms are used for completeness.

## Setting up the postgres DB

make sure you set dimensionality of the embedding column
ALTER TABLE langchain_pg_embedding
DROP COLUMN embedding;

ALTER TABLE langchain_pg_embedding
ADD COLUMN embedding VECTOR(1536);

# Installing Llama Sherpa local server

This parses the documents. You must have the docker app running.

Download docker image: ghcr.io/nlmatics/nlm-ingestor:latest

docker run -p 5010:5001 ghcr.io/nlmatics/nlm-ingestor:latest

# Deploying

This is really intended to run locally

# Making Llama Sherpa work externally (no longer works I think)

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
