import re
import sqlite3

def clean_and_tokenize(text: str) -> set:
    """Cleans a string by removing punctuation and spliting it into lowercased tokens."""
    # Convert to lowercase and strip non-alphanumeric chars
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    # Return a set of unique words of length > 2
    return {word for word in cleaned.split() if len(word) > 2}

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Computes Jaccard Similarity between two sets of tokens."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / union

def find_cluster_for_question(conn, question_text: str, category: str) -> tuple:
    """
    Simulates the Stage 2 Deduplication & Clustering AI.
    It performs a token-overlap similarity search against existing representative questions.
    
    Returns:
        tuple: (cluster_id, similarity_score)
    """
    cursor = conn.cursor()
    
    # 1. Tokenize the new question
    new_tokens = clean_and_tokenize(question_text)
    if not new_tokens:
        return None, 0.0

    # 2. Retrieve all active clusters and their representative question text
    cursor.execute("""
        SELECT c.id AS cluster_id, q.question_text, q.category
        FROM clusters c
        JOIN questions q ON q.id = c.representative_question_id
        WHERE q.category = ?;
    """, (category,))
    
    existing_clusters = cursor.fetchall()
    
    best_cluster_id = None
    best_similarity = 0.0

    # 3. Compute Jaccard Similarity
    for cluster in existing_clusters:
        rep_text = cluster['question_text']
        rep_tokens = clean_and_tokenize(rep_text)
        
        sim = jaccard_similarity(new_tokens, rep_tokens)
        
        # High token overlap counts as a match
        if sim > best_similarity:
            best_similarity = sim
            best_cluster_id = cluster['cluster_id']

    # 4. Check against deduplication threshold
    # Since Jaccard overlap is stricter than dense embeddings, we use 0.35 as a matching threshold.
    # If Nekha/Tejeswara implement sentence-transformers, they will change this to dense Cosine Similarity > 0.85
    MATCH_THRESHOLD = 0.35
    
    if best_similarity >= MATCH_THRESHOLD:
        return best_cluster_id, best_similarity
    
    return None, 0.0
