"""
Graph Storage Module
Neo4j operations for entity and relationship storage
"""

from typing import List, Dict
import logging
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)


class GraphStorage:
    """
    Neo4j operations for Graph RAG entity/relationship storage.

    Pattern adapted from graph_rag.py lines 24-37.
    """

    def __init__(self, config: Dict[str, any]):
        """
        Initialize Neo4j connection.

        Args:
            config: Neo4j configuration dict with keys:
                - uri: Neo4j bolt URI
                - user: Neo4j username
                - password: Neo4j password
                - database: Neo4j database name
        """
        self.config = config
        self.uri = config["uri"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]

        logger.info(f"Connecting to Neo4j at {self.uri}, database={self.database}")

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=config.get("max_connection_lifetime", 3600),
                max_connection_pool_size=config.get("max_connection_pool_size", 50),
                connection_acquisition_timeout=config.get(
                    "connection_acquisition_timeout", 120
                ),
            )

            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Neo4j connection established successfully")

        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Neo4j connection error: {e}")
            raise

    def add_entity(
        self,
        name: str,
        entity_type: str,
        embedding: List[float],
        label: str = "RagEntity",
    ) -> bool:
        """
        Create or update entity node in Neo4j.

        Uses MERGE to avoid duplicates (pattern from graph_rag.py lines 24-29).

        Args:
            name: Entity name (unique identifier)
            entity_type: Entity type (PER, ORG, LOC, etc.)
            embedding: Vector embedding of entity (list of floats)
            label: Neo4j node label (default: "RagEntity")

        Returns:
            True if successful, False otherwise
        """
        if not name or not entity_type:
            logger.warning("Empty name or type provided to add_entity")
            return False

        # Convert embedding to list if numpy array
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        query = f"""
        MERGE (e:{label} {{name: $name}})
        SET e.type = $type,
            e.embedding = $embedding,
            e.updated_at = datetime()
        RETURN e.name as name
        """

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(
                    query, name=name, type=entity_type, embedding=embedding
                )
                record = result.single()

                if record:
                    logger.debug(f"Entity stored: {name} (type={entity_type})")
                    return True
                else:
                    logger.warning(f"Failed to store entity: {name}")
                    return False

        except Exception as e:
            logger.error(f"Error adding entity {name}: {e}")
            raise

    def add_relationship(
        self,
        ent1: str,
        relation: str,
        ent2: str,
        entity_label: str = "RagEntity",
        rel_type: str = "RAG_RELATION",
    ) -> bool:
        """
        Create relationship edge between two entities.

        Uses MERGE to avoid duplicate relationships (pattern from graph_rag.py lines 32-37).

        Args:
            ent1: Source entity name
            relation: Relationship type (e.g., "WORKS_FOR")
            ent2: Target entity name
            entity_label: Node label for entities (default: "RagEntity")
            rel_type: Relationship label (default: "RAG_RELATION")

        Returns:
            True if successful, False otherwise
        """
        if not ent1 or not ent2 or not relation:
            logger.warning("Empty entity or relation provided to add_relationship")
            return False

        query = f"""
        MATCH (a:{entity_label} {{name: $ent1}}), (b:{entity_label} {{name: $ent2}})
        MERGE (a)-[r:{rel_type} {{type: $relation}}]->(b)
        SET r.updated_at = datetime()
        RETURN r.type as relation
        """

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, ent1=ent1, ent2=ent2, relation=relation)
                record = result.single()

                if record:
                    logger.debug(f"Relationship stored: {ent1} -{relation}-> {ent2}")
                    return True
                else:
                    logger.warning(
                        f"Failed to create relationship: {ent1} -{relation}-> {ent2} "
                        "(entities may not exist)"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error adding relationship {ent1}-{relation}->{ent2}: {e}")
            raise

    def entity_exists(self, name: str, label: str = "RagEntity") -> bool:
        """
        Check if entity already exists in Neo4j.

        Args:
            name: Entity name to check
            label: Node label (default: "RagEntity")

        Returns:
            True if entity exists, False otherwise
        """
        query = f"""
        MATCH (e:{label} {{name: $name}})
        RETURN e.name as name
        LIMIT 1
        """

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, name=name)
                return result.single() is not None

        except Exception as e:
            logger.error(f"Error checking entity existence: {e}")
            return False

    def get_entity_count(self, label: str = "RagEntity") -> int:
        """
        Get total count of entities in graph.

        Args:
            label: Node label (default: "RagEntity")

        Returns:
            Count of entities
        """
        query = f"MATCH (e:{label}) RETURN count(e) as count"

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                record = result.single()
                return record["count"] if record else 0

        except Exception as e:
            logger.error(f"Error getting entity count: {e}")
            return 0

    def get_relationship_count(self, rel_type: str = "RAG_RELATION") -> int:
        """
        Get total count of relationships in graph.

        Args:
            rel_type: Relationship type (default: "RAG_RELATION")

        Returns:
            Count of relationships
        """
        query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                record = result.single()
                return record["count"] if record else 0

        except Exception as e:
            logger.error(f"Error getting relationship count: {e}")
            return 0

    def close(self):
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
