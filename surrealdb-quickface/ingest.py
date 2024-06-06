import os
from utils import detect_face, surreal_query

# Browse the photos directory, extract the embeddings and insert them in SurrealDB.
def index_photos():
    surreal_query("USE NS test; USE DB test; REMOVE TABLE IF EXISTS users;")
    for filename in os.listdir('data'):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            print(f"Index {filename}")
            filepath = os.path.join('data', filename)
            # Extract the embedding of the largest face
            embedding = detect_face(filepath)
            if embedding is not None:
                parts = filename[:-4].replace('_', ' ').split('-')
                name = parts[0].capitalize()
                role = parts[1].capitalize()
                dep = parts[2].capitalize()
                surreal_query(f"USE NS test; USE DB test; CREATE users SET name='{name}',role='{role}',dep='{dep}',r={embedding.tolist()}, path=\"{filename}\";")
            else:
                print(f"No face detected in '{filename}'")

if __name__ == "__main__":
    index_photos()