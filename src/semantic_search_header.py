#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SemanticSearch - Recherche vectorielle pour DARYL Sharding Memory
Utilise les embeddings et la similarité cosinus pour retrouver des informations similaires
"""

import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Import robuste (script vs module)
try:
    # Si exécuté depuis src/ comme package: `python -m src.semantic_search`
    from .embedding_service import EmbeddingService
except ImportError:
    try:
        # Si exécuté depuis root avec PYTHONPATH: `PYTHONPATH=/home/buraluxtr/clawd/src:$PYTHONPATH python src/semantic_search.py`
        from embedding_service import EmbeddingService
    except ImportError as e:
        raise ImportError(f"embedding_service non disponible. Vérifie l'installation / le PYTHONPATH: {e}")


class SemanticSearch:
    """Recherche sémantique basée sur les embeddings"""
    
    def __init__(self, shards_directory="memory/shards", threshold=0.7, top_k=5):
        """
        Initialise le module de recherche sémantique
        
        Args:
            shards_directory: Répertoire des shards JSON
            threshold: Seuil de similarité cosinus (0.0-1.0)
            top_k: Nombre de résultats à retourner
        """
        self.shards_dir = shards_directory
        self.threshold = threshold
        self.top_k = top_k
        self.embedding_service = EmbeddingService()
        self.shards_data = {}
        self._load_all_shards()
