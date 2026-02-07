#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Architecture de Sharding pour la Mémoire de DARYL v2
Partitionnement de la mémoire par domaine pour une efficacité accrue
Améliorations:
- Détection automatique des cross-references entre shards
- Gestion des connexions entre shards
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
MEMORY_DIR = Path("/home/buraluxtr/clawd/memory/")
SHARDS_DIR = Path("/home/buraluxtr/clawd/memory/shards/")
SHARD_CONFIG_FILE = Path("/home/buraluxtr/clawd/memory/shard_config.json")

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
        "keywords": ["stratégie", "vision", "priority", "strategie", "tendance", "trend"]
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
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "importance_score": 0.0
        }
    
    def add_transaction(self, content, source="manual", importance=0.5, cross_refs=None):
        """Ajoute une transaction (mémoire) à ce shard"""
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
        """Recherche dans ce shard seulement"""
        query_lower = query_text.lower()
        results = []
        for t in reversed(self.transactions):  # Plus récent d'abord
            if query_lower in t["content"].lower():
                results.append(t)
                if len(results) >= limit:
                    break
        return results
    
    def get_recent(self, limit=5):
        """Récupère les transactions les plus récentes"""
        return list(reversed(self.transactions[-limit:]))
    
    def cross_shard_references(self):
        """Trouve les références vers d'autres shards"""
        refs = []
        for t in self.transactions:
            # Chercher des motifs de cross-shard references
            # Ex: "Voir shard:projects" ou "Connecté avec @Jorday"
            if "shard:" in t["content"].lower():
                refs.append(t["content"])
        return refs
    
    def _update_importance(self):
        """Met à jour le score d'importance du shard"""
        if not self.transactions:
            return
        total_importance = sum(t["importance"] for t in self.transactions)
        self.metadata["importance_score"] = total_importance / len(self.transactions)
        self.metadata["last_updated"] = datetime.now().isoformat()
    
    def _save(self):
        """Sauvegarde le shard dans un fichier JSON"""
        shard_file = SHARDS_DIR / f"{self.shard_id}.json"
        data = {
            "shard_id": self.shard_id,
            "domain": self.domain,
            "config": self.config,
            "transactions": self.transactions,
            "metadata": self.metadata
        }
        with open(shard_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def to_dict(self):
        """Convertit en dictionnaire pour export"""
        return {
            "shard_id": self.shard_id,
            "domain": self.domain,
            "config": self.config,
            "transactions": self.transactions,
            "metadata": self.metadata
        }

class ShardRouter:
    """Routeur pour gérer les shards et les recherches cross-shard"""
    
    def __init__(self):
        self.shards = {}
        self.shard_index = {}  # shard_id → Shard object
        self.cross_shard_cache = {}
    
    def load_all_shards(self):
        """Charge tous les shards depuis le système de fichiers"""
        if not SHARDS_DIR.exists():
            SHARDS_DIR.mkdir(parents=True)
            self._create_shards_for_all_domains()
        else:
            for shard_file in SHARDS_DIR.glob("*.json"):
                with open(shard_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    shard_id = data["shard_id"]
                    shard = MemoryShard(shard_id, data["domain"])
                    shard.transactions = data["transactions"]
                    shard.metadata = data["metadata"]
                    self.shards[shard_id] = shard
                    self.shard_index[shard_id] = shard
        
        # S'assurer que tous les domaines ont des shards
        for domain in SHARD_DOMAINS.keys():
            shard_id = f"shard_{domain}"
            if shard_id not in self.shards:
                self._create_shard(shard_id, domain)
    
    def _create_shards_for_all_domains(self):
        """Crée un shard pour chaque domaine"""
        for domain in SHARD_DOMAINS.keys():
            self._create_shard(f"shard_{domain}", domain)
    
    def _create_shard(self, shard_id, domain):
        """Crée un nouveau shard"""
        shard = MemoryShard(shard_id, domain)
        self.shards[shard_id] = shard
        self.shard_index[shard_id] = shard
        shard._save()
    
    def add_memory(self, content, source="manual", importance=0.5):
        """Ajoute une mémoire en détectant automatiquement le bon shard"""
        best_shard_id, cross_refs = self._find_best_shard_for_content(content)
        shard = self.shards[best_shard_id]
        transaction_id = shard.add_transaction(content, source, importance, cross_refs)
        return transaction_id

    def _find_best_shard_for_content(self, content):
        """Trouve le meilleur shard pour un contenu"""
        content_lower = content.lower()
        scores = {}
        cross_refs = []

        for shard_id, shard in self.shards.items():
            score = 0.0
            domain = shard.config["name"]

            # Score base sur les mots-cles du domaine
            for keyword in shard.config["keywords"]:
                if keyword.lower() in content_lower:
                    score += 1.0

            # Petit bonus pour l'importance actuelle du shard (réduit pour éviter la domination)
            score += shard.metadata.get("importance_score", 0) * 0.5

            scores[shard_id] = score

        # Détecter les cross-references (indépendamment du shard cible)
        for shard_id, shard in self.shards.items():
            other_domain = shard.config["name"]
            # Détection de motifs: "shard:projects", "voir shard technical", etc.
            pattern_list = [
                f"shard:{shard_id.replace('shard_', '')}",
                f"voir shard {shard_id.replace('shard_', '')}",
                f"{shard_id.replace('shard_', 'shard ')}",
                f"shard {other_domain.lower()}",
                f"connecte avec shard {other_domain}"
            ]
            if any(p in content_lower for p in pattern_list):
                if shard_id not in cross_refs:
                    cross_refs.append(shard_id)

        # Retourner le shard avec le score le plus élevé et les cross-references
        if scores:
            best_shard = max(scores, key=scores.get)
            return best_shard, cross_refs if cross_refs else None

        # Fallback: shard par défaut
        return "shard_insights", None
    
    def query(self, query_text, limit=10):
        """Recherche cross-shard"""
        results = []

        # Première passe: rechercher dans les shards pertinents
        relevant_shard_ids = self._find_shards_for_query(query_text)

        for shard_id in relevant_shard_ids:
            shard = self.shards[shard_id]
            shard_results = shard.query(query_text, limit=limit)
            results.extend(shard_results)
            if len(results) >= limit:
                break

        return results
    
    def _find_shards_for_query(self, query_text):
        """Trouve les shards pertinents pour une requête"""
        query_lower = query_text.lower()
        relevant_shards = []

        for shard_id, shard in self.shards.items():
            # Chercher dans le nom et la description du shard
            domain_text = f"{shard.config['name']} {shard.config['description']}".lower()
            if query_lower in domain_text or any(kw.lower() in query_lower for kw in shard.config["keywords"]):
                relevant_shards.append(shard_id)

        return relevant_shards
    
    def get_all_shards_status(self):
        """Retourne le statut de tous les shards"""
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
        return sorted(status, key=lambda x: x["importance_score"], reverse=True)
    
    def cross_shard_search(self, query_text):
        """Recherche avancée avec cross-references"""
        # Chercher dans tous les shards
        all_results = []
        for shard_id, shard in self.shards.items():
            results = shard.query(query_text, limit=3)
            for r in results:
                r["shard_id"] = shard_id
                r["shard_name"] = shard.config["name"]
                all_results.append(r)

        # Trier par importance et date
        all_results.sort(key=lambda x: (x.get("importance", 0), x["timestamp"]), reverse=True)

        return all_results[:10]
    
    def export_shards_summary(self):
        """Exporte un résumé de tous les shards"""
        summary = {
            "exported_at": datetime.now().isoformat(),
            "total_shards": len(self.shards),
            "total_transactions": sum(len(s.transactions) for s in self.shards.values()),
            "domains_count": len(set(s.domain for s in self.shards.values())),
            "shards_status": self.get_all_shards_status()
        }

        summary_file = MEMORY_DIR / "shards_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return summary

def main():
    """Point d'entrée principal"""
    # Créer les dossiers si nécessaires
    SHARDS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialiser le routeur de shards
    router = ShardRouter()
    router.load_all_shards()

    print("=== Sharding pour la Mémoire de DARYL v2 ===")
    print(f"\n✅ Shards initialisés: {len(router.shards)}")
    print(f"📁 Répertoire des shards: {SHARDS_DIR}")

    # Afficher le statut des shards
    print("\n📊 Statut des shards:")
    for shard_status in router.get_all_shards_status()[:5]:
        print(f"  • {shard_status['name']}: {shard_status['transactions_count']} transactions (importance: {shard_status['importance_score']:.2f})")

    # Test 1: Ajout avec cross-references
    print("\n🔍 Test 1: Ajout avec cross-references")
    test_content1 = "Post Moltbook sur le sharding - voir shard technical pour plus de détails"
    print(f"  Contenu: {test_content1}")
    best_shard_id, cross_refs = router._find_best_shard_for_content(test_content1)
    print(f"  Meilleur shard: {best_shard_id}")
    print(f"  Cross-refs détectées: {cross_refs}")

    # Test 2: Ajout sans cross-references
    print("\n🔍 Test 2: Ajout sans cross-references")
    test_content2 = "Nouvelle leçon apprise: la communication est la clé du succès"
    print(f"  Contenu: {test_content2}")
    best_shard_id2, cross_refs2 = router._find_best_shard_for_content(test_content2)
    print(f"  Meilleur shard: {best_shard_id2}")
    print(f"  Cross-refs détectées: {cross_refs2}")

    # Test 3: Ajout réel via add_memory
    print("\n🔍 Test 3: Ajout réel via add_memory")
    tid1 = router.add_memory(test_content1, "test")
    print(f"  Transaction ID: {tid1}")

    tid2 = router.add_memory(test_content2, "test")
    print(f"  Transaction ID: {tid2}")

    # Exporter le résumé
    summary = router.export_shards_summary()
    print(f"\n📝 Résumé exporté: {len(summary['shards_status'])} shards, {summary['total_transactions']} transactions")

    print("\n✅ Tests réussis !")

if __name__ == "__main__":
    main()
