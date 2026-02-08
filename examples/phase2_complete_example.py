#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemple complet d'utilisation de Phase 2 (Semantic Search & Core Features)
Démontre l'intégration de tous les modules:
- EmbeddingService (génération d'embeddings)
- SemanticSearch (recherche vectorielle et hybride)
- MemoryCompressor (compression de mémoire)
- MemoryCleaner (nettoyage TTL)
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    from embedding_service import EmbeddingService
    from semantic_search import SemanticSearch
    from memory_compressor import MemoryCompressor
    from memory_cleaner import MemoryCleaner
except ImportError as e:
    print(f"❌ Erreur import des modules: {e}")
    sys.exit(1)

def print_separator():
    """Affiche un séparateur visuel"""
    print("=" * 70)

def print_section(title):
    """Affiche un titre de section"""
    print(f"\n📦 {title}")
    print("-" * 70)

def print_success(message):
    """Affiche un message de succès"""
    print(f"✅ {message}")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"❌ {message}")

def print_info(message):
    """Affiche un message d'information"""
    print(f"ℹ️  {message}")

# Configuration
SHARDS_DIR = "memory/shards"
EXAMPLE_OUTPUT_DIR = "examples/output"

def main():
    print_separator()
    print("🚀 EXEMPLE COMPLET PHASE 2 - DARYL Sharding Memory")
    print_separator()
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Répertoire shards: {SHARDS_DIR}")
    
    # Créer le répertoire d'output
    from pathlib import Path
    output_dir = Path(EXAMPLE_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print_section("Initialisation des services")
    
    # 1. Initialiser EmbeddingService
    print_info("Chargement du modèle d'embeddings...")
    embedding_service = EmbeddingService(model_name="all-MiniLM-L6-v2")
    print_success(f"Modèle chargé: {embedding_service.model_name}")
    
    # 2. Initialiser SemanticSearch
    print_info("Initialisation du module de recherche sémantique...")
    semantic_search = SemanticSearch(shards_directory=SHARDS_DIR, threshold=0.7, top_k=5)
    print_success("Module de recherche initialisé")
    
    # 3. Initialiser MemoryCompressor
    print_info("Initialisation du module de compression de mémoire...")
    memory_compressor = MemoryCompressor(shards_directory=SHARDS_DIR, similarity_threshold=0.9)
    print_success("Module de compression initialisé")
    
    # 4. Initialiser MemoryCleaner
    print_info("Initialisation du module de nettoyage TTL...")
    memory_cleaner = MemoryCleaner(shards_directory=SHARDS_DIR)
    print_success("Module de nettoyage initialisé")
    
    print_section("Données de test")
    
    # Créer des transactions de test dans tous les shards
    test_transactions = {
        "shard_projects": [
            {
                "id": f"tx_proj_1_{datetime.now().timestamp()}",
                "content": "Projet actif: Finaliser documentation API Phase 2",
                "source": "example",
                "importance": 0.9,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                "id": f"tx_proj_2_{datetime.now().timestamp()}",
                "content": "Projet: Implémenter recherche sémantique avec embeddings",
                "source": "example",
                "importance": 0.8,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
            },
            {
                "id": f"tx_proj_3_{datetime.now().timestamp()}",
                "content": "Projet: Créer Web UI pour visualiser les shards",
                "source": "example",
                "importance": 0.7,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "shard_insights": [
            {
                "id": f"tx_ins_1_{datetime.now().timestamp()}",
                "content": "Insight: Les embeddings sentence-transformers fournissent une qualité de recherche excellente",
                "source": "example",
                "importance": 0.8,
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "id": f"tx_ins_2_{datetime.now().timestamp()}",
                "content": "Pattern: La compression de mémoire réduit la taille des données sans perte critique d'information",
                "source": "example",
                "importance": 0.9,
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat()
            }
        ],
        "shard_technical": [
            {
                "id": f"tx_tech_1_{datetime.now().timestamp()}",
                "content": "Architecture: Le système de sharding utilise des shards spécialisés pour optimiser la recherche",
                "source": "example",
                "importance": 0.7,
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat()
            },
            {
                "id": f"tx_tech_2_{datetime.now().timestamp()}",
                "content": "Technique: Utiliser la similarité cosinus pour la recherche vectorielle (score > 0.7)",
                "source": "example",
                "importance": 0.8,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "shard_strategy": [
            {
                "id": f"tx_strat_1_{datetime.now().timestamp()}",
                "content": "Stratégie: Phase 2 se concentre sur Semantic Search + Compression + TTL",
                "source": "example",
                "importance": 0.9,
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat()
            }
        ],
        "shard_people": [
            {
                "id": f"tx_ppl_1_{datetime.now().timestamp()}",
                "content": "Contact: L'équipe de développement est @buraluxtr sur Moltbook",
                "source": "example",
                "importance": 0.6,
                "timestamp": (datetime.now() - timedelta(days=7)).isoformat()
            }
        ]
    }
    
    # Créer les fichiers shards si nécessaires
    from pathlib import Path
    shards_path = Path(SHARDS_DIR)
    shards_path.mkdir(parents=True, exist_ok=True)
    
    print_info(f"Création des shards de test dans {SHARDS_DIR}")
    
    for shard_id, transactions in test_transactions.items():
        shard_file = shards_path / f"{shard_id}.json"
        
        # Structure du fichier shard
        shard_data = {
            "config": {
                "id": shard_id,
                "name": shard_id.replace("shard_", "").capitalize() + " Shard",
                "domain": shard_id.replace("shard_", ""),
                "keywords": {
                    "shard_projects": ["projet", "task", "goal", "objective"],
                    "shard_insights": ["leçon", "pattern", "insight", "décision"],
                    "shard_technical": ["architecture", "framework", "code", "protocol", "shard", "layer", "pillar"],
                    "shard_strategy": ["stratégie", "vision", "priority", "tendance", "trend"],
                    "shard_people": ["@", "contact", "person", "expert", "builder", "relation"]
                },
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "version": "1.0",
                    "description": f"{shard_id} Shard for DARYL Sharding Memory"
                }
            },
            "transactions": transactions
        }
        
        # Sauvegarder le shard
        with open(shard_file, 'w', encoding='utf-8') as f:
            json.dump(shard_data, f, indent=2, ensure_ascii=False)
        
        print_success(f"  {shard_id}: {len(transactions)} transactions créées")
    
    print_section("1. Génération d'embeddings")
    
    # Générer les embeddings pour toutes les transactions de test
    all_embeddings = {}
    total_transactions = 0
    
    for shard_id, transactions in test_transactions.items():
        shard_embeddings = {}
        
        for tx in transactions:
            content = tx.get("content", "")
            
            # Générer l'embedding
            embedding = embedding_service.generate_embedding(content)
            
            if embedding is not None:
                # Ajouter l'embedding à la transaction
                tx["embedding"] = embedding
                shard_embeddings[tx["id"]] = embedding
                total_transactions += 1
            else:
                print_error(f"  Erreur génération embedding pour {tx['id']}")
        
        if shard_embeddings:
            all_embeddings[shard_id] = shard_embeddings
            print_success(f"  {shard_id}: {len(shard_embeddings)} embeddings générées")
    
    # Sauvegarder les shards avec embeddings
    for shard_id, transactions in test_transactions.items():
        shard_file = shards_path / f"{shard_id}.json"
        
        with open(shard_file, 'w', encoding='utf-8') as f:
            json.dump({
                "config": json.load(open(shard_file)).get("config"),
                "transactions": transactions
            }, f, indent=2, ensure_ascii=False)
    
    print_success(f"Total: {total_transactions} embeddings générées")
    
    # Stats du cache d'embeddings
    cache_stats = embedding_service.get_cache_stats()
    print_info(f"Cache size: {cache_stats['cache_size']}")
    print_info(f"Model: {cache_stats['model_name']}")
    print_info(f"Embedding dimension: {cache_stats['embedding_dimension']}")
    
    print_section("2. Recherche sémantique (Vectorielle)")
    
    # Recherche sémantique pure
    query = "agents avec mémoire persistante et recherche sémantique"
    print_info(f"Requête: {query}")
    
    semantic_results = semantic_search.search(query, shard_id=None)
    
    print_success(f"Résultats sémantiques: {len(semantic_results)}")
    for i, r in enumerate(semantic_results[:3], 1):
        print(f"  {i}. [{r['shard_name']}] Score: {r['similarity']:.3f} - {r['content'][:60]}...")
    
    # Recherche hybride (sémantique + mots-clés)
    print_info("Recherche hybride (sémantique + mots-clés)...")
    hybrid_results = semantic_search.hybrid_search(query, shard_id=None)
    
    print_success(f"Résultats hybrides: {len(hybrid_results)}")
    for i, r in enumerate(hybrid_results[:3], 1):
        print(f"  {i}. [{r['shard_name']}] Score hybride: {r['hybrid_score']:.3f} - {r['content'][:60]}...")
    
    print_section("3. Compression de mémoire")
    
    # Trouver les doublons dans shard_projects
    print_info("Recherche de doublons dans shard_projects...")
    shard_id = "shard_projects"
    
    compression_result = memory_compressor.compress_shard(shard_id, force=True)
    
    if "error" not in compression_result:
        print_success(f"Doublons supprimés: {compression_result.get('removed_duplicates', 0)}")
        print_success(f"Transactions consolidées: {compression_result.get('consolidated_transactions', 0)}")
        print_success(f"Avant compression: {compression_result.get('total_before', 0)} transactions")
        print_success(f"Après compression: {compression_result.get('total_after', 0)} transactions")
        print_success(f"Réduction: {100 * (1 - compression_result.get('total_after', 1) / compression_result.get('total_before', 1)):.1f}%")
    else:
        print_error(f"Erreur compression: {compression_result.get('error', 'Unknown')}")
    
    print_section("4. Nettoyage TTL")
    
    # Vérifier les transactions expirées
    print_info("Vérification des transactions expirées...")
    
    # Nettoyer shard_projects (TTL: 30 jours)
    cleanup_result = memory_cleaner.cleanup_expired_transactions("shard_projects", dry_run=True)
    
    if "error" not in cleanup_result:
        print_success(f"Transactions expirées: {cleanup_result.get('expired_transactions', 0)}")
        print_success(f"Transactions conservées: {cleanup_result.get('kept_transactions', 0)}")
        print_success(f"Dry run: {cleanup_result.get('dry_run', False)}")
    else:
        print_error(f"Erreur nettoyage TTL: {cleanup_result.get('error', 'Unknown')}")
    
    # Nettoyer shard_technical (TTL: 180 jours)
    cleanup_result = memory_cleaner.cleanup_expired_transactions("shard_technical", dry_run=True)
    
    if "error" not in cleanup_result:
        print_success(f"Transactions expirées: {cleanup_result.get('expired_transactions', 0)}")
        print_success(f"Transactions conservées: {cleanup_result.get('kept_transactions', 0)}")
    else:
        print_error(f"Erreur nettoyage TTL: {cleanup_result.get('error', 'Unknown')}")
    
    # Nettoyage complet (dry run)
    print_info("Nettoyage complet de tous les shards (dry run)...")
    cleanup_all_results = memory_cleaner.run_cleanup_all_shards(dry_run=True)
    
    if "error" not in cleanup_all_results:
        print_success(f"Total transactions expirées: {sum(v.get('expired_transactions', 0) for v in cleanup_all_results.values())}")
        print_success(f"Total transactions supprimées pour limites: {sum(v.get('removed_transactions', 0) for v in cleanup_all_results.values())}")
    else:
        print_error("Erreur nettoyage complet")
    
    print_section("Résultats globaux")
    
    # Stats de compression
    compression_stats = memory_compressor.get_compression_stats()
    print_info("Compression:")
    print(f"  Transactions consolidées: {compression_stats.get('consolidated_transactions', 0)}")
    print(f"  Doublons supprimés: {compression_stats.get('removed_duplicates', 0)}")
    
    # Stats de recherche sémantique
    search_stats = semantic_search.get_search_stats()
    print_info("Recherche sémantique:")
    print(f"  Total shards: {search_stats.get('total_shards', 0)}")
    print(f"  Total transactions: {search_stats.get('total_transactions', 0)}")
    print(f"  Total embeddings: {search_stats.get('total_embeddings', 0)}")
    print(f"  Cache size: {search_stats.get('cache_size', 0)}")
    print(f"  Model: {search_stats.get('model_name', '')}")
    print(f"  Embedding dimension: {search_stats.get('embedding_dimension', 0)}")
    
    # Stats de nettoyage TTL
    cleanup_stats = memory_cleaner.get_cleanup_stats()
    print_info("Nettoyage TTL:")
    print(f"  Total shards: {cleanup_stats.get('total_shards', 0)}")
    print(f"  Transactions expirées: {cleanup_stats.get('expired_transactions', 0)}")
    print(f"  Transactions supprimées pour limites: {cleanup_stats.get('archived_transactions', 0)}")
    print(f"  Dernier nettoyage: {cleanup_stats.get('last_cleanup', 'N/A')}")
    
    print_separator()
    print_success("Exemple complet terminé avec succès !")
    print_info("Fichiers de test créés dans memory/shards/")
    print_info("Output sauvegardé dans examples/output/")
    print_separator()
    print("📚 Pour voir les résultats détaillés:")
    print("   1. Vérifiez les fichiers shards dans memory/shards/")
    print("   2. Les embeddings sont intégrées dans les transactions")
    print("   3. Recherche sémantique opérationnelle")
    print("   4. Compression et nettoyage TTL fonctionnels")
    print_separator()
    
    # Sauvegarder le rapport
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_transactions": total_transactions,
        "embeddings_generated": total_transactions,
        "semantic_search_results": len(semantic_results),
        "hybrid_search_results": len(hybrid_results),
        "compression_result": compression_result,
        "cleanup_result": cleanup_all_results,
        "cache_stats": cache_stats,
        "search_stats": search_stats,
        "cleanup_stats": cleanup_stats
    }
    
    report_file = output_dir / "phase2_example_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print_success(f"Rapport sauvegardé: {report_file}")
    print_separator()
    return 0

if __name__ == "__main__":
    sys.exit(main())
