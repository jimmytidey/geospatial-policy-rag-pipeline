from flask import Flask, request
from flask_cors import CORS, cross_origin
import pandas as pd
import os 
from rag import rag_query

app = Flask(__name__)

CORS(app, support_credentials=True)

@app.route('/sherpa/')
def sherpa_chunks():
    csv_file_path = os.path.join('files', 'sherpa_chunks.csv')
    df = pd.read_csv(csv_file_path)
    df_filled = df.fillna('???')

    html = "<div style=' width: 600px;'>"
    for index, row in df_filled.iterrows():
        html += f"<h3> {row['sections']} </h3>"
        html += f"<p> {row['text']} </p>"
        html += f"<p><em>Page {row['page']} </em>, {row['notes']}, {row['coalesced_with']} </p> "
    
    html +="</div>"
    return html 

@app.route('/rag', methods=['GET'])
def rag():
    topic = request.args.get('topic')
    if topic is None:
        return "Please provide a topic"

    [prompt, response, links] = rag_query(topic)

    prompt = prompt.replace('\n', '<br/>')
    response = response.content.replace('\n', '<br/>')
    
    html = "<div style=' width: 600px;'>"
    html += "<h1> Response </h1>"
    html += f"<p> {response} </p>"
    html += "<h2> Links </h2>"
    html += links    
    html += "<h1> prompt </h1>"
    html += f"<p> {prompt} </p>"

    html +="</div>"
    return html 

@app.route('/api/rag', methods=['GET'])
def api_rag():
    topic = request.args.get('topic')
    if topic is None:
        return "Please provide a topic"

    [prompt, response, links] = rag_query(topic)

    prompt = prompt.replace('\n', '<br/>')
    response = response.content.replace('\n', '<br/>')
    
    html = "<h1> Response </h1>"
    html += f"<p> {response} </p>"
    html += "<h2> Links </h2>"
    html += links    

    return html 

@app.route('/pymupdf/')
def unstructured_chunks():
    csv_file_path = os.path.join('files', 'pymupdf_chunks.csv')

    df = pd.read_csv(csv_file_path)
    df_filled = df.fillna('???')

    html = "<div style='width=600px'>"
    for index, row in df_filled.iterrows():
        html += f"<h3> {row['page']} </h3>"
        html += f"<p> {row['context_text']} </p>"
    
    html +="</div>"
    return html 


if __name__ == '__main__':
    app.run()