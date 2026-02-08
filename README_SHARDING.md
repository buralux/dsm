# DARYL Sharding Memory System

Architecture de partitionnement de mémoire par domaine pour une efficacité accrue.

## 📁 Structure

```
memory/
├── shards/
│   ├── shard_projects.json      # Projets en cours
│   ├── shard_insights.json     # Leçons apprises
│   ├── shard_people.json       # Contacts, experts
│   ├── shard_technical.json    # Architecture, code
│   └── shard_strategy.json    # Vision long terme
└── shards_summary.json        # Résumé global
```

## ✅ Fonctionnalités

### 1. Partitionnement automatique par domaine
- 5 shards pré-définis (projects, insights, people, technical, strategy)
- Détection automatique du meilleur shard pour chaque contenu
- Scoring basé sur les mots-clés + importance du shard

### 2. Cross-references (NOUVEAU)
- Détecte automatiquement les connexions entre shards
- Patterns détectés : "shard:projects", "voir shard technical", "connecté avec shard X"
- Stockage des références dans les transactions
- Navigation facilitée entre shards liés

### 3. Recherche cross-shard
- Recherche dans plusieurs shards simultanément
- Résultats triés par importance et date
- Support des requêtes multi-domaine

### 4. Gestion des transactions
- Ajout manuel ou automatique
- Source tracking (manual, moltbook, auto)
- Scoring d'importance (0.0 à 1.0)
- Timestamp ISO 8601

## 🔧 Utilisation

### CLI Interface
```bash
# Exécuter les tests
python3 memory_sharding_system.py

# Depuis un script Python
from memory_sharding_system import ShardRouter

router = ShardRouter()
router.load_all_shards()

# Ajouter une mémoire
router.add_memory("Leçon apprise: la communication est la clé", source="moltbook", importance=0.8)

# Rechercher
results = router.query("Moltbook", limit=10)
for r in results:
    print(f"{r['shard_name']}: {r['content'][:50]}")
```

## 📊 API (FUTUR)

### Endpoints planifiés
- `GET /memory` - Lister toutes les mémoires
- `POST /memory` - Ajouter une mémoire
- `GET /query?q=<text>` - Rechercher cross-shard
- `GET /shards` - Statut des shards
- `POST /checkpoint` - Sauvegarde/Restauration de l'état

### Format des données
```json
{
  "transaction_id": "shard_technical_0_1234567890.123",
  "content": "Leçon sur l'architecture des agents",
  "timestamp": "2026-02-06T02:30:00Z",
  "source": "moltbook",
  "importance": 0.8,
  "cross_refs": ["shard_projects", "shard_insights"],
  "shard_id": "shard_technical",
  "shard_name": "Technique et Architecture"
}
```

## 🎯 Cas d'usage

### 1. Moltbook Comments → Memory
- Détecter automatiquement les leçons apprises dans les commentaires
- Extraire les patterns et insights
- Ajouter au shard `shard_insights`

### 2. Stratégie de contenu → Shard Strategy
- Stocker les décisions de stratégie (topics, fréquences, etc.)
- Stocker les analyses de performance
- Stocker la vision long terme

### 3. Architecture technique → Shard Technical
- Stocker les décisions architecturales
- Stocker les patterns de code
- Stocker les frameworks réutilisables

## 🔮 Limitations actuelles

1. **Compression** : Pas encore implémentée (les vieux fichiers peuvent devenir volumineux)
2. **Sauvegarde/Restauration** : Pas de checkpoint global
3. **API REST** : Pas encore implémentée
4. **Déduplication** : Pas de détection des doublons
5. **Versioning** : Pas de gestion des versions de transactions

## 🚀 Améliorations en cours

- [x] Cross-references automatiques
- [ ] Compression des transactions anciennes
- [ ] Checkpoint global (save/load state)
- [ ] API REST légère
- [ ] Documentation complète

## 📝 Contributeurs

- DARYL (Assistant IA)
- Date de création : 2026-02-06

---

Pour plus d'informations, voir `memory_sharding_system.py`.
