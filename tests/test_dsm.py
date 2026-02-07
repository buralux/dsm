#!/usr/bin/env python3
"""
Unit Tests for DARYL Sharding Memory System
"""

import sys
import os
import json
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory_sharding_system import ShardRouter, MemoryShard
from link_validator import LinkValidator

class TestShardRouting(unittest.TestCase):
    """Test automatic shard routing by domain"""

    def setUp(self):
        self.router = ShardRouter()
        self.router.load_all_shards()

    def test_routing_to_projects(self):
        """Test: Content with 'projet' keyword routes to projects shard"""
        best_shard, cross_refs = self.router._find_best_shard_for_content(
            "Projet actif: Finaliser la documentation"
        )
        self.assertEqual(best_shard, "shard_projects")

    def test_routing_to_insights(self):
        """Test: Content with 'pattern' keyword routes to insights shard"""
        best_shard, cross_refs = self.router._find_best_shard_for_content(
            "Pattern identifié: Structure modulaire améliore la maintenabilité"
        )
        self.assertEqual(best_shard, "shard_insights")

    def test_routing_to_strategy(self):
        """Test: Content with 'stratégie' keyword routes to strategy shard"""
        best_shard, cross_refs = self.router._find_best_shard_for_content(
            "Stratégie de contenu: Qualité > Quantité"
        )
        self.assertEqual(best_shard, "shard_strategy")

    def test_routing_to_technical(self):
        """Test: Content with 'architecture' keyword routes to technical shard"""
        best_shard, cross_refs = self.router._find_best_shard_for_content(
            "Architecture du système de sharding"
        )
        self.assertEqual(best_shard, "shard_technical")

class TestCrossReferences(unittest.TestCase):
    """Test cross-reference validation"""

    def setUp(self):
        self.validator = LinkValidator()

    def test_validate_valid_cross_ref(self):
        """Test: Validate a legitimate cross-reference"""
        is_valid, message = self.validator.validate_link("shard_projects", "shard_technical")
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid cross-shard reference")

    def test_validate_self_reference(self):
        """Test: Self-reference should be invalid"""
        is_valid, message = self.validator.validate_link("shard_projects", "shard_projects")
        self.assertFalse(is_valid)
        self.assertEqual(message, "Self-reference not allowed")

    def test_validate_invalid_shard(self):
        """Test: Invalid shard ID should fail validation"""
        is_valid, message = self.validator.validate_link("shard_projects", "shard_invalid")
        self.assertFalse(is_valid)
        self.assertIn("does not exist", message)

class TestMemoryOperations(unittest.TestCase):
    """Test core memory operations"""

    def setUp(self):
        self.router = ShardRouter()
        self.router.load_all_shards()
        self.test_content = "Test unitaire: Vérification du routing automatique"

    def test_add_memory_returns_transaction_id(self):
        """Test: add_memory returns a valid transaction ID"""
        tx_id = self.router.add_memory(
            self.test_content,
            source="test",
            importance=0.7
        )
        self.assertIsNotNone(tx_id)
        self.assertTrue(tx_id.startswith("shard_"))

    def test_add_memory_increases_transaction_count(self):
        """Test: Adding memory increases transaction count"""
        initial_count = sum(len(s.transactions) for s in self.router.shards.values())
        self.router.add_memory(self.test_content, source="test", importance=0.7)
        final_count = sum(len(s.transactions) for s in self.router.shards.values())
        self.assertEqual(final_count, initial_count + 1)

    def test_query_returns_results(self):
        """Test: Query returns matching results"""
        # Add a transaction with keyword that will be routed to technical shard
        self.router.add_memory(
            "Test avec framework et code: Architecture du système",
            source="test",
            importance=0.5
        )
        # Reload router to trigger file persistence
        self.router.load_all_shards()
        # Query with keyword that matches shard_technical keywords
        results = self.router.query("architecture", limit=5)
        self.assertGreater(len(results), 0)

class TestImportanceScoring(unittest.TestCase):
    """Test importance scoring and shard priority"""

    def setUp(self):
        self.router = ShardRouter()
        self.router.load_all_shards()

    def test_importance_increases_score(self):
        """Test: High importance content routes to high-importance shard"""
        # Add a high-importance transaction to projects shard
        shard = self.router.shards["shard_projects"]
        shard.add_transaction("High importance project", source="test", importance=0.9)

        # Query should prefer high-importance shard
        best_shard, _ = self.router._find_best_shard_for_content(
            "Project with keyword"
        )
        self.assertIn("projects", best_shard.lower())

    def test_importance_range_validation(self):
        """Test: Importance scores are in valid range [0.0, 1.0]"""
        shard = self.router.shards["shard_insights"]
        shard.add_transaction("Test", source="test", importance=1.0)

        transaction = shard.transactions[-1]
        self.assertGreaterEqual(transaction["importance"], 0.0)
        self.assertLessEqual(transaction["importance"], 1.0)

class TestDataPersistence(unittest.TestCase):
    """Test data persistence across reloads"""

    def setUp(self):
        self.test_shard_id = "shard_technical"
        self.test_content = "Test persistence: Sauvegarde des transactions"
        self.router = ShardRouter()
        self.router.load_all_shards()

    def test_transaction_saved_to_file(self):
        """Test: Transactions are saved to JSON files"""
        # Add a transaction
        self.router.add_memory(self.test_content, source="test", importance=0.7)

        # Reload and verify
        router2 = ShardRouter()
        router2.load_all_shards()

        shard = router2.shards[self.test_shard_id]
        self.assertGreater(len(shard.transactions), 0)

    def test_transaction_data_integrity(self):
        """Test: Transaction data is preserved after reload"""
        router = ShardRouter()
        router.load_all_shards()

        # Add a specific transaction
        tx_id = router.add_memory(self.test_content, source="test", importance=0.7)

        # Force save
        router.shards[self.test_shard_id]._save()

        # Reload and verify
        router2 = ShardRouter()
        router2.load_all_shards()

        # Find the transaction by content (ID may differ due to timestamp)
        shard = router2.shards[self.test_shard_id]
        found = False
        for tx in shard.transactions:
            if tx["content"] == self.test_content:
                self.assertEqual(tx["source"], "test")
                self.assertEqual(tx["importance"], 0.7)
                found = True
                break
        self.assertTrue(found, "Transaction not found after reload")

def run_tests():
    """Run all tests and report results"""

    print("🧪 Running DARYL Sharding Memory Tests\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestShardRouting))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossReferences))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestImportanceScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestDataPersistence))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
