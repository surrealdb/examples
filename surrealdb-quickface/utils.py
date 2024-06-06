import sys
import cv2
import requests
import os
from keras_facenet import FaceNet

embedder = FaceNet()

# Extract the embedding for the largest face detected in the image
def detect_face(filepath):
    image = cv2.imread(filepath)
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    detections = embedder.extract(image, threshold=0.95)
    sys.stdout = original_stdout
    largest = find_largest_face(detections)
    if largest:
        return largest['embedding']

# Fine the largest face in the provided detected faces. 
def find_largest_face(detections):
    if not detections:
        return None
    largest_area = 0
    largest_detection = None
    for detection in detections:
        box = detection['box']
        area = box[2] * box[3]  # width * height
        if area > largest_area:
            largest_area = area
            largest_detection = detection
    return largest_detection

def surreal_session():
    s = requests.Session()
    s.auth = ('root', 'pass')
    s.headers.update({"Accept": "application/json"})
    return s

session = surreal_session()

# Execute a SurrealQL statement
def surreal_query(query):
    result = session.post('http://127.0.0.1:8000/sql', data=query)
    # Check the HTTP status is valid
    if result.status_code != 200:
        raise RuntimeError(result.text)
    results = result.json()
    # Check the SurrealDB results are OK
    for res in results:
        if res.get('status') != 'OK':
            raise RuntimeError(res)
    return results
