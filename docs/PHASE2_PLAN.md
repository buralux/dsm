# DARYL Sharding Memory - Phase 2 Plan
**Objectif**: Ajouter des fonctionnalités core avec Semantic Search
**Date**: 2026-02-07
**Status**: En préparation

---

## 🎯 Objectifs de la Phase 2

### Priorité 1: Semantic Search (Recherche sémantique)
- Intégrer des embeddings pour la recherche par similarité
- Hybrider recherche full-text + semantic
- Améliorer la pertinence des résultats

### Priorité 2: Memory Compression (Compression de mémoire)
- Regrouper automatiquement les mémoires similaires
- Réduire l'espace de stockage
- Optimiser les requêtes

### Priorité 3: Time-based Expiry (Expiration temporelle)
- Configuration TTL par shard
- Nettoyage automatique des vieilles mémoires
- Archivage des données obsolètes

---

## 📋 Tâches détaillées

### Priorité 1: Semantic Search ⚡

#### Tâche 1.1: Sélectionner le modèle d'embeddings
**Objectif**: Choisir un modèle d'embeddings adapté

**Options à considérer**:
- **sentence-transformers** (HuggingFace):
  - all-MiniLM-L6-v2 (lightweight, 384 dimensions)
  - all-mpnet-base-v2 (meilleure qualité, 768 dimensions)
  - Avantages: Open-source, Python pur, pas d'API externe
  - Inconvénients: Téléchargement des modèles (~100-500MB)

- **OpenAI Embeddings**:
  - text-embedding-3-small (1536 dimensions)
  - text-embedding-3-large (3072 dimensions)
  - Avantages: Meilleure qualité, maintenance assurée
  - Inconvénients: Coût par 1000 tokens, requiert clé API

- **Option 3** (Hybride):
  - sentence-transformers en local (cache)
  - OpenAI embeddings pour fallback

**Recommandation**: Commencer avec sentence-transformers (all-MiniLM-L6-v2)
- **Raison**: Open-source, gratuit, léger, bonne qualité pour le français

#### Tâche 1.2: Intégrer les embeddings dans le système
**Objectif**: Ajouter la génération d'embeddings aux transactions

**Actions**:
1. Installer les dépendances:
   ```bash
   pip install sentence-transformers torch
   ```

2. Créer `src/embedding_service.py`:
   - Classe `EmbeddingService` avec modèle sentence-transformers
   - Méthodes: `generate_embedding(text)`, `batch_generate(texts)`
   - Cache des embeddings pour éviter les re-calculs

3. Modifier `MemoryShard._save()` pour générer embeddings:
   - Ajouter champ `embedding` (list de floats) aux transactions
   - Générer au moment de l'ajout (pas à la requête)

**Fichiers à créer/modifier**:
- `src/embedding_service.py` (nouveau)
- `src/memory_sharding_system.py` (modifié - MemoryShard._save)

#### Tâche 1.3: Implémenter la recherche par similarité
**Objectif**: Ajouter une méthode de recherche vectorielle

**Actions**:
1. Créer `src/semantic_search.py`:
   - Classe `SemanticSearch` avec méthodes:
     - `search(query, top_k=5, threshold=0.7)`
     - `_cosine_similarity(emb1, emb2)` (calcul de similarité cosinus)
     - `_filter_by_threshold(results, threshold)`

2. Intégrer dans `ShardRouter`:
   - Ajouter méthode `semantic_search(query_text, top_k=5)`
   - Hybrider avec `query()` existante (full-text)

**Fichiers à créer/modifier**:
- `src/semantic_search.py` (nouveau)
- `src/memory_sharding_system.py` (modifié - ShardRouter)

#### Tâche 1.4: Ajouter tests pour Semantic Search
**Objectif**: Valider la recherche sémantique

**Tests à créer** (`tests/test_semantic_search.py`):
- Test génération d'embeddings
- Test similarité cosinus (valeurs attendues: 0.0-1.0)
- Test recherche avec/sans résultats
- Test threshold filtering
- Test hybride (text + semantic)

