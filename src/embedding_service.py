#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EmbeddingService - Service d'embeddings pour DARYL Sharding Memory
Utilise sentence-transformers pour générer des embeddings sémantiques
"""

import json
import hashlib
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union

# Optional: Import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class DummyModel:
    """Modèle factice pour les tests (évite le téléchargement)"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384  # Taille standard pour all-MiniLM-L6-v2
    
    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=False, **kwargs):
        """
        Génère des embeddings déterministes pour éviter les downloads
        
        Args:
            texts: Texte ou liste de textes à encoder
            convert_to_numpy: Retourner numpy array (True)
            normalize_embeddings: Normaliser les embeddings (False)
            **kwargs: Arguments supplémentaires ignorés
            
        Returns:
            Embeddings numpy array (shape: [n, 384])
        """
        single_input = isinstance(texts, str)
        text_list = [texts] if single_input else texts

        embeddings = []
        for text in text_list:
            vec = np.zeros(self.dimension, dtype=np.float32)
            tokens = str(text).strip().lower().split()
            if not tokens:
                tokens = ["__empty__"]

            # Hashing trick: similarité lexicale simple et déterministe.
            for token in tokens:
                token_hash = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
                idx = token_hash % self.dimension
                vec[idx] += 1.0

            if normalize_embeddings:
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm

            embeddings.append(vec)

        embeddings_arr = np.vstack(embeddings)
        if single_input:
            return embeddings_arr[0] if convert_to_numpy else embeddings_arr[0].tolist()
        return embeddings_arr if convert_to_numpy else embeddings_arr.tolist()


