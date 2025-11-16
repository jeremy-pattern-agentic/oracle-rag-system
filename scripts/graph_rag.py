from transformers import pipeline
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection
import re

# Initialize connections
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
milvus_collection = Collection("entities")  # Assumes pre-created collection
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Transformers pipelines
ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
relation_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Function to add entity to Neo4j
def add_entity(tx, name, entity_type, embedding):
    tx.run(
        "MERGE (e:Entity {name: $name}) "
        "SET e.type = $type, e.embedding = $embedding",
        name=name, type=entity_type, embedding=embedding.tolist()
    )

# Function to add relationship to Neo4j
def add_relationship(tx, ent1, rel, ent2):
    tx.run(
        "MATCH (a:Entity {name: $ent1}), (b:Entity {name: $ent2}) "
        "MERGE (a)-[r:RELATION {type: $rel}]->(b)",
        ent1=ent1, rel=rel, ent2=ent2
    )

# Function to chunk text (simple example)
def chunk_text(text, max_length=512):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current_chunk, current_length = [], [], 0
    for sentence in sentences:
        length = len(sentence.split())
        if current_length + length > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk, current_length = [sentence], length
        else:
            current_chunk.append(sentence)
            current_length += length
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# Main function to process text and populate graph
def populate_graph(text):
    chunks = chunk_text(text)
    for chunk in chunks:
        # Extract entities
        entities = ner_pipeline(chunk)
        entity_list = []
        for ent in entities:
            if ent['score'] > 0.7:  # Confidence threshold
                name = ent['word'].strip('##')
                entity_type = ent['entity'].split('-')[-1]  # e.g., B-PER -> PER
                embedding = embedder.encode(name)
                entity_list.append((name, entity_type, embedding))
                
                # Add to Neo4j
                with driver.session() as session:
                    session.write_transaction(add_entity, name, entity_type, embedding)
                
                # Add to Milvus
                milvus_collection.insert([[name], [embedding.tolist()], [entity_type]])

        # Infer relationships (simple pairwise check)
        for i, (ent1, type1, _) in enumerate(entity_list):
            for j, (ent2, type2, _) in enumerate(entity_list[i+1:], i+1):
                if type1 != type2:  # Avoid same-type relations
                    # Example: check for "works for" or "located in"
                    candidate_rels = ["WORKS_FOR", "LOCATED_IN", "NONE"]
                    context = f"{ent1} {ent2} {chunk[:50]}"
                    result = relation_classifier(context, candidate_rels, multi_label=False)
                    rel = result['labels'][0]
                    if rel != "NONE" and result['scores'][0] > 0.6:
                        with driver.session() as session:
                            session.write_transaction(add_relationship, ent1, rel, ent2)

# Example usage
sample_text = """
Elon Musk is the CEO of Tesla. Tesla is based in California. 
Musk also founded SpaceX, which works on rocket technology.
"""
populate_graph(sample_text)

# Clean up
driver.close()
milvus_collection.release()