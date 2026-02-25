#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SemanticSearch - Recherche vectorielle pour DARYL Sharding Memory
Utilise les embeddings et la similarité cosinus pour retrouver des informations similaires
"""

import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Import absolu pour éviter les problèmes de module relatif
try:
    from embedding_service import EmbeddingService
except ImportError as e:
    raise ImportError(f"embedding_service non disponible. Vérifiez le PYTHONPATH: {e}")


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
    
    def _load_all_shards(self):
        """Charge toutes les données de shards avec leurs embeddings"""
        shards_path = Path(self.shards_dir)
        
        if not shards_path.exists():
            print(f"❌ Répertoire des shards non trouvé: {self.shards_dir}")
            return
        
        # Parcourir tous les fichiers .json
        shard_files = list(shards_path.glob("*.json"))
        
        print(f"📁 Chargement de {len(shard_files)} shards depuis {self.shards_dir}")
        
        for shard_file in shard_files:
            shard_id = shard_file.stem
            try:
                with open(shard_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extraire les transactions avec leurs embeddings
                    transactions = data.get("transactions", [])
                    
                    # Générer les embeddings manquants si nécessaires
                    for tx in transactions:
                        if "embedding" not in tx and "content" in tx:
                            content = tx["content"]
                            embedding = self.embedding_service.generate_embedding(content)
                            if embedding is not None:
                                tx["embedding"] = embedding
                    
                    self.shards_data[shard_id] = {
                        "config": data.get("config", {}),
                        "transactions": transactions
                    }
                    
                    print(f"   ✅ {shard_id}: {len(transactions)} transactions chargées")
            except Exception as e:
                print(f"   ❌ {shard_id}: Erreur de chargement - {e}")
    
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calcule la similarité cosinus entre deux vecteurs
        
        Args:
            vec_a: Premier vecteur
            vec_b: Second vecteur
            
        Returns:
            Score de similarité cosinus (0.0-1.0)
        """
        try:
            # Convertir en numpy arrays
            a = np.array(vec_a, dtype=np.float32)
            b = np.array(vec_b, dtype=np.float32)
            
            # Vérifier si les vecteurs sont vides
            if np.all(a == 0) or np.all(b == 0):
                return 0.0
            
            # Produit scalaire
            dot = np.dot(a, b)
            
            # Normes
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            # Vérifier pour éviter la division par zéro
            if norm_a == 0.0 or norm_b == 0.0:
                return 0.0
            
            # Similarité cosinus
            similarity = dot / (norm_a * norm_b)
            
            # Assurer que le score est dans [-1, 1]
            return max(-1.0, min(1.0, similarity))
        except Exception as e:
            print(f"❌ Erreur calcul similarité: {e}")
            return 0.0
    
    def search(
        self,
        query_text: str,
        shard_id: Optional[str] = None,
        threshold: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Recherche sémantique dans les shards
        
        Args:
            query_text: Texte de la requête
            shard_id: ID du shard cible (optionnel)
            
        Returns:
            Liste des résultats triés par similarité (décroissante)
        """
        effective_threshold = self.threshold if threshold is None else threshold
        effective_top_k = self.top_k if top_k is None else top_k

        # Générer l'embedding de la requête
        query_embedding = self.embedding_service.generate_embedding(query_text)
        
        if query_embedding is None:
            print(f"❌ Erreur génération embedding pour: {query_text}")
            return []
        
        results = []
        
        # Déterminer les shards à interroger
        shards_to_search = [shard_id] if shard_id else list(self.shards_data.keys())
        
        for sid in shards_to_search:
            if sid not in self.shards_data:
                continue
            
            shard_data = self.shards_data[sid]
            transactions = shard_data.get("transactions", [])
            
            for tx in transactions:
                if "embedding" not in tx:
                    continue
                
                tx_embedding = tx["embedding"]
                
                # Calculer la similarité cosinus (return float)
                similarity = self._cosine_similarity(query_embedding, tx_embedding)
                
                # Filtrer par seuil
                if similarity >= effective_threshold:
                    output_similarity = float(max(0.0, min(1.0, similarity)))
                    results.append({
                        "shard_id": sid,
                        "shard_name": shard_data.get("config", {}).get("name", sid),
                        "transaction_id": tx.get("id", ""),
                        "content": tx.get("content", ""),
                        "importance": tx.get("importance", 0),
                        "timestamp": tx.get("timestamp", ""),
                        "source": tx.get("source", ""),
                        "similarity": output_similarity,
                        "score": output_similarity,
                    })

        # Fallback lexical si les embeddings ne remontent aucun résultat.
        if not results:
            query_lower = query_text.lower().strip()
            query_tokens = {tok for tok in query_lower.split() if tok}
            for sid in shards_to_search:
                if sid not in self.shards_data:
                    continue
                shard_data = self.shards_data[sid]
                for tx in shard_data.get("transactions", []):
                    content = tx.get("content", "")
                    content_lower = content.lower()
                    if not content_lower:
                        continue

                    if query_lower and query_lower in content_lower:
                        lexical_similarity = 1.0
                    else:
                        content_tokens = {tok for tok in content_lower.split() if tok}
                        overlap = len(query_tokens.intersection(content_tokens))
                        lexical_similarity = (overlap / len(query_tokens)) if query_tokens else 0.0

                    if lexical_similarity >= effective_threshold:
                        results.append({
                            "shard_id": sid,
                            "shard_name": shard_data.get("config", {}).get("name", sid),
                            "transaction_id": tx.get("id", ""),
                            "content": content,
                            "importance": tx.get("importance", 0),
                            "timestamp": tx.get("timestamp", ""),
                            "source": tx.get("source", ""),
                            "similarity": float(lexical_similarity),
                            "score": float(lexical_similarity),
                        })
        
        # Trier par similarité décroissante
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Limiter à top_k résultats
        return results[:effective_top_k]
    
    def hybrid_search(
        self,
        query_text: str,
        shard_id: Optional[str] = None,
        threshold: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Recherche hybride: sémantique + full-text (mots-clés)
        
        Args:
            query_text: Texte de la requête
            shard_id: ID du shard cible (optionnel)
            
        Returns:
            Liste des résultats triés (score hybride, décroissant)
        """
        # 1. Recherche sémantique
        effective_top_k = self.top_k if top_k is None else top_k
        semantic_results = self.search(query_text, shard_id, threshold=threshold, top_k=effective_top_k)
        
        # 2. Recherche full-text (mots-clés)
        query_lower = query_text.lower()
        text_results = []
        
        shards_to_search = [shard_id] if shard_id else list(self.shards_data.keys())
        
        for sid in shards_to_search:
            if sid not in self.shards_data:
                continue
            
            shard_data = self.shards_data[sid]
            transactions = shard_data.get("transactions", [])
            
            config = shard_data.get("config", {})
            keywords = config.get("keywords", [])
            
            for tx in transactions:
                content = tx.get("content", "").lower()
                
                # Vérifier les mots-clés
                keyword_matches = sum(1 for kw in keywords if kw.lower() in content)
                
                if keyword_matches > 0:
                    text_results.append({
                        "shard_id": sid,
                        "shard_name": config.get("name", sid),
                        "transaction_id": tx.get("id", ""),
                        "content": tx.get("content", ""),
                        "importance": tx.get("importance", 0),
                        "timestamp": tx.get("timestamp", ""),
                        "source": tx.get("source", ""),
                        "similarity": 0.5,
                        "score": 0.5,  # Score moyen pour full-text match
                        "match_type": "keyword"
                    })
        
        # 3. Fusionner les résultats (déduplication)
        seen_ids = set()
        hybrid_results = []
        
        # Ajouter les résultats sémantiques
        for r in semantic_results:
            if r["transaction_id"] not in seen_ids:
                r["match_type"] = "semantic"
                hybrid_results.append(r)
                seen_ids.add(r["transaction_id"])
        
        # Ajouter les résultats full-text (si pas déjà vus)
        for r in text_results:
            if r["transaction_id"] not in seen_ids:
                hybrid_results.append(r)
                seen_ids.add(r["transaction_id"])
        
        # 4. Trier par score hybride (similarité sémantique + pertinence mots-clés)
        for r in hybrid_results:
            r["hybrid_score"] = r["score"]
            if r["match_type"] == "keyword":
                r["hybrid_score"] += 0.3  # Bonus pour match mots-clés
        
        hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        # Limiter à top_k résultats
        return hybrid_results[:effective_top_k]
    
    def find_similar_transactions(self, transaction_id: str, shard_id: str, threshold: float = 0.9, top_k: int = 5) -> List[Dict]:
        """
        Trouve des transactions similaires dans un shard
        
        Args:
            transaction_id: ID de la transaction de référence
            shard_id: ID du shard cible
            threshold: Seuil de similarité (default: 0.9)
            top_k: Nombre de résultats (default: 5)
            
        Returns:
            Liste des transactions similaires
        """
        if shard_id not in self.shards_data:
            return []
        
        shard_data = self.shards_data[shard_id]
        transactions = shard_data.get("transactions", [])
        
        # Trouver la transaction de référence
        target_tx = None
        for tx in transactions:
            if tx.get("id") == transaction_id:
                target_tx = tx
                break
        
        if target_tx is None or "embedding" not in target_tx:
            return []
        
        target_embedding = target_tx["embedding"]
        similar_transactions = []
        
        # Calculer la similarité avec toutes les autres transactions
        for tx in transactions:
            if tx.get("id") == transaction_id:
                continue
            
            if "embedding" not in tx:
                continue
            
            tx_embedding = tx["embedding"]
            similarity = self._cosine_similarity(target_embedding, tx_embedding)
            
            # Filtrer par seuil
            if similarity >= threshold:
                similar_transactions.append({
                    "transaction_id": tx.get("id"),
                    "content": tx.get("content", ""),
                    "score": float(similarity),  # Ensure it's a float
                    "importance": tx.get("importance", 0),
                    "timestamp": tx.get("timestamp", "")
                })
        
        # Trier par similarité décroissante
        similar_transactions.sort(key=lambda x: x["score"], reverse=True)
        
        return similar_transactions[:top_k]
    
    def get_search_stats(self) -> Dict[str, int]:
        """
        Retourne les statistiques de recherche
        
        Returns:
            Dictionnaire avec les stats
        """
        total_transactions = sum(len(shard.get("transactions", [])) for shard in self.shards_data.values())
        total_embeddings = sum(1 for shard in self.shards_data.values() for tx in shard.get("transactions", []) if "embedding" in tx)
        
        cache_stats = self.embedding_service.get_cache_stats()
        
        return {
            "total_shards": len(self.shards_data),
            "total_transactions": total_transactions,
            "total_embeddings": total_embeddings,
            "cache_size": cache_stats.get("cache_size", 0),
            "model_name": cache_stats.get("model_name", ""),
            "embedding_dimension": cache_stats.get("embedding_dimension", 0)
        }


if __name__ == "__main__":
    # Test du module de recherche sémantique
    searcher = SemanticSearch(shards_directory="memory/shards", threshold=0.7, top_k=5)
    
    print("🧪 Test du module SemanticSearch")
    print(f"   Shards chargés: {len(searcher.shards_data)}")
    print(f"   Seuil de similarité: {searcher.threshold}")
    print(f"   Top-k: {searcher.top_k}")
    print()
    
    # Test de recherche sémantique
    query = "agents avec mémoire persistante"
    print(f"🔍 Recherche: {query}")
    results = searcher.search(query)
    
    print(f"   Résultats: {len(results)}")
    for i, r in enumerate(results, 1):
        print(f"   {i}. [{r['shard_name']}] Score: {r['score']:.3f} - {r['content'][:60]}...")
    
    print()
    
    # Test de recherche hybride
    print("🔍 Recherche hybride: sémantique + mots-clés")
    results_hybrid = searcher.hybrid_search(query)
    
    print(f"   Résultats: {len(results_hybrid)}")
    for i, r in enumerate(results_hybrid, 1):
        print(f"   {i}. [{r['shard_name']}] Score hybride: {r['hybrid_score']:.3f} - {r['content'][:60]}...")
    
    print()
    print("📊 Statistiques de recherche:")
    stats = searcher.get_search_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
