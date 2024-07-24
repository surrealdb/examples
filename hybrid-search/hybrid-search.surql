DEFINE FUNCTION fn::hybrid_search($query_text: string, $match_count: int, $full_text_weight: float, $semantic_weight: float, $rrf_k: int) {
    LET $query_embeddings = return http::post('http://localhost:11434/api/embeddings', {
        "model": "nomic-embed-text",
        "prompt": $query_text
    }).embedding; 

    LET $full_text_results = (
        SELECT id, details, search::score(1) AS relevance
        FROM product
        WHERE details @1@ $query_text
        ORDER BY relevance DESC
        LIMIT $match_count * 2
    );

    LET $semantic_results = (
        SELECT id, vector::similarity::cosine(details_embedding, $query_embeddings) as similarity
        FROM product
        ORDER BY similarity DESC
        LIMIT $match_count * 2
    );

    RETURN (
        SELECT 
            id,
            name,
            details,
            (($full_text_weight * (1.0 / ($rrf_k + ((array::find_index($full_text_results.id, id) ?? $match_count * 2) + 1)))) + 
             ($semantic_weight * (1.0 / ($rrf_k + ((array::find_index($semantic_results.id, id) ?? $match_count * 2) + 1))))) 
            AS combined_score
        FROM product
        WHERE id IN $full_text_results.id OR id IN $semantic_results.id
        ORDER BY combined_score DESC
        LIMIT $match_count
    );
};
SELECT * FROM fn::hybrid_search('Versatile fitted jacket with pockets', 10, 0.5f, 0.5f, 60);
