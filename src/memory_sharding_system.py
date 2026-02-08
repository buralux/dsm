#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Architecture de Sharding pour la Mémoire de DARYL v2.0
Partitionnement de la mémoire par domaine pour une efficacité accrue
Améliorations:
- Détection automatique des cross-references entre shards
- Gestion des connexions entre shards
- Intégration Phase 2: Semantic Search, Memory Compressor, Memory Cleaner
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from embedding_service import EmbeddingService
    from semantic_search import SemanticSearch
    from memory_compressor import MemoryCompressor
    from memory_cleaner import MemoryCleaner
except ImportError:
    raise ImportError("Phase 2 modules not available. Vérifiez l'installation.")

# Configuration
MEMORY_DIR = Path("/home/buraluxtr/clawd/memory")
SHARDS_DIR = MEMORY_DIR / "shards"
SHARD_CONFIG_FILE = SHARDS_DIR / "shard_config.json"

# Définition des shards par domaine
SHARD_DOMAINS = {
    "projects": {
        "name": "Projets en cours",
        "description": "Projets actifs, tâches en cours, objectifs",
        "keywords": ["projet", "task", "project", "todo", "goal", "objective"]
    },
    "insights": {
        "name": "Insights et Leçons",
        "description": "Leçons apprises, patterns identifiés, décisions importantes",
        "keywords": ["leçon", "lesson", "pattern", "insight", "décision", "decision"]
    },
    "people": {
        "name": "Personnes et Relations",
        "description": "Contacts, experts, builders, relations importantes",
        "keywords": ["@", "contact", "person", "expert", "builder", "relation"]
    },
    "technical": {
        "name": "Technique et Architecture",
        "description": "Architecture, code, protocoles, frameworks",
        "keywords": ["architecture", "framework", "code", "protocol", "shard", "layer", "pillar"]
    },
    "strategy": {
        "name": "Stratégie et Vision",
        "description": "Vision à long terme, priorités, stratégies de contenu",
        "keywords": ["stratégie", "vision", "priority", "tendance", "trend"]
    }
}