**Critères de réussite**:
- Embeddings générées en <100ms
- Similarité calculée correctement
- Résultats triés par pertinence (score > 0.7)

---

### Priorité 2: Memory Compression 📦

#### Tâche 2.1: Définir les critères de similarité
**Objectif**: Identifier quand deux transactions sont similaires

**Critères à considérer**:
- Similarité cosinus > 0.9 (embeddings très proches)
- Mots-clés identiques (routing vers le même shard)
- Similarité sémantique du contenu (via embeddings)
- Différence de temps < 24h

#### Tâche 2.2: Implémenter la consolidation
**Objectif**: Regrouper les transactions similaires

**Actions**:
1. Créer `src/memory_compressor.py`:
   - Classe `MemoryCompressor` avec méthodes:
     - `find_similar_transactions(transactions, threshold=0.9)`
     - `consolidate_transactions(group)`
     - `generate_summary(transactions)` (optionnel)

2. Stratégies de consolidation:
   - **Keep newest**: Garder la plus récente, archiver les anciennes
   - **Merge**: Fusionner les contenus (concaténation intelligente)
   - **Summarize**: Créer un résumé (via LLM si disponible)

**Fichiers à créer**:
- `src/memory_compressor.py` (nouveau)
- Modifier `src/memory_sharding_system.py` pour intégrer la compression

#### Tâche 2.3: Ajouter des tests de compression
**Objectif**: Valider la logique de consolidation

**Tests à créer**:
- Test identification de similarité
- Test consolidation (keep newest vs merge)
- Test génération de résumés
- Test intégration avec ShardRouter

---

### Priorité 3: Time-based Expiry ⏰

#### Tâche 3.1: Définir la configuration TTL
**Objectif**: Configurer l'expiration par shard

**Structure de configuration**:
```json
{
  "shard_projects": {
    "ttl_days": 30,
    "max_transactions": 100
  },
  "shard_insights": {
    "ttl_days": 90,
    "max_transactions": 50
  },
  "shard_strategy": {
    "ttl_days": 180,
    "max_transactions": 200
  }
}
```

#### Tâche 3.2: Implémenter le nettoyage automatique
**Objectif**: Supprimer les transactions expirées

**Actions**:
1. Créer `src/memory_cleaner.py`:
   - Classe `MemoryCleaner` avec méthodes:
     - `check_expired_transactions(shard, ttl_days)`
     - `archive_transactions(transactions)` (optionnel)
     - `delete_transactions(transactions)`
     - `run_cleanup_all_shards(config)`

2. Intégrer dans `ShardRouter`:
   - Ajouter méthode `cleanup_expired()`
   - Appeler au boot (optionnel via config)
   - Ou via tâche planifiée

**Fichiers à créer**:
- `src/memory_cleaner.py` (nouveau)
- `src/config/ttl_config.json` (nouveau)
- Modifier `src/memory_sharding_system.py` pour intégrer

#### Tâche 3.3: Ajouter des tests d'expiration
**Objectif**: Valider la logique de TTL

**Tests à créer**:
- Test identification de transactions expirées
- Test suppression (avec et sans archivage)
- Test configuration TTL par shard
- Test intégration avec ShardRouter

---

## 🔧 Dépendances

### Packages Python à installer:
```bash
pip install sentence-transformers torch numpy scipy scikit-learn
```

**Explications**:
- `sentence-transformers`: Modèles d'embeddings HuggingFace
- `torch`: Backend de calcul pour les embeddings
- `numpy`: Calculs vectoriels
- `scipy`: Calcul de similarité cosinus
- `scikit-learn`: Clustering (optionnel pour compression)

---

## 📊 Résultats attendus

### Métriques de succès:
1. **Semantic Search**:
   - Recherche par similarité fonctionne
   - Résultats pertinents (score > 0.7)
   - Performance <200ms par requête
   - Hybride text+semantic opérationnel

2. **Memory Compression**:
   - Réduction de 20-40% de l'espace
   - Pas de perte critique d'information
   - Consolidation intelligente des doublons

3. **Time-based Expiry**:
   - Configuration TTL fonctionnelle
   - Nettoyage automatique opérationnel
   - Archive optionnelle des données expirées

