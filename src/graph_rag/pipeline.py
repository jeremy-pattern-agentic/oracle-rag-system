"""
Graph RAG Pipeline
Main orchestration of entity extraction and graph building
"""

from typing import Dict, List
import logging
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer

from .chunker import chunk_text
from .entity_extractor import EntityExtractor
from .relation_classifier import RelationClassifier
from .graph_storage import GraphStorage
from .vector_storage import VectorStorage

logger = logging.getLogger(__name__)


class GraphRAGPipeline:
    """
    Main Graph RAG pipeline orchestration.

    Pattern adapted from graph_rag.py lines 56-87.
    """

    def __init__(
        self,
        neo4j_config: Dict[str, any],
        milvus_config: Dict[str, any],
        collection_config: Dict[str, any],
        graph_rag_config: Dict[str, any]
    ):
        """
        Initialize Graph RAG pipeline with all components.

        Args:
            neo4j_config: Neo4j configuration
            milvus_config: Milvus configuration
            collection_config: Milvus collection configuration
            graph_rag_config: Graph RAG processing configuration
        """
        self.config = graph_rag_config

        logger.info("Initializing Graph RAG pipeline...")

        # Initialize embedding model (auto-detect GPU if available)
        logger.info(f"Loading embedding model: {graph_rag_config['embedding_model']}")
        self.embedder = SentenceTransformer(graph_rag_config['embedding_model'])

        # Initialize entity extractor
        self.entity_extractor = EntityExtractor(
            model_name=graph_rag_config['ner_model'],
            confidence_threshold=graph_rag_config['ner_confidence_threshold']
        )

        # Initialize relation classifier
        self.relation_classifier = RelationClassifier(
            model_name=graph_rag_config['relation_model'],
            candidate_relations=graph_rag_config['candidate_relations'],
            confidence_threshold=graph_rag_config['relation_confidence_threshold']
        )

        # Initialize storage backends
        self.graph_storage = GraphStorage(neo4j_config)
        self.vector_storage = VectorStorage(milvus_config, collection_config)

        logger.info("Graph RAG pipeline initialized successfully")

    def process_text(self, text: str) -> Dict[str, any]:
        """
        Full Graph RAG pipeline:
        1. Chunk text
        2. Extract entities from each chunk
        3. Generate embeddings
        4. Store in Neo4j + Milvus
        5. Classify relationships
        6. Store relationships in Neo4j

        Args:
            text: Input text to process

        Returns:
            Statistics dict with:
                - chunks_created: Number of chunks
                - entities_extracted: Total entities found
                - entities_stored_neo4j: Entities added to Neo4j
                - entities_stored_milvus: Entities added to Milvus
                - relations_found: Total relationships found
                - relations_stored: Relationships added to Neo4j
                - processing_time_seconds: Total processing time
        """
        start_time = time.time()
        stats = {
            "chunks_created": 0,
            "entities_extracted": 0,
            "entities_stored_neo4j": 0,
            "entities_stored_milvus": 0,
            "relations_found": 0,
            "relations_stored": 0,
            "processing_time_seconds": 0.0
        }

        logger.info("Starting Graph RAG text processing...")

        try:
            # Step 1: Chunk text
            chunks = chunk_text(text, max_length=self.config['chunk_max_length'])
            stats['chunks_created'] = len(chunks)
            logger.info(f"Created {len(chunks)} chunks")

            # Track all entities across chunks for relationship extraction
            all_entities: List[Dict] = []

            # Step 2-4: Process each chunk
            for chunk_idx, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {chunk_idx + 1}/{len(chunks)}")

                # Extract entities
                entities = self.entity_extractor.extract_entities(chunk)
                stats['entities_extracted'] += len(entities)
                logger.debug(f"Extracted {len(entities)} entities from chunk {chunk_idx + 1}")

                # Process each entity
                for entity in entities:
                    # Generate embedding
                    embedding = self.embedder.encode(entity['name'])

                    # Store in Neo4j
                    success_neo4j = self.graph_storage.add_entity(
                        name=entity['name'],
                        entity_type=entity['type'],
                        embedding=embedding.tolist(),
                        label=self.config['entity_label']
                    )
                    if success_neo4j:
                        stats['entities_stored_neo4j'] += 1

                    # Store in Milvus
                    success_milvus = self.vector_storage.add_entity_vector(
                        name=entity['name'],
                        embedding=embedding.tolist(),
                        entity_type=entity['type']
                    )
                    if success_milvus:
                        stats['entities_stored_milvus'] += 1

                    # Add entity with chunk context for relationship extraction
                    all_entities.append({
                        **entity,
                        'chunk': chunk,
                        'chunk_idx': chunk_idx
                    })

            # Step 5-6: Extract relationships (pairwise entity classification)
            logger.info("Extracting relationships between entities...")
            for i, ent1_data in enumerate(all_entities):
                for j, ent2_data in enumerate(all_entities[i+1:], i+1):
                    ent1 = ent1_data['name']
                    ent2 = ent2_data['name']
                    type1 = ent1_data['type']
                    type2 = ent2_data['type']

                    # Skip same-type entities (pattern from graph_rag.py line 79)
                    if type1 == type2:
                        continue

                    # Use chunk context where both entities appear
                    # Prefer same chunk, otherwise use first entity's chunk
                    if ent1_data['chunk_idx'] == ent2_data['chunk_idx']:
                        context = ent1_data['chunk']
                    else:
                        context = ent1_data['chunk']

                    # Classify relationship
                    result = self.relation_classifier.classify_relation(
                        ent1=ent1,
                        ent2=ent2,
                        context=context
                    )

                    if result:
                        stats['relations_found'] += 1

                        # Store relationship in Neo4j
                        success = self.graph_storage.add_relationship(
                            ent1=ent1,
                            relation=result['relation'],
                            ent2=ent2,
                            entity_label=self.config['entity_label'],
                            rel_type=self.config['relationship_type']
                        )

                        if success:
                            stats['relations_stored'] += 1

            # Calculate processing time
            stats['processing_time_seconds'] = round(time.time() - start_time, 2)

            logger.info(
                f"Graph RAG processing complete: "
                f"{stats['entities_extracted']} entities, "
                f"{stats['relations_found']} relations, "
                f"{stats['processing_time_seconds']}s"
            )

            return stats

        except Exception as e:
            logger.error(f"Error in Graph RAG pipeline: {e}")
            raise

    def process_document(self, file_path: str) -> Dict[str, any]:
        """
        Read file, extract text, run pipeline.

        Args:
            file_path: Path to document file

        Returns:
            Statistics dict from process_text()
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Processing document: {file_path}")

        # Read text from file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Process text
            return self.process_text(text)

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise

    def get_statistics(self) -> Dict[str, any]:
        """
        Get current statistics from storage backends.

        Returns:
            Dict with entity/relationship counts from Neo4j and Milvus
        """
        return {
            "neo4j_entities": self.graph_storage.get_entity_count(
                label=self.config['entity_label']
            ),
            "neo4j_relationships": self.graph_storage.get_relationship_count(
                rel_type=self.config['relationship_type']
            ),
            "milvus_entities": self.vector_storage.get_entity_count()
        }

    def close(self):
        """Close all connections."""
        self.graph_storage.close()
        self.vector_storage.close()
        logger.info("Graph RAG pipeline closed")
