# Face Recognition with Flask and OpenCV

This project demonstrates a face recognition application using Flask, OpenCV, and Keras FaceNet. It captures a snapshot from the laptop camera, compares it with photos stored in the data folder, and displays the recognition results.

## Features

- Start and stop the camera stream
- Capture a photo from the camera
- Perform face recognition using Keras FaceNet
- Display the recognition results

## Requirements

- Python 3.6+
- Flask (for serving static files and client-side interactions)

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/surrealdb-quickface.git
cd surrealdb-quickface
```

2. Make sure you run a SurrealDB instance

```bash
surreal start --allow-all -u root -p root -b 127.0.0.1:8000
```

3. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

4. Install the required Python packages:

```bash
pip install -r requirements.txt
```

5. Ingest data

```bash
python ingest.py
```

6. Run the app

```bash
python server.py
```

7. Open browser and point to the following url:

```bash
http://127.0.0.1:5001
```
