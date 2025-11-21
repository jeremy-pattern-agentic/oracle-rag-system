"""
Vector Storage Module
Milvus Lite operations for entity embeddings
"""

from typing import List, Dict, Optional
import logging
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)

logger = logging.getLogger(__name__)


class VectorStorage:
    """
    Milvus Lite operations for Graph RAG entity embeddings.

    Pattern adapted from graph_rag.py line 74.
    """

    def __init__(
        self, milvus_config: Dict[str, any], collection_config: Dict[str, any]
    ):
        """
        Initialize Milvus Lite connection and collection.

        Args:
            milvus_config: Milvus configuration dict with keys:
                - uri: Milvus Lite database file path
                - token: Authentication token (empty for local)
            collection_config: Collection configuration dict with keys:
                - name: Collection name
                - dimension: Vector dimension
                - index_type: Index type (e.g., "IVF_FLAT")
                - metric_type: Distance metric (e.g., "COSINE")
                - nlist: Index parameter
        """
        self.milvus_config = milvus_config
        self.collection_config = collection_config
        self.collection_name = collection_config["name"]
        self.dimension = collection_config["dimension"]

        logger.info(f"Connecting to Milvus Lite at {milvus_config['uri']}")

        try:
            # Connect to Milvus Lite (local file-based storage)
            connections.connect(
                alias="default",
                uri=milvus_config["uri"],
                token=milvus_config.get("token", ""),
            )
            logger.info("Milvus Lite connection established")

            # Create collection if it doesn't exist
            self._ensure_collection()

        except Exception as e:
            logger.error(f"Milvus connection error: {e}")
            raise

    def _ensure_collection(self):
        """Create collection if it doesn't exist, otherwise load it."""
        if utility.has_collection(self.collection_name):
            logger.info(
                f"Collection '{self.collection_name}' already exists, loading..."
            )
            self.collection = Collection(self.collection_name)
            self.collection.load()
        else:
            logger.info(f"Creating new collection '{self.collection_name}'")
            self._create_collection()

    def _create_collection(self):
        """Create Milvus collection with proper schema."""
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="entity_name", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="entity_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(
                name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension
            ),
        ]

        schema = CollectionSchema(
            fields=fields,
            description=self.collection_config.get(
                "description", "Graph RAG entity embeddings"
            ),
        )

        # Create collection
        self.collection = Collection(name=self.collection_name, schema=schema)

        # Create index on vector field
        index_params = {
            "index_type": self.collection_config.get("index_type", "IVF_FLAT"),
            "metric_type": self.collection_config.get("metric_type", "COSINE"),
            "params": {"nlist": self.collection_config.get("nlist", 128)},
        }

        self.collection.create_index(field_name="embedding", index_params=index_params)

        # Load collection into memory
        self.collection.load()

        logger.info(
            f"Collection '{self.collection_name}' created with "
            f"{self.collection_config.get('index_type', 'IVF_FLAT')} index"
        )

    def add_entity_vector(
        self, name: str, embedding: List[float], entity_type: str
    ) -> bool:
        """
        Store entity embedding in Milvus.

        Args:
            name: Entity name
            embedding: Vector embedding (list of floats)
            entity_type: Entity type (PER, ORG, LOC, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not name or not embedding or not entity_type:
            logger.warning(
                "Empty name, embedding, or type provided to add_entity_vector"
            )
            return False

        # Convert embedding to list if numpy array
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        # Verify dimension
        if len(embedding) != self.dimension:
            logger.error(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {len(embedding)}"
            )
            return False

        try:
            # Insert entity vector
            data = [
                [name],  # entity_name
                [entity_type],  # entity_type
                [embedding],  # embedding
            ]

            self.collection.insert(data)
            self.collection.flush()

            logger.debug(
                f"Entity vector stored: {name} (type={entity_type}, dim={len(embedding)})"
            )
            return True

        except Exception as e:
            logger.error(f"Error adding entity vector {name}: {e}")
            raise

    def search_similar_entities(
        self,
        query_vector: List[float],
        top_k: int = 5,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, any]]:
        """
        Vector similarity search for entities.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            output_fields: Fields to return (default: ["entity_name", "entity_type"])

        Returns:
            List of search results: [{"name": str, "type": str, "distance": float}]
        """
        if not query_vector:
            logger.warning("Empty query vector provided to search_similar_entities")
            return []

        # Convert to list if numpy array
        if hasattr(query_vector, "tolist"):
            query_vector = query_vector.tolist()

        # Verify dimension
        if len(query_vector) != self.dimension:
            logger.error(
                f"Query vector dimension mismatch: expected {self.dimension}, "
                f"got {len(query_vector)}"
            )
            return []

        if output_fields is None:
            output_fields = ["entity_name", "entity_type"]

        try:
            # Search parameters
            search_params = {
                "metric_type": self.collection_config.get("metric_type", "COSINE"),
                "params": {"nprobe": 10},
            }

            # Perform search
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=output_fields,
            )

            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append(
                        {
                            "name": hit.entity.get("entity_name"),
                            "type": hit.entity.get("entity_type"),
                            "distance": float(hit.distance),
                        }
                    )

            logger.info(
                f"Found {len(formatted_results)} similar entities (top_k={top_k})"
            )
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching similar entities: {e}")
            raise

    def get_entity_count(self) -> int:
        """
        Get total count of entities in collection.

        Returns:
            Count of entities
        """
        try:
            self.collection.flush()
            return self.collection.num_entities

        except Exception as e:
            logger.error(f"Error getting entity count: {e}")
            return 0

    def drop_collection(self):
        """Drop the collection (for cleanup/testing)."""
        try:
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                logger.info(f"Collection '{self.collection_name}' dropped")

        except Exception as e:
            logger.error(f"Error dropping collection: {e}")

    def close(self):
        """Close Milvus connection."""
        try:
            connections.disconnect("default")
            logger.info("Milvus connection closed")

        except Exception as e:
            logger.error(f"Error closing Milvus connection: {e}")