### Couverture de tests:
- Target: 90% de couverture
- Nouveaux tests: 20+ cas de test
- Classes: SemanticSearch, MemoryCompressor, MemoryCleaner

---

## 🚀 Ordre d'implémentation

### S1: Préparation (1-2 heures)
1. Installer les dépendances
2. Télécharger le modèle d'embeddings
3. Créer `src/config/ttl_config.json`
4. Tests des dépendances

### S2: Semantic Search (4-6 heures)
1. Implémenter `EmbeddingService`
2. Intégrer embeddings dans `MemoryShard`
3. Implémenter `SemanticSearch`
4. Intégrer dans `ShardRouter`
5. Tests de Semantic Search

### S3: Memory Compression (3-4 heures)
1. Implémenter `MemoryCompressor`
2. Stratégies de consolidation
3. Tests de compression

### S4: Time-based Expiry (2-3 heures)
1. Implémenter `MemoryCleaner`
2. Configuration TTL
3. Nettoyage automatique
4. Tests d'expiration

### S5: Intégration & Tests (2-3 heures)
1. Intégration complète avec `ShardRouter`
2. Tests d'intégration
3. Mise à jour de la CLI
4. Documentation mise à jour

**Total estimé: 12-18 heures**

---

## 📋 Livrables

### Code:
- `src/embedding_service.py` - Service d'embeddings
- `src/semantic_search.py` - Recherche sémantique
- `src/memory_compressor.py` - Compression de mémoire
- `src/memory_cleaner.py` - Nettoyage TTL
- `src/config/ttl_config.json` - Configuration TTL
- Modifications de `src/memory_sharding_system.py`
- Modifications de `src/cli/daryl_memory_cli.py`

### Documentation:
- `docs/SEMANTIC_SEARCH.md` - Guide d'utilisation
- Mise à jour de `docs/API_REFERENCE.md`
- Mise à jour de `README.md` (nouvelles fonctionnalités)

### Tests:
- `tests/test_semantic_search.py` - Tests recherche sémantique
- `tests/test_memory_compressor.py` - Tests compression
- `tests/test_memory_cleaner.py` - Tests TTL
- Mise à jour de `tests/test_dsm.py` (tests existants)

---

## 🚀 Prochaines étapes après Phase 2

### Phase 3: User Experience 💻
1. Web UI (Flask/FastAPI)
   - Dashboard visuel des shards
   - Interface graphique pour ajouter/chercher
   - Graph de connexions entre shards
   - Visualisation des embeddings (optionnel)

2. REST API
   - Endpoints HTTP pour intégration externe
   - Documentation Swagger/OpenAPI

3. Multi-language Support
   - Traductions (EN, FR, ES, DE)
   - Messages localisés

### Phase 4: Advanced Features 🚀
1. Memory Consolidation
   - Résumé automatique des mémoires
   - Fusion intelligente (LLM-based)

2. Context-aware Retrieval
   - Amélioration des requêtes avec contexte
   - Reranking dynamique

3. Collaborative Sharing
   - Partage sécurisée entre agents
   - Encryption des données partagées

4. Blockchain Backup (experimental)
   - Snapshots immutables
   - Comparaison avec l'approche Namnesis

---

## ⚠️ Notes et Risques

### Risques identifiés:
1. **Performance**: Embeddings peuvent être lents sur CPU
   - **Mitigation**: Cache des embeddings, calcul async

2. **Stockage**: Embeddings augmentent la taille des fichiers JSON
   - **Mitigation**: Compression gzip, stockage séparé (binary)

3. **Complexité**: Plus de code à maintenir
   - **Mitigation**: Tests complets, documentation claire

4. **Dépendances**: sentence-transformers + torch lourds
   - **Mitigation**: Option d'API externe (OpenAI)

### Questions ouvertes:
1. Utiliser sentence-transformers ou OpenAI embeddings?
2. Archiver ou supprimer les transactions expirées?
3. Compression automatique ou manuelle?

---

*Plan créé: 2026-02-07*
*Estimation: 12-18 heures*
*Priorité: Semantic Search > Compression > Expiry*
