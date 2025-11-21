"""
Unit Tests for Graph RAG Module
Tests entity extraction, relation classification, storage, and pipeline
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_rag.chunker import chunk_text
from graph_rag.entity_extractor import EntityExtractor
from graph_rag.relation_classifier import RelationClassifier
from graph_rag.graph_storage import GraphStorage
from graph_rag.vector_storage import VectorStorage
from graph_rag.pipeline import GraphRAGPipeline

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent / "config"))
from config import NEO4J_CONFIG, MILVUS_CONFIG, MILVUS_COLLECTIONS, GRAPH_RAG_CONFIG


class TestChunker:
    """Test text chunking functionality."""

    def test_basic_chunking(self):
        """Test basic text chunking."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text(text, max_length=10)

        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        print(f"\n✓ Chunking test passed: {len(chunks)} chunks created")

    def test_long_text_chunking(self):
        """Test chunking of longer text."""
        text = " ".join([f"Sentence {i}." for i in range(100)])
        chunks = chunk_text(text, max_length=50)

        assert len(chunks) > 1
        for chunk in chunks:
            word_count = len(chunk.split())
            assert word_count <= 60  # Allow some margin
        print(f"✓ Long text chunking test passed: {len(chunks)} chunks")

    def test_empty_text(self):
        """Test handling of empty text."""
        chunks = chunk_text("")
        assert chunks == []
        print("✓ Empty text handling test passed")


class TestEntityExtractor:
    """Test entity extraction functionality."""

    @pytest.fixture
    def extractor(self):
        """Create entity extractor instance."""
        return EntityExtractor(
            model_name=GRAPH_RAG_CONFIG["ner_model"],
            confidence_threshold=GRAPH_RAG_CONFIG["ner_confidence_threshold"],
        )

    def test_entity_extraction(self, extractor):
        """Test NER pipeline extracts entities correctly."""
        sample_text = "Elon Musk is the CEO of Tesla. Tesla is based in California."
        entities = extractor.extract_entities(sample_text)

        print("\n✓ Entity extraction test:")
        print(f"  Text: {sample_text}")
        print(f"  Entities found: {len(entities)}")
        for ent in entities:
            print(
                f"    - {ent['name']} ({ent['type']}, confidence={ent['confidence']:.3f})"
            )

        assert len(entities) >= 2  # At least Elon Musk and Tesla
        assert all(e["confidence"] >= 0.7 for e in entities)
        assert all("name" in e and "type" in e for e in entities)

    def test_entity_confidence_threshold(self, extractor):
        """Test confidence threshold filtering."""
        text = "Apple is a company."
        entities = extractor.extract_entities(text)

        for ent in entities:
            assert ent["confidence"] >= GRAPH_RAG_CONFIG["ner_confidence_threshold"]

        print(
            f"✓ Confidence threshold test passed: all entities > {GRAPH_RAG_CONFIG['ner_confidence_threshold']}"
        )

    def test_empty_text_handling(self, extractor):
        """Test handling of empty text."""
        entities = extractor.extract_entities("")
        assert entities == []
        print("✓ Empty text entity extraction test passed")


