# SurrealDB Vector Search Example using Surreal Deal Dataset

This is a step by step tutorial to implement Vector Search using SurrealDB. 

Vector search allows for similarity-based queries on high-dimensional data, which is particularly useful for applications like semantic search, recommendation systems, and more.

## Prerequisites

- [SurrealDB installed](https://surrealdb.com/install) and running
- Ollama installed with the [nomic-embed-text model](https://ollama.com/library/nomic-embed-text)
- Import [Surreal Deal dataset](https://surrealdb.com/docs/surrealdb/surrealql/demo).

## Setup

Import the dataset that includes vector embeddings for products.
The dataset already includes the vector index and embeddings for the fields product name, product_details and review. 
For this example we will only be using the product details embeddings. 

The product embeddings will be stored in the `details_embedding` field.
```sql
DEFINE FIELD details_embedding
    ON TABLE product 
    TYPE array<decimal>;
```
The vector index `idx_product_details_embedding` uses the MTREE algorithm with 768 dimensions and cosine distance for similarity calculations.
```sql
DEFINE INDEX idx_product_details_embedding ON product 
    FIELDS details_embedding 
    MTREE DIMENSION 768 DIST COSINE;
```

## Usage

Generate query embeddings
This uses the Ollama API to generate embeddings for the query text.

```sql
LET $query_text = "baggy clothes"; 
LET $query_embeddings = select * from http::post('http://localhost:11434/api/embeddings', {
  "model": "nomic-embed-text",
  "prompt": $query_text
}).embedding;
```


Perform a vector similarity search:

```sql
SELECT
id,
name,
category,
sub_category,
price,
vector::similarity::cosine(details_embedding,$query_embeddings) AS similarity
FROM product
ORDER BY similarity DESC
LIMIT 3;
```

This query calculates the cosine similarity between the query embeddings and the product embeddings, then returns the top 2 most similar products.

```json
[
	{
		category: 'Men',
		id: product:01GBDKYEAG93XBKM07CFH1S9S6,
		name: "Men's Slammer Heavy Hoodie",
		price: 65,
		similarity: 0.5410314334339928f,
		sub_category: 'Shirts & Tops'
	},
	{
		category: 'Men',
		id: product:01GADYP46G8GN8YBPYTWGKYVB9,
		name: "Men's Locker Heavy Zip-Through Hoodie",
		price: 70,
		similarity: 0.5395832679844547f,
		sub_category: 'Shirts & Tops'
	}
]
```
