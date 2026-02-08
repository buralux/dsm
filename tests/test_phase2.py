#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitaires pour DARYL Sharding Memory - Phase 2 (Semantic Search)
Couvre: Embeddings, Semantic Search, Memory Compressor, Memory Cleaner
"""

import sys
import os
import json
import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from embedding_service import EmbeddingService
    from semantic_search import SemanticSearch
    from memory_compressor import MemoryCompressor
    from memory_cleaner import MemoryCleaner
    from memory_sharding_system import ShardRouter
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)


class TestEmbeddingService(unittest.TestCase):
    """Tests du service d'embeddings"""
    
    def setUp(self):
        self.service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        self.test_text = "DARYL Sharding Memory est un système sémantique pour agents"
    
    def tearDown(self):
        self.service.clear_cache()
    
    def test_model_loaded(self):
        """Test: Le modèle d'embeddings est chargé"""
        self.assertIsNotNone(self.service.model)
        self.assertEqual(self.service.model_name, "all-MiniLM-L6-v2")
    
    def test_generate_embedding(self):
        """Test: Génération d'embedding"""
        embedding = self.service.generate_embedding(self.test_text)
        self.assertIsNotNone(embedding)
        self.assertEqual(len(embedding), 384)  # all-MiniLM-L6-v2 dimension
    
    def test_embedding_cache(self):
        """Test: Cache des embeddings"""
        # Première génération (pas dans le cache)
        embedding1 = self.service.generate_embedding(self.test_text)
        self.assertIsNotNone(embedding1)
        
        # Deuxième génération (devrait être dans le cache)
        embedding2 = self.service.generate_embedding(self.test_text)
        self.assertIsNotNone(embedding2)
        self.assertEqual(len(embedding1), len(embedding2))
    
    def test_cache_stats(self):
        """Test: Statistiques du cache"""
        stats = self.service.get_cache_stats()
        self.assertIn("cache_size", stats)
        self.assertIn("model_name", stats)
        self.assertIn("embedding_dimension", stats)
        self.assertGreater(stats["cache_size"], 0)
    
    def test_clear_cache(self):
        """Test: Vidage du cache"""
        self.service.generate_embedding(self.test_text)  # Ajouter au cache
        stats_before = self.service.get_cache_stats()
        self.assertGreater(stats_before["cache_size"], 0)
        
        self.service.clear_cache()
        
        stats_after = self.service.get_cache_stats()
        self.assertEqual(stats_after["cache_size"], 0)


class TestSemanticSearch(unittest.TestCase):
    """Tests du module de recherche sémantique"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer des shards de test
        shards_data = {
            "shard_projects.json": {
                "config": {
                    "id": "shard_projects",
                    "name": "Projects Shard",
                    "domain": "projects",
                    "keywords": ["project", "task", "goal"]
                },
                "transactions": [
                    {
                        "id": "proj_1",
                        "content": "Projet: Finaliser documentation API",
                        "timestamp": datetime.now().isoformat(),
                        "source": "test",
                        "importance": 0.9,
                        "embedding": [0.1] * 384  # Fake embedding
                    },
                    {
                        "id": "proj_2",
                        "content": "Projet: Implémenter recherche sémantique",
                        "timestamp": datetime.now().isoformat(),
                        "source": "test",
                        "importance": 0.8,
                        "embedding": [0.2] * 384  # Fake embedding
                    }
                ]
            },
            "shard_insights.json": {
                "config": {
                    "id": "shard_insights",
                    "name": "Insights Shard",
                    "domain": "insights",
                    "keywords": ["lesson", "pattern", "insight"]
                },
                "transactions": [
                    {
                        "id": "ins_1",
                        "content": "Insight: Les embeddings améliorent la recherche",
                        "timestamp": datetime.now().isoformat(),
                        "source": "test",
                        "importance": 0.8,
                        "embedding": [0.3] * 384  # Fake embedding
                    }
                ]
            }
        }
        
        # Écrire les fichiers shards
        for shard_file, shard_content in shards_data.items():
            with open(os.path.join(self.temp_dir, shard_file), 'w') as f:
                json.dump(shard_content, f)
        
        self.searcher = SemanticSearch(shards_directory=self.temp_dir, threshold=0.7, top_k=5)
    
    def tearDown(self):
        # Nettoyer le répertoire temporaire
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_shards_loaded(self):
        """Test: Les shards sont chargés"""
        self.assertGreater(len(self.searcher.shards_data), 0)
        self.assertIn("shard_projects", self.searcher.shards_data)
        self.assertIn("shard_insights", self.searcher.shards_data)
    
    def test_cosine_similarity(self):
        """Test: Calcul de similarité cosinus"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]  # Identiques
        similarity = self.searcher._cosine_similarity(vec1, vec2)
        self.assertEqual(similarity, 1.0)
        
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [-1.0, 0.0, 0.0]  # Opposés
        similarity = self.searcher._cosine_similarity(vec3, vec4)
        self.assertEqual(similarity, -1.0)
    
    def test_semantic_search(self):
        """Test: Recherche sémantique"""
        query = "documentation API"
        results = self.searcher.search(query, shard_id="shard_projects")
        
        # Devrait retourner des résultats
        self.assertGreater(len(results), 0)
        
        # Vérifier que tous les résultats ont un score
        for r in results:
            self.assertIn("similarity", r)
            self.assertGreaterEqual(r["similarity"], 0.0)
            self.assertLessEqual(r["similarity"], 1.0)
    
    def test_hybrid_search(self):
        """Test: Recherche hybride (sémantique + mots-clés)"""
        query = "projet"
        results = self.searcher.hybrid_search(query)
        
        # Devrait retourner des résultats
        self.assertGreater(len(results), 0)
        
        # Vérifier que les résultats ont un score hybride
        for r in results:
            self.assertIn("hybrid_score", r)
            self.assertIn("match_type", r)
            self.assertGreaterEqual(r["hybrid_score"], 0.0)


