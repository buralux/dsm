#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemoryCompressor - Compression de mémoire pour DARYL Sharding Memory
Consolide les transactions similaires et supprime les doublons
"""

import json
import numpy as np
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Import absolu pour éviter les problèmes de module relatif
try:
    from semantic_search import SemanticSearch
except ImportError as e:
    raise ImportError(f"semantic_search non disponible. Vérifiez que l'installation est complète: {e}")


class MemoryCompressor:
    """Module de compression de mémoire pour DARYL"""
    
    def __init__(self, shards_directory="memory/shards", similarity_threshold=0.9, max_age_days=90):
        """
        Initialise le module de compression
        
        Args:
            shards_directory: Répertoire des shards JSON
            similarity_threshold: Seuil de similarité cosinus (0.9)
            max_age_days: Âge maximum des transactions en jours
        """
        self.shards_dir = Path(shards_directory)
        self.similarity_threshold = similarity_threshold
        self.max_age = max_age_days
        self.max_age_days = max_age_days
        self.semantic_search = SemanticSearch(shards_directory=str(self.shards_dir), threshold=similarity_threshold, top_k=10)
        self.shards_data = {}
        self.stats = {
            "total_transactions": 0,
            "consolidated_transactions": 0,
            "removed_duplicates": 0,
            "expired_transactions": 0,
            "last_compression": None
        }
        self._load_all_shards()

    def _load_all_shards(self):
        """Charge en mémoire la liste des shards disponibles."""
        self.shards_data = {}
        if not self.shards_dir.exists():
            return

        for shard_file in self.shards_dir.glob("*.json"):
            try:
                with open(shard_file, 'r', encoding='utf-8') as f:
                    self.shards_data[shard_file.stem] = json.load(f)
            except Exception as e:
                print(f"⚠️ Shard ignoré ({shard_file.name}): {e}", file=sys.stderr)
    
    def _load_shard_data(self, shard_id: str) -> Optional[Dict]:
        """
        Charge les données d'un shard
        
        Args:
            shard_id: ID du shard
            
        Returns:
            Données du shard ou None
        """
        shard_path = self.shards_dir / f"{shard_id}.json"
        
        if not shard_path.exists():
            return None
        
        try:
            with open(shard_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"❌ Erreur chargement shard {shard_id}: {e}", file=sys.stderr)
            return None
    
    def _find_similar_transactions(self, shard_data: Dict, transaction_id: str, top_k: int = 5) -> List[Dict]:
        """
        Trouve des transactions similaires dans le shard
        
        Args:
            shard_data: Données du shard
            transaction_id: ID de la transaction de référence
            top_k: Nombre de résultats similaires
            
        Returns:
            Liste des transactions similaires
        """
        # Extraire le contenu de la transaction de référence
        transactions = shard_data.get("transactions", [])
        target_tx = None
        
        for tx in transactions:
            if tx.get("id") == transaction_id:
                target_tx = tx
                break
        
        if target_tx is None:
            return []
        
        if "content" not in target_tx:
            return []
        
        # Utiliser le module SemanticSearch pour trouver des transactions similaires
        similar_results = self.semantic_search.search(target_tx["content"], shard_id=shard_data.get("config", {}).get("id", ""))
        
        # Filtrer les résultats (exclure la transaction elle-même)
        filtered = []
        for r in similar_results:
            if r.get("transaction_id") != transaction_id:
                filtered.append(r)
        
        return filtered[:top_k]
    
    def _consolidate_transactions(self, shard_id: str, transaction_ids: List[str]) -> Optional[Dict]:
        """
        Consolide plusieurs transactions en une seule
        
        Args:
            shard_id: ID du shard
            transaction_ids: IDs des transactions à consolider
            
        Returns:
            Transaction consolidée ou None
        """
        shard_data = self._load_shard_data(shard_id)
        
        if shard_data is None:
            return None
        
        transactions = shard_data.get("transactions", [])
        
        # Filtrer les transactions à consolider
        target_transactions = []
        for tx in transactions:
            if tx.get("id") in transaction_ids:
                target_transactions.append(tx)
        
        if len(target_transactions) < 2:
            return None
        
        # Créer une transaction consolidée
        contents = [tx.get("content", "") for tx in target_transactions]
        importance_scores = [tx.get("importance", 0.5) for tx in target_transactions]
        sources = list(set([tx.get("source", "unknown") for tx in target_transactions]))
        
        # Prendre le contenu le plus long comme base
        base_content = max(contents, key=len)
        
        consolidated_tx = {
            "id": f"consolidated_{shard_id}_{datetime.now().timestamp()}",
            "content": f"[Consolidated: {len(transaction_ids)} items] {base_content}",
            "source": "memory_compressor",
            "importance": max(importance_scores),
            "timestamp": datetime.now().isoformat(),
            "consolidated_from": transaction_ids,
            "consolidated_count": len(transaction_ids),
            "cross_refs": []
        }
        
        return consolidated_tx
    
    def compress_shard(self, shard_id: str, force: bool = False) -> Dict[str, int]:
        """
        Compress un shard (suppression des doublons, consolidation)
        
        Args:
            shard_id: ID du shard à compresser
            force: Force la compression même si pas de doublons
            
        Returns:
            Dictionnaire avec stats de compression
        """
        shard_data = self._load_shard_data(shard_id)
        
        if shard_data is None:
            return {"error": "Shard not found"}
        
        transactions = shard_data.get("transactions", [])
        removed_duplicates = []
        consolidated_count = 0
        
        # Trouver les doublons (contenus identiques)
        seen_contents = set()
        unique_transactions = []
        
        for tx in transactions:
            content = tx.get("content", "").strip().lower()
            content_hash = content
            
            if content_hash in seen_contents:
                removed_duplicates.append(tx.get("id"))
                continue
            
            seen_contents.add(content_hash)
            unique_transactions.append(tx)

        # Considérer la déduplication comme une forme de consolidation.
        if removed_duplicates:
            consolidated_count += 1
        
        # Consolider les transactions similaires
        for i, tx in enumerate(unique_transactions):
            if "embedding" not in tx:
                continue
            
            similar = self._find_similar_transactions(shard_data, tx["id"], top_k=3)
            
            if len(similar) >= 1:
                # Trouver les transactions similaires
                similar_ids = [tx.get("id")] + [s.get("transaction_id") for s in similar]
                similar_ids = [sid for sid in similar_ids if sid]
                
                # Consolidater
                consolidated = self._consolidate_transactions(shard_id, similar_ids)
                
                if consolidated:
                    # Marquer les transactions originales pour suppression
                    for tx in unique_transactions:
                        if tx.get("id") in similar_ids:
                            tx["consolidated_into"] = consolidated["id"]
                    
                    # Ajouter la transaction consolidée
                    unique_transactions.append(consolidated)
                    consolidated_count += 1
                    
                    # Sortir pour éviter de reconsolider
                    break
        
        # Supprimer les transactions marquées pour consolidation
        final_transactions = []
        for tx in unique_transactions:
            if "consolidated_into" not in tx:
                final_transactions.append(tx)
        
        # Sauvegarder
        shard_data["transactions"] = final_transactions
        shard_data["metadata"] = shard_data.get("metadata", {})
        shard_data["metadata"]["last_compression"] = datetime.now().isoformat()
        shard_data["metadata"]["consolidated_count"] = consolidated_count
        
        self._save_shard(shard_id, shard_data)
        
        return {
            "removed_duplicates": len(removed_duplicates),
            "consolidated_transactions": consolidated_count,
            "total_before": len(transactions),
            "total_after": len(final_transactions)
        }
    
    def _save_shard(self, shard_id: str, shard_data: Dict):
        """
        Sauvegarde les données d'un shard
        
        Args:
            shard_id: ID du shard
            shard_data: Données du shard
        """
        self.shards_dir.mkdir(parents=True, exist_ok=True)
        shard_path = self.shards_dir / f"{shard_id}.json"
        
        try:
            with open(shard_path, 'w', encoding='utf-8') as f:
                json.dump(shard_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erreur sauvegarde shard {shard_id}: {e}", file=sys.stderr)
    
    def compress_all_shards(self, force: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Compress tous les shards
        
        Args:
            force: Force la compression même si pas de doublons
            
        Returns:
            Dictionnaire avec stats par shard
        """
        shards_path = self.shards_dir
        
        if not shards_path.exists():
            return {"error": "Shards directory not found"}
        
        results = {}
        
        # Parcourir tous les fichiers .json
        for shard_file in shards_path.glob("*.json"):
            shard_id = shard_file.stem
            
            # Compresser le shard
            compression_result = self.compress_shard(shard_id, force=force)
            
            if "error" not in compression_result:
                results[shard_id] = compression_result
        
        # Mettre à jour les stats globales
        self.stats["total_transactions"] = sum(r.get("total_before", 0) for r in results.values())
        self.stats["consolidated_transactions"] = sum(r.get("consolidated_transactions", 0) for r in results.values())
        self.stats["removed_duplicates"] = sum(r.get("removed_duplicates", 0) for r in results.values())
        self.stats["last_compression"] = datetime.now().isoformat()
        
        return results
    
    def get_compression_stats(self) -> Dict[str, int]:
        """
        Retourne les statistiques de compression
        
        Returns:
            Dictionnaire avec les stats
        """
        return self.stats


