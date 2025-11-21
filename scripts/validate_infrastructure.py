#!/usr/bin/env python3
"""
Oracle RAG System - Infrastructure Validation Script
Tests Neo4j and Milvus Lite connectivity

Evidence-based validation per Mr.AI Framework Gate 1
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from neo4j import GraphDatabase
from pymilvus import MilvusClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def validate_neo4j():
    """Test Neo4j connectivity"""
    logger.info("=" * 60)
    logger.info("GATE 1: Neo4j Connectivity Validation")
    logger.info("=" * 60)

    try:
        # Import config
        sys.path.insert(0, str(Path(__file__).parent.parent / "config"))
        from config import NEO4J_CONFIG

        # Connect to Neo4j
        driver = GraphDatabase.driver(
            NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
        )

        # Test connection with simple query
        with driver.session(database=NEO4J_CONFIG["database"]) as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()

            if record["test"] == 1:
                logger.info("✅ Neo4j connection successful")

                # Get database info
                db_info = session.run("""
                    CALL dbms.components() YIELD name, versions, edition
                    RETURN name, versions[0] AS version, edition
                """).single()

                logger.info(f"   Database: {NEO4J_CONFIG['database']}")
                logger.info(f"   Version: {db_info['version']}")
                logger.info(f"   Edition: {db_info['edition']}")

                # Count existing nodes
                node_count = session.run("MATCH (n) RETURN count(n) AS count").single()[
                    "count"
                ]
                logger.info(f"   Existing nodes: {node_count}")

                driver.close()
                return True
            else:
                logger.error("❌ Neo4j query returned unexpected result")
                driver.close()
                return False

    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        return False


def validate_milvus_lite():
    """Test Milvus Lite connectivity"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("GATE 1: Milvus Lite Connectivity Validation")
    logger.info("=" * 60)

    try:
        # Import config
        sys.path.insert(0, str(Path(__file__).parent.parent / "config"))
        from config import MILVUS_CONFIG

        # Connect to Milvus Lite (local file-based)
        client = MilvusClient(uri=MILVUS_CONFIG["uri"])

        logger.info("✅ Milvus Lite connection successful")
        logger.info(f"   Storage: {MILVUS_CONFIG['uri']}")
        logger.info("   Mode: Milvus Lite (CPU-only, local file)")

        # List existing collections
        collections = client.list_collections()
        logger.info(f"   Existing collections: {len(collections)}")

        if collections:
            for coll_name in collections:
                logger.info(f"      - {coll_name}")

        # Test collection creation (will drop if exists)
        test_collection = "oracle_rag_test"

        if test_collection in collections:
            logger.info(f"   Dropping test collection: {test_collection}")
            client.drop_collection(test_collection)

        # Create test collection
        logger.info(f"   Creating test collection: {test_collection}")
        client.create_collection(
            collection_name=test_collection,
            dimension=384,  # all-MiniLM-L6-v2 dimension
            metric_type="COSINE",
        )

        # Insert test data
        test_data = [
            {"id": 1, "vector": [0.1] * 384, "text": "Oracle RAG test entity 1"},
            {"id": 2, "vector": [0.2] * 384, "text": "Oracle RAG test entity 2"},
        ]

        logger.info(f"   Inserting {len(test_data)} test vectors...")
        client.insert(collection_name=test_collection, data=test_data)

        # Query test data
        logger.info("   Querying test vectors...")
        results = client.search(
            collection_name=test_collection,
            data=[[0.15] * 384],  # Query vector
            limit=2,
            output_fields=["text"],
        )

        logger.info(f"   Query returned {len(results[0])} results")
        for i, hit in enumerate(results[0]):
            logger.info(
                f"      {i + 1}. ID={hit['id']}, Distance={hit['distance']:.4f}, Text={hit['entity']['text']}"
            )

        # Cleanup test collection
        logger.info("   Cleaning up test collection...")
        client.drop_collection(test_collection)

        logger.info("✅ Milvus Lite validation complete")
        return True

    except Exception as e:
        logger.error(f"❌ Milvus Lite validation failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """Run all infrastructure validation tests"""
    logger.info("\n" + "=" * 60)
    logger.info("Oracle RAG System - Infrastructure Validation")
    logger.info("Mr.AI Framework Gate 1: Functional Validation")
    logger.info("=" * 60 + "\n")

    results = {"neo4j": validate_neo4j(), "milvus_lite": validate_milvus_lite()}

    logger.info("")
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)

    for component, status in results.items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        logger.info(f"{component.upper()}: {status_str}")

    all_passed = all(results.values())

    logger.info("")
    if all_passed:
        logger.info("🎉 Gate 1 PASSED: All infrastructure components validated")
        logger.info("   Ready to proceed with Oracle RAG implementation")
        return 0
    else:
        logger.error("❌ Gate 1 FAILED: Infrastructure issues detected")
        logger.error("   Resolve failures before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