class MemoryShard:
    """Représente un shard de mémoire"""
    
    def __init__(self, shard_id, domain):
        self.shard_id = shard_id
        self.domain = domain
        self.config = SHARD_DOMAINS[domain]
        self.transactions = []
        self.metadata = {
            "version": "2.0",
            "importance_score": 0.0,
            "last_updated": None
        }
        self._load()
    
    def _load(self):
        """Charge les transactions depuis le fichier JSON"""
        shard_path = SHARDS_DIR / f"{self.shard_id}.json"
        
        if not shard_path.exists():
            # Créer le shard avec la configuration par défaut
            self.metadata["created_at"] = datetime.now().isoformat()
            self._save()
            return
        
        try:
            with open(shard_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.transactions = data.get("transactions", [])
                self.metadata.update(data.get("metadata", {}))
        except Exception as e:
            print(f"❌ Error loading shard {self.shard_id}: {e}")
    
    def add_transaction(self, content, source="manual", importance=0.5, cross_refs=None):
        """
        Ajoute une transaction (mémoire) à ce shard
        
        Args:
            content: Contenu de la mémoire
            source: Source de la mémoire (manual, system, user)
            importance: Importance de la mémoire (0.0-1.0)
            cross_refs: Liste des références cross-shard
        """
        transaction = {
            "id": f"{self.shard_id}_{len(self.transactions)}_{datetime.now().timestamp()}",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "importance": importance,
            "cross_refs": cross_refs or []
        }
        self.transactions.append(transaction)
        self._update_importance()
        self._save()
        return transaction["id"]
    
    def query(self, query_text, limit=10):
        """
        Recherche dans ce shard
        
        Args:
            query_text: Texte de la recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des résultats
        """
        query_lower = query_text.lower()
        results = []
        
        for t in reversed(self.transactions):
            if query_lower in t["content"].lower():
                results.append(t)
                if len(results) >= limit:
                    break
        
        return results
    
    def _update_importance(self):
        """
        Met à jour le score d'importance du shard
        Basé sur le nombre de transactions et leur importance moyenne
        """
        if not self.transactions:
            return
        
        # Moyenne d'importance des transactions
        avg_importance = sum(t["importance"] for t in self.transactions) / len(self.transactions)
        
        # Bonus pour les shards avec beaucoup de transactions (jusqu'à 100 tx)
        transaction_count = min(len(self.transactions), 100)
        count_bonus = transaction_count / 100.0  # 0.0 à 1.0
        
        # Score d'importance combiné
        self.metadata["importance_score"] = avg_importance + count_bonus
        self.metadata["last_updated"] = datetime.now().isoformat()
    
    def _save(self):
        """Sauvegarde les données du shard"""
        shard_path = SHARDS_DIR / f"{self.shard_id}.json"
        
        data = {
            "config": {
                "id": self.shard_id,
                "name": self.config["name"],
                "domain": self.domain,
                "keywords": self.config["keywords"],
                "created_at": self.metadata.get("created_at", datetime.now().isoformat())
            },
            "transactions": self.transactions,
            "metadata": self.metadata
        }
        
        try:
            with open(shard_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving shard {self.shard_id}: {e}")


class ShardRouter:
    """Routeur de shards - Gestion intelligente de la mémoire"""
    
    def __init__(self):
        self.shards = {}
        self.shards_config = {
            "routing_config": {
                "importance_threshold": 0.6,
                "bonus_frequent_shards": 0.5,
                "bonus_keywords": 1.0,
                "max_cross_refs": 3,
                "whitelist_patterns": [
                    r"voir shard\s+(\w+)",
                    r"shard:\s*(\w+)"
                r"shard\s*(\w+)"
                r"@\s*(\w+)"
                r"connecté avec\s*@\s*(\w+)"
                r"relation\s*@\s*(\w+)"
                r"expert\s*@\s*(\w+)"
                    r"builder\s*@\s*(\w+)"
                r"contact\s*@\s*(\w+)"
                r"discussion\s*avec\s*@\s*(\w+)"
                    r"réponse\s*à\s*@\s*(\w+)"
                ]
            }
        }
        self._load_all_shards()
        
        # Phase 2: Initialiser les services
        try:
            self.embedding_service = EmbeddingService()
            self.semantic_search = SemanticSearch(shards_directory=str(SHARDS_DIR))
            self.memory_compressor = MemoryCompressor(shards_directory=str(SHARDS_DIR), similarity_threshold=0.9)
            self.memory_cleaner = MemoryCleaner(shards_directory=str(SHARDS_DIR))
            print("✅ Phase 2 services initialized")
        except Exception as e:
            print(f"⚠️ Phase 2 services not available: {e}")
            self.embedding_service = None
            self.semantic_search = None
            self.memory_compressor = None
            self.memory_cleaner = None
    
    def _load_all_shards(self):
        """Charge tous les shards depuis les fichiers JSON"""
        if not SHARDS_DIR.exists():
            SHARDS_DIR.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created shards directory: {SHARDS_DIR}")
        
        shard_files = list(SHARDS_DIR.glob("*.json"))
        print(f"📁 Loading {len(shard_files)} shards from {SHARDS_DIR}")
        
        for shard_file in shard_files:
            shard_id = shard_file.stem
            domain = shard_id.replace("shard_", "")
            try:
                with open(shard_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Créer l'instance MemoryShard
                    shard = MemoryShard(shard_id, domain)
                    shard.transactions = data.get("transactions", [])
                    shard.metadata.update(data.get("metadata", {}))
                    
                    self.shards[shard_id] = shard
                    print(f"  ✅ {shard_id}: {len(shard.transactions)} transactions")
            except Exception as e:
                print(f"  ❌ {shard_id}: Error loading - {e}")
        
        print(f"📊 Total shards loaded: {len(self.shards)}")
    
    def _find_best_shard_for_content(self, content):
        """
        Trouve le meilleur shard pour un contenu
        
        Args:
            content: Contenu à classifier
            
        Returns:
            (best_shard_id, cross_refs)
        """
        content_lower = content.lower()
        shard_scores = {}
        
        for shard_id, shard in self.shards.items():
            score = 0.0
            
            # Score basé sur les mots-clés du shard
            keywords = shard.config.get("keywords", [])
            keyword_matches = sum(1 for kw in keywords if kw.lower() in content_lower)
            score += keyword_matches * self.shards_config["routing_config"]["bonus_keywords"]
            
            # Bonus d'importance pour les shards fréquemment utilisés
            score += shard.metadata.get("importance_score", 0) * self.shards_config["routing_config"]["bonus_frequent_shards"]
            
            shard_scores[shard_id] = score
        
        # Trouver le shard avec le score le plus élevé
        if not shard_scores:
            return ("shard_technical", [])  # Défaut
        
        best_shard_id = max(shard_scores, key=lambda x: shard_scores[x])
        best_score = shard_scores[best_shard_id]
        
        # Filtrer par seuil d'importance
        threshold = self.shards_config["routing_config"]["importance_threshold"]
        if best_score < threshold and "shard_projects" in shard_scores:
            if shard_scores["shard_projects"] >= threshold:
                best_shard_id = "shard_projects"
        
        # Détecter les cross-references
        cross_refs = self._detect_cross_references(content)
        
        # Limiter à max_cross_refs
        max_refs = self.shards_config["routing_config"]["max_cross_refs"]
        cross_refs = cross_refs[:max_refs]
        
        return (best_shard_id, cross_refs)
    
    def _detect_cross_references(self, content):
        """
        Détecte les cross-references dans le contenu
        
        Args:
            content: Contenu à analyser
            
        Returns:
            Liste des shard_id référencés
        """
        cross_refs = []
        patterns = self.shards_config["routing_config"]["whitelist_patterns"]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extraire l'ID du shard (groupe 1: \\w+)
                shard_match = re.search(r'(shard_|\w+)', match)
                if shard_match:
                    shard_id = shard_match.group(1)
                    
                    # Normaliser l'ID du shard
                    shard_id = shard_id.lower()
                    
                    # Vérifier si c'est un shard valide
                    for valid_shard_id in self.shards.keys():
                        if valid_shard_id.lower() == shard_id:
                            cross_refs.append(valid_shard_id)
                            break
        
        # Supprimer les doublons
        cross_refs = list(set(cross_refs))
        
        return cross_refs
    
    def add_memory(self, content, source="manual", importance=0.5, shard_id=None):
        """
        Ajoute une mémoire avec routage automatique
        
        Args:
            content: Contenu de la mémoire
            source: Source de la mémoire (manual, system, user)
            importance: Importance de la mémoire (0.0-1.0)
            shard_id: ID du shard cible (optionnel)
            
        Returns:
            ID de la transaction
        """
        # Trouver le meilleur shard si non spécifié
        if shard_id is None:
            shard_id, cross_refs = self._find_best_shard_for_content(content)
        else:
            cross_refs = []
        
        # Vérifier que le shard existe
        if shard_id not in self.shards:
            raise ValueError(f"Shard not found: {shard_id}")
        
        # Ajouter au shard
        shard = self.shards[shard_id]
        tx_id = shard.add_transaction(content, source=source, importance=importance, cross_refs=cross_refs)
        
        return tx_id
    
    def query(self, query_text, limit=10, shard_id=None):
        """
        Recherche dans les shards
        
        Args:
            query_text: Texte de la recherche
            limit: Nombre maximum de résultats
            shard_id: ID du shard cible (optionnel)
            
        Returns:
            Liste des résultats
        """
        if shard_id:
            # Recherche dans un shard spécifique
            if shard_id not in self.shards:
                return []
            shard = self.shards[shard_id]
            results = shard.query(query_text, limit=limit)
            for r in results:
                r["shard_id"] = shard_id
                r["shard_name"] = shard.config["name"]
            return results
        else:
            # Recherche dans tous les shards (priorité par importance)
            all_results = []
            for sid, shard in sorted(self.shards.items(), key=lambda x: x[1].metadata.get("importance_score", 0), reverse=True):
                shard_results = shard.query(query_text, limit=limit)
                for r in shard_results:
                    r["shard_id"] = sid
                    r["shard_name"] = shard.config["name"]
                all_results.extend(shard_results)
            
            return all_results[:limit]
    
    def semantic_search(self, query_text, shard_id=None, top_k=5, threshold=0.7):
        """
        Recherche sémantique avec embeddings
        
        Args:
            query_text: Texte de la requête
            shard_id: ID du shard cible (optionnel)
            top_k: Nombre de résultats
            threshold: Seuil de similarité cosinus
            
        Returns:
            Liste des résultats
        """
        if self.semantic_search is None:
            print("❌ Semantic search not available")
            return []
        
        return self.semantic_search.search(query_text, shard_id=shard_id)
    
    def hybrid_search(self, query_text, shard_id=None, top_k=5, threshold=0.7):
        """
        Recherche hybride: sémantique + full-text (mots-clés)
        
        Args:
            query_text: Texte de la requête
            shard_id: ID du shard cible (optionnel)
            top_k: Nombre de résultats
            threshold: Seuil de similarité cosinus
            
        Returns:
            Liste des résultats
        """
        if self.semantic_search is None:
            print("❌ Semantic search not available")
            return []
        
        return self.semantic_search.hybrid_search(query_text, shard_id=shard_id)
    
    def compress_memory(self, shard_id=None, force=False):
        """
        Compress la mémoire (doublons, consolidation)
        
        Args:
            shard_id: ID du shard à compresser (optionnel)
            force: Force la compression même si pas de doublons
            
        Returns:
            Dictionnaire avec les stats de compression
        """
        if self.memory_compressor is None:
            print("❌ Memory compressor not available")
            return {"error": "Memory compressor not available"}
        
        if shard_id:
            # Compresser un shard spécifique
            return self.memory_compressor.compress_shard(shard_id, force=force)
        else:
            # Compresser tous les shards
            return self.memory_compressor.compress_all_shards(force=force)
    
    def cleanup_expired(self, shard_id=None, dry_run=False):
        """
        Nettoie les transactions expirées (TTL)
        
        Args:
            shard_id: ID du shard à nettoyer (optionnel)
            dry_run: Si True, ne supprime pas, seulement compte
            
        Returns:
            Dictionnaire avec les stats de nettoyage
        """
        if self.memory_cleaner is None:
            print("❌ Memory cleaner not available")
            return {"error": "Memory cleaner not available"}
        
        if shard_id:
            # Nettoyer un shard spécifique
            return self.memory_cleaner.cleanup_expired_transactions(shard_id, dry_run=dry_run)
        else:
            # Nettoyer tous les shards
            return self.memory_cleaner.run_cleanup_all_shards(dry_run=dry_run)
    
    def find_similar_transactions(self, transaction_id, shard_id, top_k=5):
        """
        Trouve des transactions similaires dans un shard
        
        Args:
            transaction_id: ID de la transaction de référence
            shard_id: ID du shard cible
            top_k: Nombre de résultats similaires
            
        Returns:
            Liste des transactions similaires
        """
        if self.semantic_search is None:
            print("❌ Semantic search not available")
            return []
        
        return self.semantic_search.find_similar_transactions(transaction_id, shard_id, top_k=top_k)
    
    def cross_shard_search(self, query_text):
        """
        Recherche avancée avec cross-references
        
        Args:
            query_text: Texte de la requête
            
        Returns:
            Liste des résultats triés
        """
        # 1. Recherche sémantique
        semantic_results = []
        if self.semantic_search:
            semantic_results = self.semantic_search.search(query_text)
        
        # 2. Recherche full-text
        text_results = []
        for shard_id, shard in self.shards.items():
            results = shard.query(query_text, limit=3)
            text_results.extend(results)
        
        # 3. Fusionner (déduplication)
        seen_ids = set()
        cross_shard_results = []
        
        # Ajouter les résultats sémantiques
        for r in semantic_results:
            if r["transaction_id"] not in seen_ids:
                cross_shard_results.append(r)
                seen_ids.add(r["transaction_id"])
        
        # Ajouter les résultats full-text (si pas déjà vus)
        for r in text_results:
            if r["transaction_id"] not in seen_ids:
                cross_shard_results.append(r)
                seen_ids.add(r["transaction_id"])
        
        # 4. Trier par similarité sémantique (prioritaire)
        cross_shard_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        return cross_shard_results[:10]
    
    def get_shard_status(self, shard_id):
        """
        Retourne le statut d'un shard
        
        Args:
            shard_id: ID du shard
            
        Returns:
            Dictionnaire avec le statut
        """
        if shard_id not in self.shards:
            return {"error": "Shard not found"}
        
        shard = self.shards[shard_id]
        
        return {
            "shard_id": shard_id,
            "domain": shard.domain,
            "name": shard.config["name"],
            "transactions_count": len(shard.transactions),
            "importance_score": shard.metadata.get("importance_score", 0),
            "last_updated": shard.metadata.get("last_updated", "N/A")
        }
    
    def get_all_shards_status(self):
        """
        Retourne le statut de tous les shards
        
        Returns:
            Liste des stats triées par importance
        """
        status = []
        for shard_id, shard in self.shards.items():
            status.append({
                "shard_id": shard_id,
                "domain": shard.domain,
                "name": shard.config["name"],
                "transactions_count": len(shard.transactions),
                "importance_score": shard.metadata.get("importance_score", 0),
                "last_updated": shard.metadata.get("last_updated", "N/A")
            })
        
        # Trier par importance score décroissant
        status.sort(key=lambda x: x["importance_score"], reverse=True)
        
        return status
    
    def export_shards_summary(self):
        """
        Exporte un résumé de tous les shards
        
        Returns:
            Dictionnaire avec le résumé
        """
        summary = {
            "exported_at": datetime.now().isoformat(),
            "total_shards": len(self.shards),
            "total_transactions": sum(len(s.transactions) for s in self.shards.values()),
            "domains_count": len(set(s.domain for s in self.shards.values())),
            "shards_status": self.get_all_shards_status(),
            "routing_config": self.shards_config["routing_config"]
        }
        
        # Sauvegarder le résumé
        summary_file = MEMORY_DIR / "shards_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary
    
    def get_all_shards(self):
        """
        Retourne tous les shards
        
        Returns:
            Dictionnaire {shard_id: MemoryShard}
        """
        return self.shards
    
    def get_shard_by_domain(self, domain):
        """
        Retourne les shards par domaine
        
        Args:
            domain: Domaine cible
            
        Returns:
            Liste des shards du domaine
        """
        return [shard for sid, shard in self.shards.items() if shard.domain == domain]


def main():
    """Point d'entrée principal"""
    # Créer les dossiers si nécessaires
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialiser le routeur de shards
    router = ShardRouter()
    
    print("🚀 DARYL Sharding Memory v2.0")
    print("📁 Répertoire shards:", SHARDS_DIR)
    print()
    print("✅ Phase 2 Integration:")
    print("   - EmbeddingService: {}".format("✅" if router.embedding_service else "❌"))
    print("   - SemanticSearch: {}".format("✅" if router.semantic_search else "❌"))
    print("   - MemoryCompressor: {}".format("✅" if router.memory_compressor else "❌"))
    print("   - MemoryCleaner: {}".format("✅" if router.memory_cleaner else "❌"))
    print()
    
    # Afficher le statut des shards
    print("📊 Shards Status:")
    for status in router.get_all_shards_status()[:5]:
        print(f"  • [{status['domain']}] {status['name']}: {status['transactions_count']} tx (score: {status['importance_score']:.2f})")
    print(f"  ... + {len(router.shards) - 5} more shards")
    print()
    
    # Exemple d'utilisation
    print("🔍 Exemple d'utilisation:")
    print("  # Ajouter une mémoire avec routage automatique")
    print("  tx_id = router.add_memory('Projet actif: Finaliser Phase 2', importance=0.8)")
    print()
    print("  # Recherche sémantique")
    print("  results = router.semantic_search('agents avec mémoire persistante')")
    print()
    print("  # Compression de mémoire")
    print("  compression_stats = router.compress_memory()")
    print()
    print("  # Nettoyage TTL")
    print("  cleanup_stats = router.cleanup_expired(dry_run=True)")
    print()
    
    # Exporter le résumé
    summary = router.export_shards_summary()
    print(f"📊 Résumé exporté: {len(summary['shards_status'])} shards, {summary['total_transactions']} transactions")
    print()
    print("✅ DARYL Sharding Memory v2.0 ready!")


if __name__ == "__main__":
    main()