if __name__ == "__main__":
    # Test du module de compression
    compressor = MemoryCompressor(shards_directory="memory/shards", similarity_threshold=0.9, max_age_days=90)
    
    print("🧪 Test du module MemoryCompressor")
    print(f"   Seuil de similarité: {compressor.similarity_threshold}")
    print(f"   Âge maximum: {compressor.max_age_days} jours")
    print()
    
    # Charger un shard test
    test_shard = compressor._load_shard_data("shard_projects")
    
    if test_shard:
        print(f"📁 Shard chargé: {test_shard.get('config', {}).get('name', 'unknown')}")
        print(f"   Transactions: {len(test_shard.get('transactions', []))}")
        print()
        
        # Test de compression
        print("🗜️ Compression du shard...")
        result = compressor.compress_shard("shard_projects", force=True)
        
        if "error" not in result:
            print(f"   Doublons supprimés: {result['removed_duplicates']}")
            print(f"   Transactions consolidées: {result['consolidated_transactions']}")
            print(f"   Avant compression: {result['total_before']}")
            print(f"   Après compression: {result['total_after']}")
        else:
            print(f"   ❌ Erreur: {result['error']}", file=sys.stderr)
    else:
        print("❌ Shard test non trouvé", file=sys.stderr)
    
    print()
    print("📊 Statistiques globales:")
    stats = compressor.get_compression_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
