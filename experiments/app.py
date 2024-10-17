from flask import Flask, render_template, request, redirect, url_for
import requests
from flask_cors import CORS 
import pandas as pd
import os 
from api import rag_query
from postgres import Postgres 

pg = Postgres()

app = Flask(__name__)

CORS(app, support_credentials=True)

LABELS = [
    "no_label", "broken_fragment","small_fragment", "bad_start", "truncated", "context", "green_space", "CIL", "sustainable_development", "plan_making", "decision_making", "house_building", "economy", 
    "town_centers", "communities", "transport", "communications", "land", "design", "green_belt", 
    "climate_change", "natural_environment", "historic_environment", "materials", "policy", 
      "consultation", "process", "annex",  "table_of_contents", 'education', 'sports', 'views', 'community_facilities'  
]

@app.route('/label_entries_manually', methods=['GET', 'POST'])
def label_entries_manually():
    if request.method == 'POST':
        # Handle form submission and call the /api/add_labels endpoint
        record_id = request.form['record_id']
        selected_labels = [
            request.form['label1'],
            request.form['label2'],
            request.form['label3'],
            request.form['label4']
        ]
  
        pg.add_labels_to_cmetadata(record_id, selected_labels)
  
        # Redirect back to the main page after submission
        return redirect(url_for('label_entries'))

    # Fetch 100 records where the 'labels' key is not set and 'experiment' is set to 'leeds'
    records = pg.query("""
        SELECT id, cmetadata->>'neighbourhood' as neighbourhood, cmetadata->>'block_idx' as block_idx, cmetadata->>'sections' as sections, cmetadata->>'text' as text
        FROM langchain_pg_embedding
        WHERE NOT (cmetadata ? 'labels') 
        AND cmetadata->>'experiment' = 'leeds'
        AND cmetadata->>'chunker' = 'sherpa'
        ORDER BY RANDOM()
		LIMIT 1;
    """)

    # Render the records and the form for each
    return render_template('label_entries.html', records=records, labels=LABELS)



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



@app.route('/api/add_labels', methods=['GET'])
def add_labels():
    # Get the 'id' and 'labels' query parameters
    id = request.args.get('id')
    labels = request.args.get('labels')

    # Check if 'id' and 'labels' are provided
    if not id or not labels:
        return jsonify({"error": "Missing 'id' or 'labels' parameters"}), 400

    # Split the labels string by commas to form an array
    labels_array = labels.split(',')

    # Call the 'addLabels' function
    result = addLabels(id, labels_array)




# Probably not going to use these 

@app.route('/rag', methods=['GET'])
def rag():
    topic = request.args.get('topic')
    if topic is None:
        return "Please provide a topic"

    [prompt, response, links] = rag_query(topic)

    prompt = prompt.replace('<br/>', '')
    response = response.replace('<br/>', '')
    
    html = "<div style=' width: 600px;'>"
    html += "<h1 class='govuk-heading-m'> Response </h1>"
    html += f"<p> {response} </p>"
    html += "<h2 class='govuk-heading-s'> Links </h2>"
    html += links    
    html += "<h1 class='govuk-heading-m' > prompt </h1>"
    html += f"<p> {prompt} </p>"

    html +="</div>"
    return html 



@app.route('/api/rag', methods=['GET'])
def api_rag():
    topic = request.args.get('topic')
    if topic is None:
        return "Please provide a topic"

    [prompt, response, links] = rag_query(topic)

    prompt = prompt.replace('<br/>', '')
    response = response.replace('<br/>', '')
    print(response)
    
    html = "<h1 class='govuk-heading-m'> Response </h1>"
    html += f"<p> {response} </p>"
    html += "<h2 class='govuk-heading-m'> Links </h2>"
    html += links    

    return html 

if __name__ == '__main__':
    app.run()