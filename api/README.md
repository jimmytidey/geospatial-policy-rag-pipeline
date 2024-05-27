# Data analysis for local plans

## Running Locally

CD API (if you are not already in the API folder)

python -m venv venv

pip install -r requirements.txt

To run notebooks in visual studio, you will have to open a new window in the API folder.

VS Code cannot find venv files outside the root

`python app.py` will run the Flask server locally

When chunking, two algorithms are used for completeness.

To see the last chunked PDF, as chunked by Llama Sherpa:
http://127.0.0.1:5000/sherpa/

To see the last chunked PDF, as chunked by PyMuPDF:
http://127.0.0.1:5000/pymupdf/

To interact with the RAG enpoint:
http://127.0.0.1:5000/rag?topic=climate change (where topic parameter is of your choosing)

## Setting up the postgres DB

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
