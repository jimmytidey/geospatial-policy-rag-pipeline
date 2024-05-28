# Data analysis for local plans

## Running Locally

`python -m venv venv`

`pip install -r requirements.txt`

`python app.py` will run the Flask server locally

When chunking, two algorithms are used for completeness.

To see the last chunked PDF, as chunked by Llama Sherpa:
http://127.0.0.1:5000/sherpa/

To see the last chunked PDF, as chunked by PyMuPDF:
http://127.0.0.1:5000/pymupdf/

To interact with the RAG enpoint:
http://127.0.0.1:5000/rag?topic=climate change (where topic parameter is of your choosing)

## Setting up the postgres DB

make sure you set dimensionality of the embedding column
ALTER TABLE langchain_pg_embedding
DROP COLUMN embedding;

ALTER TABLE langchain_pg_embedding
ADD COLUMN embedding VECTOR(1536);

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

# Deploying

Set heroku env variables from env file

# Google API auth

Steps to Set ADC on Heroku

Service Account Key:

Create a service account in your Google Cloud project.
Download a JSON key file for this service account.
Heroku Configuration:

Open your Heroku app's dashboard.
Navigate to "Settings" and then "Config Vars".
Add the following config vars:
GOOGLE_CREDENTIALS: Paste the entire contents of the JSON key file here.
GOOGLE_APPLICATION_CREDENTIALS: Set this to /app/google-credentials.json.
Profile Script:

Create a file named .profile in the root directory of your project.
Add this line to the file:
