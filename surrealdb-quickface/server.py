import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import logging
from utils import surreal_query, detect_face, surreal_session

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Set up logging
logging.basicConfig(level=logging.DEBUG)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture')
def capture():
    return render_template('capture.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'photo' not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files['photo']
    if file.filename == '':
        return jsonify(error="No selected file"), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logging.debug(f"Saving file to {filepath}")
        file.save(filepath)

        # Extract the face embedding for this photo:
        embedding = detect_face(filepath)

        # If there is a face detected, search for the best matching user in SurrealDB
        if embedding is not None:
            result = surreal_query(f"USE NS test; USE DB test; SELECT name,role,dep FROM users WHERE r <|1,EUCLIDEAN|> {embedding.tolist()};")
            logging.debug(result)
            result = result[2]['result'][0] 
        else:
            result = {}
        
        # Clean up the uploaded file
        try:
            os.remove(filepath)  
            logging.debug(f"Removed file {filepath}")
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")

        return jsonify(result)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(host='0.0.0.0', port=5001, debug=True)
