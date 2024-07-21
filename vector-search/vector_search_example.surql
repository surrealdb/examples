LET $query_text = "baggy clothes"; 

LET $query_embeddings = select * from http::post('http://localhost:11434/api/embeddings', {
  "model": "nomic-embed-text",
  "prompt": $query_text
}).embedding;

SELECT id, name, category, sub_category, price, vector::similarity::cosine(details_embedding, $query_embeddings) AS similarity FROM product ORDER BY similarity DESC LIMIT 3;