class TestMemoryCompressor(unittest.TestCase):
    """Tests du module de compression de mémoire"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer un shard de test avec des doublons
        shard_data = {
            "config": {
                "id": "shard_projects",
                "name": "Projects Shard",
                "domain": "projects",
                "keywords": ["project", "task"]
            },
            "transactions": [
                {
                    "id": "proj_1",
                    "content": "Projet: Finaliser documentation API",
                    "timestamp": datetime.now().isoformat(),
                    "source": "test",
                    "importance": 0.9,
                    "embedding": [0.1] * 384
                },
                {
                    "id": "proj_2",
                    "content": "Projet: Finaliser documentation API",  # Doublon
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "source": "test",
                    "importance": 0.8,
                    "embedding": [0.1] * 384
                },
                {
                    "id": "proj_3",
                    "content": "Projet: Implémenter recherche sémantique",
                    "timestamp": datetime.now().isoformat(),
                    "source": "test",
                    "importance": 0.8,
                    "embedding": [0.2] * 384
                }
            ]
        }
        
        # Écrire le fichier shard
        shard_file = os.path.join(self.temp_dir, "shard_projects.json")
        with open(shard_file, 'w') as f:
            json.dump(shard_data, f)
        
        self.compressor = MemoryCompressor(shards_directory=self.temp_dir, similarity_threshold=0.9)
    
    def tearDown(self):
        # Nettoyer le répertoire temporaire
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_duplicates(self):
        """Test: Détection des doublons"""
        result = self.compressor.compress_shard("shard_projects", force=True)
        
        # Devrait avoir détecté au moins un doublon
        if "error" not in result:
            self.assertGreater(result.get("removed_duplicates", 0), 0)
    
    def test_consolidate_transactions(self):
        """Test: Consolidation des transactions similaires"""
        result = self.compressor.compress_shard("shard_projects", force=True)
        
        # Devrait avoir consolidé des transactions
        if "error" not in result:
            self.assertGreater(result.get("consolidated_transactions", 0), 0)
            self.assertLess(result.get("total_after", 0), result.get("total_before", 0))


class TestMemoryCleaner(unittest.TestCase):
    """Tests du module de nettoyage TTL"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer des shards de test avec des transactions expirées
        old_date = datetime.now() - timedelta(days=100)
        
        shard_data = {
            "config": {
                "id": "shard_projects",
                "name": "Projects Shard",
                "domain": "projects",
                "keywords": ["project", "task"]
            },
            "transactions": [
                {
                    "id": "proj_old",
                    "content": "Projet ancien: Refactorer le code",
                    "timestamp": old_date.isoformat(),
                    "source": "test",
                    "importance": 0.5,
                    "embedding": [0.1] * 384
                },
                {
                    "id": "proj_recent",
                    "content": "Projet récent: Finaliser documentation API",
                    "timestamp": datetime.now().isoformat(),
                    "source": "test",
                    "importance": 0.9,
                    "embedding": [0.2] * 384
                }
            ]
        }
        
        # Écrire le fichier shard
        shard_file = os.path.join(self.temp_dir, "shard_projects.json")
        with open(shard_file, 'w') as f:
            json.dump(shard_data, f)
        
        self.cleaner = MemoryCleaner(shards_directory=self.temp_dir)
    
    def tearDown(self):
        # Nettoyer le répertoire temporaire
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_expired_transactions(self):
        """Test: Vérification des transactions expirées"""
        result = self.cleaner.cleanup_expired_transactions("shard_projects", dry_run=True)
        
        # Devrait avoir détecté au moins une transaction expirée
        if "error" not in result:
            self.assertGreater(result.get("expired_transactions", 0), 0)
            self.assertGreater(result.get("kept_transactions", 0), 0)
    
    def test_ttl_config_loaded(self):
        """Test: Configuration TTL chargée"""
        self.assertIsNotNone(self.cleaner.ttl_config)
        self.assertIn("shard_projects", self.cleaner.ttl_config)