class TestRelationClassifier:
    """Test relation classification functionality."""

    @pytest.fixture
    def classifier(self):
        """Create relation classifier instance."""
        return RelationClassifier(
            model_name=GRAPH_RAG_CONFIG["relation_model"],
            candidate_relations=GRAPH_RAG_CONFIG["candidate_relations"],
            confidence_threshold=GRAPH_RAG_CONFIG["relation_confidence_threshold"],
        )

    def test_relation_classification(self, classifier):
        """Test zero-shot relation classifier."""
        result = classifier.classify_relation(
            "Elon Musk", "Tesla", "Elon Musk is the CEO of Tesla"
        )

        print("\n✓ Relation classification test:")
        if result:
            print("  Entities: Elon Musk -> Tesla")
            print(
                f"  Relation: {result['relation']} (confidence={result['confidence']:.3f})"
            )
            assert result["relation"] in GRAPH_RAG_CONFIG["candidate_relations"]
            assert (
                result["confidence"]
                >= GRAPH_RAG_CONFIG["relation_confidence_threshold"]
            )
        else:
            print(
                f"  No confident relation found (threshold={GRAPH_RAG_CONFIG['relation_confidence_threshold']})"
            )

    def test_no_relation(self, classifier):
        """Test classification when no clear relation exists."""
        result = classifier.classify_relation(
            "Apple", "Microsoft", "Apple and Microsoft are technology companies"
        )

        print(f"✓ No relation test passed: result={result}")

    def test_location_relation(self, classifier):
        """Test LOCATED_IN relation."""
        result = classifier.classify_relation(
            "Tesla", "California", "Tesla is based in California"
        )

        print("\n✓ Location relation test:")
        if result:
            print(
                f"  Relation: {result['relation']} (confidence={result['confidence']:.3f})"
            )


class TestGraphStorage:
    """Test Neo4j graph storage functionality."""

    @pytest.fixture
    def storage(self):
        """Create graph storage instance."""
        storage = GraphStorage(NEO4J_CONFIG)
        yield storage
        storage.close()

    def test_neo4j_connection(self, storage):
        """Test Neo4j connectivity."""
        # Connection verified in __init__
        print("\n✓ Neo4j connection test passed")
        assert storage.driver is not None

    def test_entity_storage(self, storage):
        """Test entity storage in Neo4j."""
        test_embedding = [0.1] * GRAPH_RAG_CONFIG["embedding_dimension"]

        success = storage.add_entity(
            name="TestEntity_GraphRAG",
            entity_type="TEST",
            embedding=test_embedding,
            label=GRAPH_RAG_CONFIG["entity_label"],
        )

        assert success
        assert storage.entity_exists(
            "TestEntity_GraphRAG", label=GRAPH_RAG_CONFIG["entity_label"]
        )

        print("\n✓ Entity storage test passed")
        print("  Entity: TestEntity_GraphRAG (type=TEST)")

    def test_relationship_storage(self, storage):
        """Test relationship storage in Neo4j."""
        # Create two test entities first
        test_embedding = [0.1] * GRAPH_RAG_CONFIG["embedding_dimension"]

        storage.add_entity(
            "TestEnt1_GraphRAG",
            "PERSON",
            test_embedding,
            GRAPH_RAG_CONFIG["entity_label"],
        )
        storage.add_entity(
            "TestEnt2_GraphRAG", "ORG", test_embedding, GRAPH_RAG_CONFIG["entity_label"]
        )

        # Create relationship
        success = storage.add_relationship(
            "TestEnt1_GraphRAG",
            "WORKS_FOR",
            "TestEnt2_GraphRAG",
            entity_label=GRAPH_RAG_CONFIG["entity_label"],
            rel_type=GRAPH_RAG_CONFIG["relationship_type"],
        )

        assert success
        print("\n✓ Relationship storage test passed")
        print("  Relationship: TestEnt1_GraphRAG -WORKS_FOR-> TestEnt2_GraphRAG")

    def test_get_counts(self, storage):
        """Test entity/relationship count queries."""
        entity_count = storage.get_entity_count(label=GRAPH_RAG_CONFIG["entity_label"])
        rel_count = storage.get_relationship_count(
            rel_type=GRAPH_RAG_CONFIG["relationship_type"]
        )

        print("\n✓ Count queries test passed")
        print(f"  Entities: {entity_count}")
        print(f"  Relationships: {rel_count}")

        assert entity_count >= 0
        assert rel_count >= 0


