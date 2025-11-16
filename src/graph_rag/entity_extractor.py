"""
Entity Extraction Module
NER-based entity extraction using transformers pipeline
"""

from typing import List, Dict
import logging
from transformers import pipeline

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    NER-based entity extraction using BERT model.

    Pattern adapted from graph_rag.py lines 60-67.
    """

    def __init__(self, model_name: str, confidence_threshold: float = 0.7):
        """
        Initialize the entity extractor.

        Args:
            model_name: HuggingFace model name for NER
            confidence_threshold: Minimum confidence score for entity extraction
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold

        logger.info(f"Loading NER model: {model_name}")
        # Auto-detect GPU (device=0) or fallback to CPU (device=-1)
        import torch
        device = 0 if torch.cuda.is_available() else -1
        self.ner_pipeline = pipeline(
            "ner",
            model=model_name,
            aggregation_strategy="simple",  # Aggregates subword tokens
            device=device
        )
        logger.info(f"NER model loaded successfully (threshold={confidence_threshold})")

    def extract_entities(self, text: str) -> List[Dict[str, any]]:
        """
        Extract entities from text with confidence > threshold.

        Args:
            text: Input text to extract entities from

        Returns:
            List of entities: [{"name": str, "type": str, "confidence": float}]

        Example:
            >>> extractor = EntityExtractor("dbmdz/bert-large-cased-finetuned-conll03-english", 0.7)
            >>> entities = extractor.extract_entities("Elon Musk works at Tesla")
            >>> len(entities) >= 1
            True
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to extract_entities")
            return []

        try:
            # Run NER pipeline
            raw_entities = self.ner_pipeline(text)

            # Filter by confidence and clean entity names
            entities = []
            for ent in raw_entities:
                if ent['score'] >= self.confidence_threshold:
                    # Clean entity name: strip '##' from BERT subword tokens
                    name = ent['word'].strip().replace('##', '')

                    # Extract entity type: e.g., B-PER -> PER, I-ORG -> ORG
                    entity_type = ent['entity_group'] if 'entity_group' in ent else ent['entity'].split('-')[-1]

                    entities.append({
                        "name": name,
                        "type": entity_type,
                        "confidence": float(ent['score'])
                    })

            logger.info(f"Extracted {len(entities)} entities from text (threshold={self.confidence_threshold})")
            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            raise