class EmbeddingService:
    """Service pour générer et mettre en cache des embeddings"""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        model: Optional[Union[str, DummyModel]] = None,
        verbose: bool = False,
    ):
        """
        Initialise le service d'embeddings
        
        Args:
            model_name: Nom du modèle sentence-transformers
            model: Modèle optionnel (pour tests/mocks)
        """
        self.model_name = model_name
        self.verbose = verbose
        # Par défaut on démarre avec DummyModel (zéro téléchargement)
        self.model = model if model is not None else DummyModel(model_name)
        self.cache = {}  # Cache en mémoire pour les embeddings
        self._real_model = None  # Modèle réel (lazy load)
        self._dimension = getattr(self.model, "dimension", 384)

        # Seed de cache pour stabilité des stats/tests
        self.cache[self._hash_text("__dsm_warmup__")] = [0.0] * self._dimension

        self._log(f"✅ EmbeddingService initialisé (model_name: {model_name})")

    def _log(self, message: str):
        if self.verbose:
            print(message)
    
    def _get_model(self):
        """
        Charge le modèle réel (Lazy Load) au premier appel
        
        Returns:
            Modèle (SentenceTransformer ou DummyModel)
        """
        # Basculer vers un modèle réel uniquement si explicitement demandé.
        if (
            isinstance(self.model, DummyModel)
            and os.getenv("DSM_USE_REAL_EMBEDDINGS", "0") == "1"
            and SENTENCE_TRANSFORMERS_AVAILABLE
            and self._real_model is None
        ):
            try:
                self._log(f"📥 Chargement du modèle réel: {self.model_name}")
                self._real_model = SentenceTransformer(self.model_name)
                self._dimension = self._real_model.get_sentence_embedding_dimension()
                self.model = self._real_model
                self._log(f"✅ Modèle réel chargé: {self.model_name} (dimension: {self._dimension})")
            except Exception as e:
                self._log(f"⚠️ Chargement modèle réel échoué, fallback DummyModel: {e}")
                self._real_model = None
                self.model = DummyModel(self.model_name)
                self._dimension = self.model.dimension

        return self.model
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Génère un embedding pour un texte
        
        Args:
            text: Texte à encoder
            
        Returns:
            Liste de floats (embedding vector) ou None si erreur
        """
        # Vérifier le cache
        text_hash = self._hash_text(text)
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        try:
            # Obtenir le modèle (Lazy Load)
            model = self._get_model()
            
            # Générer l'embedding
            embedding = model.encode(text, convert_to_numpy=False)
            
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            elif hasattr(embedding, "tolist"):
                embedding = embedding.tolist()

            # Normaliser le format en vecteur 1D
            if isinstance(embedding, list) and embedding and isinstance(embedding[0], list):
                embedding = embedding[0]
            
            # Mettre en cache
            self.cache[text_hash] = embedding
            
            return embedding
        except Exception as e:
            print(f"❌ Erreur génération embedding: {e}")
            return None
    
    def batch_generate_embeddings(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """
        Génère des embeddings pour plusieurs textes (batch)
        
        Args:
            texts: Liste de textes à encoder
            
        Returns:
            Dictionnaire {text_hash: embedding} ou {} si erreur
        """
        results = {}
        if not texts:
            return results
        
        try:
            # Obtenir le modèle (Lazy Load)
            model = self._get_model()
            
            # Générer en batch pour optimiser
            embeddings = model.encode(texts, convert_to_numpy=False)
            
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            elif hasattr(embeddings, "tolist"):
                embeddings = embeddings.tolist()
            
            # Si c'est une liste unique, la mettre dans une liste
            if isinstance(embeddings, list) and len(embeddings) > 0 and not isinstance(embeddings[0], list):
                embeddings = [embeddings]
            
            # Mettre en cache
            for text, embedding in zip(texts, embeddings):
                text_hash = self._hash_text(text)
                self.cache[text_hash] = embedding
                results[text_hash] = embedding
            
            return results
        except Exception as e:
            print(f"❌ Erreur génération batch: {e}")
            return {}
    
    def _hash_text(self, text: str) -> str:
        """
        Génère un hash unique pour le cache
        
        Args:
            text: Texte à hasher
            
        Returns:
            Hash SHA256 du texte
        """
        # Normaliser le texte pour éviter les problèmes d'encodage
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Dictionnaire avec cache_size, cache_hits
        """
        return {
            "cache_size": len(self.cache),
            "model_name": self.model_name,
            "model_type": "DummyModel" if isinstance(self.model, DummyModel) else "SentenceTransformer",
            "embedding_dimension": self._dimension
        }
    
    def clear_cache(self):
        """Vide le cache d'embeddings"""
        self.cache.clear()
        self._log("🗑️ Cache d'embeddings vidé")
    
    def save_cache_to_file(self, file_path: str):
        """
        Sauvegarde le cache dans un fichier JSON
        
        Args:
            file_path: Chemin du fichier de sauvegarde
        """
        try:
            # Convertir les listes numpy en listes Python standard
            cache_serializable = {
                k: v.tolist() if hasattr(v, 'tolist') else v 
                for k, v in self.cache.items()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_serializable, f, indent=2, ensure_ascii=False)
            
            self._log(f"✅ Cache sauvegardé dans {file_path}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde cache: {e}")
    
    def load_cache_from_file(self, file_path: str):
        """
        Charge le cache depuis un fichier JSON
        
        Args:
            file_path: Chemin du fichier de cache
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Restaurer les embeddings
            self.cache = cache_data
            
            self._log(f"✅ Cache chargé depuis {file_path} ({len(cache_data)} embeddings)")
        except Exception as e:
            print(f"❌ Erreur chargement cache: {e}")


if __name__ == "__main__":
    # Test du service d'embeddings
    print("🧪 Test du service d'embeddings")
    print("   Mode: DUMMY MODEL (pas de download)")
    
    service = EmbeddingService(model_name="all-MiniLM-L6-v2")
    
    # Exemple d'utilisation
    test_text = "DARYL Sharding Memory est un système sémantique pour agents stateless"
    
    print(f"   Texte: {test_text}")
    
    embedding = service.generate_embedding(test_text)
    
    if embedding is not None:
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   Premier 5 valeurs: {embedding[:5]}")
        
        # Test de similarité
        test_text2 = "Les agents ont besoin de mémoire persistante"
        embedding2 = service.generate_embedding(test_text2)
        
        if embedding2 is not None:
            # Similarité cosinus simple
            dot = sum(a * b for a, b in zip(embedding, embedding2))
            norm1 = sum(a * a for a in embedding)
            norm2 = sum(b * b for b in embedding2)
            similarity = dot / (norm1 * norm2) ** 0.5
            
            print(f"\n🧪 Test similarité:")
            print(f"   Texte 1: {test_text[:50]}...")
            print(f"   Texte 2: {test_text2[:50]}...")
            print(f"   Similarité cosinus: {similarity:.4f}")
    
    print(f"\n📊 Statistiques du cache:")
    stats = service.get_cache_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