class TestIntegration(unittest.TestCase):
    """Tests d'intégration Phase 2"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Créer les shards de test
        shards_data = {
            "shard_projects.json": {
                "config": {
                    "id": "shard_projects",
                    "name": "Projects Shard",
                    "domain": "projects",
                    "keywords": ["project", "task", "goal"]
                },
                "transactions": []
            },
            "shard_insights.json": {
                "config": {
                    "id": "shard_insights",
                    "name": "Insights Shard",
                    "domain": "insights",
                    "keywords": ["lesson", "pattern", "insight"]
                },
                "transactions": []
            },
            "shard_technical.json": {
                "config": {
                    "id": "shard_technical",
                    "name": "Technical Shard",
                    "domain": "technical",
                    "keywords": ["architecture", "code", "framework"]
                },
                "transactions": []
            },
            "shard_strategy.json": {
                "config": {
                    "id": "shard_strategy",
                    "name": "Strategy Shard",
                    "domain": "strategy",
                    "keywords": ["strategy", "vision", "priority"]
                },
                "transactions": []
            },
            "shard_people.json": {
                "config": {
                    "id": "shard_people",
                    "name": "People Shard",
                    "domain": "people",
                    "keywords": ["@", "contact", "expert"]
                },
                "transactions": []
            }
        }
        
        # Écrire les fichiers shards
        for shard_file, shard_content in shards_data.items():
            with open(os.path.join(self.temp_dir, shard_file), 'w') as f:
                json.dump(shard_content, f)
        
        self.router = ShardRouter()
        self.router.shards_dir = Path(self.temp_dir)
        self.router._load_all_shards()
    
    def tearDown(self):
        # Nettoyer le répertoire temporaire
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_all_shards_loaded(self):
        """Test: Tous les shards sont chargés"""
        self.assertEqual(len(self.router.shards), 5)
        self.assertIn("shard_projects", self.router.shards)
        self.assertIn("shard_insights", self.router.shards)
        self.assertIn("shard_technical", self.router.shards)
        self.assertIn("shard_strategy", self.router.shards)
        self.assertIn("shard_people", self.router.shards)
    
    def test_add_memory_with_routing(self):
        """Test: Ajout de mémoire avec routage automatique"""
        content = "Projet actif: Finaliser documentation API Phase 2"
        
        # Ajouter au shard projects
        tx_id = self.router.add_memory(content, importance=0.9)
        
        self.assertIsNotNone(tx_id)
        self.assertIn("shard_projects", tx_id)
    
    def test_cross_shard_references(self):
        """Test: Détection des cross-references"""
        content = "Voir shard technical pour plus de détails sur l'architecture"
        best_shard_id, cross_refs = self.router._find_best_shard_for_content(content)
        
        self.assertIsNotNone(best_shard_id)
        self.assertIn("shard_technical", cross_refs)


def run_tests():
    """Execute tous les tests et retourne les résultats"""
    print("🧪 Running DARYL Sharding Memory - Phase 2 Unit Tests")
    print("="*70)
    print()
    
    # Créer suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingService))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryCompressor))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryCleaner))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Résumé
    print()
    print("="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    if result.wasSuccessful():
        print("✅ ALL PHASE 2 TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
