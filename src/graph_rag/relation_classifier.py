"""
Relation Classification Module
Zero-shot classification of relationships between entities
"""

from typing import List, Dict, Optional
import logging
from transformers import pipeline

logger = logging.getLogger(__name__)


class RelationClassifier:
    """
    Zero-shot relation classification between entities using BART model.

    Pattern adapted from graph_rag.py lines 77-87.
    """

    def __init__(
        self,
        model_name: str,
        candidate_relations: List[str],
        confidence_threshold: float = 0.6,
    ):
        """
        Initialize the relation classifier.

        Args:
            model_name: HuggingFace model name for zero-shot classification
            candidate_relations: List of possible relationship types
            confidence_threshold: Minimum confidence score for relation extraction
        """
        self.model_name = model_name
        self.candidate_relations = candidate_relations
        self.confidence_threshold = confidence_threshold

        logger.info(f"Loading relation classifier model: {model_name}")
        # Auto-detect GPU (device=0) or fallback to CPU (device=-1)
        import torch

        device = 0 if torch.cuda.is_available() else -1
        self.classifier = pipeline(
            "zero-shot-classification", model=model_name, device=device
        )
        logger.info(
            f"Relation classifier loaded (threshold={confidence_threshold}, "
            f"candidates={len(candidate_relations)})"
        )

    def classify_relation(
        self, ent1: str, ent2: str, context: str
    ) -> Optional[Dict[str, any]]:
        """
        Classify relationship between two entities using context.

        Args:
            ent1: First entity name
            ent2: Second entity name
            context: Text context containing both entities

        Returns:
            {"relation": str, "confidence": float} or None if confidence < threshold

        Example:
            >>> classifier = RelationClassifier(
            ...     "facebook/bart-large-mnli",
            ...     ["WORKS_FOR", "LOCATED_IN", "NONE"],
            ...     0.6
            ... )
            >>> result = classifier.classify_relation(
            ...     "Elon Musk", "Tesla",
            ...     "Elon Musk is the CEO of Tesla"
            ... )
            >>> result is not None
            True
        """
        if not ent1 or not ent2 or not context:
            logger.warning("Empty entity or context provided to classify_relation")
            return None

        try:
            # Build hypothesis from entity pair and context
            # Pattern from graph_rag.py line 82: include chunk context
            hypothesis = f"{ent1} and {ent2} in context: {context[:100]}"

            # Run zero-shot classification
            result = self.classifier(
                hypothesis, self.candidate_relations, multi_label=False
            )

            # Get top prediction
            top_label = result["labels"][0]
            top_score = result["scores"][0]

            # Filter by confidence threshold and exclude "NONE" relations
            if top_score >= self.confidence_threshold and top_label != "NONE":
                logger.debug(
                    f"Classified relation: {ent1} -{top_label}-> {ent2} "
                    f"(confidence={top_score:.3f})"
                )
                return {"relation": top_label, "confidence": float(top_score)}
            else:
                logger.debug(
                    f"No confident relation found between {ent1} and {ent2} "
                    f"(top={top_label}, score={top_score:.3f})"
                )
                return None

        except Exception as e:
            logger.error(f"Error classifying relation: {e}")
            raise
