#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EmbeddingService - Service d'embeddings pour DARYL Sharding Memory
Utilise sentence-transformers pour générer des embeddings sémantiques
"""

import json
import hashlib
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
        # Convertir en liste si nécessaire
        if isinstance(texts, str):
            texts = [texts]
        
        # Générer des embeddings déterministes basés sur le hash du texte
        embeddings = []
        for text in texts:
            # Hash du texte pour génération déterministe
            s = sum(ord(c) for c in text.strip().lower()) % 1000
            s_norm = (s + 1) / 1001.0
            
            # Créer un embedding pseudo-aléatoire mais déterministe
            arr = []
            for i in range(384):
                # Seed basé sur hash du texte + index
                np.random.seed(s + i * 1000)
                val = (np.random.rand() - 0.5) * 2.0  # Valeur entre -1 et 1
                arr.append(val)
            
            embeddings.append(arr)
        
        return np.array(embeddings, dtype=np.float32)


class EmbeddingService:
    """Service pour générer et mettre en cache des embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", model: Optional[Union[str, DummyModel]] = None):
        """
        Initialise le service d'embeddings
        
        Args:
            model_name: Nom du modèle sentence-transformers
            model: Modèle optionnel (pour tests/mocks)
        """
        self.model_name = model_name
        self.model = model  # Permet d'injecter un modèle (ex: DummyModel pour tests)
        self.cache = {}  # Cache en mémoire pour les embeddings
        self._real_model = None  # Modèle réel (lazy load)
        self._dimension = 384  # Taille par défaut
        
        # Ne PAS charger le modèle dans __init__ (Lazy Load)
        print(f"✅ EmbeddingService initialisé (model_name: {model_name})")
    
    def _get_model(self):
        """
        Charge le modèle réel (Lazy Load) au premier appel
        
        Returns:
            Modèle (SentenceTransformer ou DummyModel)
        """
        # Si un modèle injecté (ex: DummyModel), l'utiliser
        if self.model is not None:
            return self.model
        
        # Si modèle réel déjà chargé, le retourner
        if self._real_model is not None:
            return self._real_model
        
        # Sinon, charger le modèle réel
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("⚠️ sentence-transformers non disponible. Utilisation DummyModel.")
            self.model = DummyModel(self.model_name)
            self._real_model = self.model
            self._dimension = self.model.dimension
            return self.model
        
        try:
            print(f"📥 Chargement du modèle réel: {self.model_name}")
            self._real_model = SentenceTransformer(self.model_name)
            self._dimension = self._real_model.get_sentence_embedding_dimension()
            print(f"✅ Modèle réel chargé: {self.model_name} (dimension: {self._dimension})")
            return self._real_model
        except Exception as e:
            print(f"❌ Erreur chargement modèle réel: {e}")
            print("⚠️ Utilisation DummyModel en cas d'échec.")
            self.model = DummyModel(self.model_name)
            self._real_model = self.model
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
            
            # Si c'est un tensor, le convertir en liste
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            elif isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
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
        
        try:
            # Obtenir le modèle (Lazy Load)
            model = self._get_model()
            
            # Générer en batch pour optimiser
            embeddings = model.encode(texts, convert_to_numpy=False)
            
            # Si c'est un tensor, le convertir en liste de listes
            if hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
            elif isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            # Si c'est une liste unique, la mettre dans une liste
            if isinstance(embeddings, list) and len(embeddings) > 0 and not isinstance(embeddings[0], list):
                embeddings = [embeddings]
            
            # Mettre en cache
            for text, embedding in zip(texts, embeddings):
                text_hash = self._hash_text(text)
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
        print("🗑️ Cache d'embeddings vidé")
    
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
            
            print(f"✅ Cache sauvegardé dans {file_path}")
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
            
            print(f"✅ Cache chargé depuis {file_path} ({len(cache_data)} embeddings)")
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