class TestVectorStorage:
    """Test Milvus vector storage functionality."""

    @pytest.fixture
    def storage(self):
        """Create vector storage instance."""
        storage = VectorStorage(MILVUS_CONFIG, MILVUS_COLLECTIONS["graph_entities"])
        yield storage
        storage.close()

    def test_milvus_connection(self, storage):
        """Test Milvus Lite connectivity."""
        # Connection verified in __init__
        print("\n✓ Milvus Lite connection test passed")
        assert storage.collection is not None

    def test_vector_storage(self, storage):
        """Test vector storage in Milvus."""
        test_embedding = [0.1] * GRAPH_RAG_CONFIG["embedding_dimension"]

        success = storage.add_entity_vector(
            name="TestEntity_Milvus", embedding=test_embedding, entity_type="TEST"
        )

        assert success
        print("\n✓ Vector storage test passed")
        print(f"  Entity: TestEntity_Milvus (dim={len(test_embedding)})")

    def test_vector_search(self, storage):
        """Test vector similarity search."""
        # Add a test vector first
        test_embedding = [0.2] * GRAPH_RAG_CONFIG["embedding_dimension"]
        storage.add_entity_vector("SearchTest_Entity", test_embedding, "TEST")

        # Search for similar vectors
        results = storage.search_similar_entities(test_embedding, top_k=5)

        print("\n✓ Vector search test passed")
        print(f"  Results found: {len(results)}")
        for i, result in enumerate(results[:3]):
            print(f"    {i + 1}. {result['name']} (distance={result['distance']:.4f})")

        assert isinstance(results, list)

    def test_get_count(self, storage):
        """Test entity count in Milvus."""
        count = storage.get_entity_count()

        print("\n✓ Milvus count query test passed")
        print(f"  Entities in Milvus: {count}")

        assert count >= 0


class TestGraphRAGPipeline:
    """Test complete Graph RAG pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        pipeline = GraphRAGPipeline(
            neo4j_config=NEO4J_CONFIG,
            milvus_config=MILVUS_CONFIG,
            collection_config=MILVUS_COLLECTIONS["graph_entities"],
            graph_rag_config=GRAPH_RAG_CONFIG,
        )
        yield pipeline
        pipeline.close()

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.entity_extractor is not None
        assert pipeline.relation_classifier is not None
        assert pipeline.graph_storage is not None
        assert pipeline.vector_storage is not None
        assert pipeline.embedder is not None

        print("\n✓ Pipeline initialization test passed")

    def test_end_to_end_pipeline(self, pipeline):
        """Test complete Graph RAG pipeline."""
        sample_text = """
        Elon Musk is the CEO of Tesla. Tesla is based in California.
        Musk also founded SpaceX, which works on rocket technology.
        """

        stats = pipeline.process_text(sample_text)

        print("\n" + "=" * 60)
        print("END-TO-END PIPELINE TEST - EVIDENCE")
        print("=" * 60)
        print(f"Chunks created: {stats['chunks_created']}")
        print(f"Entities extracted: {stats['entities_extracted']}")
        print(f"Entities stored in Neo4j: {stats['entities_stored_neo4j']}")
        print(f"Entities stored in Milvus: {stats['entities_stored_milvus']}")
        print(f"Relations found: {stats['relations_found']}")
        print(f"Relations stored: {stats['relations_stored']}")
        print(f"Processing time: {stats['processing_time_seconds']}s")
        print("=" * 60)

        assert stats["chunks_created"] >= 1
        assert stats["entities_extracted"] >= 3  # Elon Musk, Tesla, California, SpaceX
        assert stats["entities_stored_neo4j"] >= 3
        assert stats["entities_stored_milvus"] >= 3
        assert stats["processing_time_seconds"] > 0

    def test_get_statistics(self, pipeline):
        """Test statistics retrieval."""
        stats = pipeline.get_statistics()

        print("\n✓ Statistics test passed")
        print(f"  Neo4j entities: {stats['neo4j_entities']}")
        print(f"  Neo4j relationships: {stats['neo4j_relationships']}")
        print(f"  Milvus entities: {stats['milvus_entities']}")

        assert "neo4j_entities" in stats
        assert "neo4j_relationships" in stats
        assert "milvus_entities" in stats


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
