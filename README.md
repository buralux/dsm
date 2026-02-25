# DSM — Daryl Sharding Memory

A **Python-based semantic memory system** for stateful AI agents, with domain sharding, semantic search, compression and TTL cleanup.

---

## ✅ Production Readiness

- **Installable**: `pyproject.toml` + console scripts (`daryl-memory`, `dsm-webui`)
- **Packaged**: wheel/sdist build via `python -m build`
- **Deployable**: `Dockerfile` + `docker-compose.yml`
- **Publishable**: GitHub release workflow for PyPI (`v*` tags)
- **Credible**: CI pipeline, security policy, contribution guide, changelog, pre-commit

---

## 🚀 Quick Start

```bash
git clone https://github.com/buralux/dsm.git
cd dsm
python3 -m pip install -e ".[dev,web]"
daryl-memory status
```

---

## 📦 Install

### From PyPI

```bash
python3 -m pip install daryl-sharding-memory
daryl-memory --help
```

### Local editable install (contributors)

```bash
python3 -m pip install -e ".[dev,web]"
```

### Project naming (important)

- **PyPI package name**: `daryl-sharding-memory`
- **Python imports**: module-based (`memory_sharding_system`, `semantic_search`, etc.)
- **CLI commands**: `daryl-memory`, `dsm-webui`

---

## 🧪 Dev run

```bash
# Core demo run
python3 src/memory_sharding_system.py

# CLI via source module
python3 -m cli.daryl_memory_cli status

# Web UI via source module
python3 -m webui.app
```

---

## 💻 CLI usage

```bash
# Check system status
daryl-memory status

# Add memory with automatic routing
daryl-memory add "Projet actif: Finaliser GitHub release" --importance 0.9

# Search across all shards
daryl-memory query "GitHub" --limit 5

# Search in a specific shard
daryl-memory search shard_projects "GitHub"

# Verbose mode
daryl-memory --verbose status
```

---

## 📦 Packaging

Build distributables:

```bash
python3 -m pip install -U build
python3 -m build
```

Artifacts are generated in `dist/` (`.whl` + `.tar.gz`).

---

## 🚢 Deployment

### Docker

```bash
docker build -t dsm:latest .
docker run --rm -p 8000:8000 -e DSM_MEMORY_DIR=/data/memory -v "$(pwd)/memory:/data/memory" dsm:latest
```

### Docker Compose

```bash
docker compose up --build
```

---

## 🌍 Publishing

Manual publication flow:

```bash
python3 -m pip install -U build twine
python3 -m build
twine check dist/*
twine upload dist/*
```

Automated flow:

- Configure repository secret: `PYPI_API_TOKEN`
- Ensure the tagged commit is already reachable from `main`
- Create a tag `vX.Y.Z`
- Push the tag
- GitHub Action `Publish to PyPI` publishes the package

Note: the release workflow is tag-based (`v*`) and is intended for mainline releases.

---

## 🧩 Compatibility

- **Python**: 3.10, 3.11, 3.12
- **OS**: Linux/macOS/Windows (WSL recommended on Windows)
- **Docker**: optional for deployment
- **Embeddings backend**:
  - default: deterministic local dummy embeddings (no model download)
  - optional real model: install `.[ml]` and set `DSM_USE_REAL_EMBEDDINGS=1`

---

## 📁 Architecture

```
dsm/
├── pyproject.toml                  # Packaging metadata
├── Dockerfile                      # Container deployment
├── docker-compose.yml              # Local deployment
├── .github/workflows/
│   ├── ci.yml                      # CI (tests + build)
│   └── release-pypi.yml            # Publish on v* tags
├── memory/
│   └── shards/                     # 5 domain-specific memory stores (JSON)
├── src/
│   ├── memory_sharding_system.py   # Core sharding logic
│   ├── semantic_search.py          # Semantic retrieval
│   ├── memory_compressor.py        # Compression / deduplication
│   ├── memory_cleaner.py           # TTL cleanup
│   ├── cli/
│   │   └── daryl_memory_cli.py     # Command-line interface
│   └── webui/
│       └── app.py                  # FastAPI web interface
├── docs/
└── tests/
```

---

## ✨ Features

### 🧠 Intelligent Memory Routing
- **5 Specialized Shards** (projects, insights, people, technical, strategy)
- **Keyword-based scoring** - Automatic routing based on domain keywords
- **Importance weighting** - Prioritizes frequently-used shards (configurable bonus)

### 🔗 Auto Cross-References
- **Automatic detection** - Identifies connections between shards ("voir shard technical")
- **Whitelist patterns** - Only allows safe cross-ref formats
- **Max 3 refs per transaction** - Prevents spam and circular references

### 🔐 Security & Validation
- **Input sanitization** - Strips dangerous HTML/JS tags
- **Link validation** - Prevents shard poisoning
- **Auditability** - All operations traceable via CLI
- **No secrets storage** - System never stores API keys or passwords

### 📊 Real-Time Status
- **Shard statistics** - Transaction counts and importance scores
- **Last updated timestamps** - Track recent activity
- **Summary dashboard** - Quick overview of all shards

---

## 📊 System Status

Current stats (example):
```
📊 Statut des Shards DARYL:

  📁 Projets en cours: 2 transactions (importance: 0.90)
  📁 Stratégie et Vision: 1 transaction (importance: 0.80)
  📚 Technique et Architecture: 12 transactions (importance: 0.70)
  📁 Insights et Leçons: 1 transaction (importance: 0.70)
  📭 Personnes et Relations: 0 transactions

📊 Total: 5 shards, 16 transactions
```

---

## 🧪 Tested Scenarios

- ✅ **Routing by domain** - "Projet actif" → shard_projects
- ✅ **Cross-reference detection** - "voir shard technical" → automatic linking
- ✅ **Importance scoring** - Correctly prioritizes active shards
- ✅ **CLI operations** - All commands (add, query, search, status, help)
- ✅ **Data persistence** - JSON shards saved and restored correctly

---

## 🔐 Security

See `docs/SECURITY_CONSIDERATIONS.md` for complete security model:
- **Threat model analysis** (MEDIUM-LOW risk profile)
- **Mitigation strategies** for memory poisoning and injection
- **Audit trails** for all operations
- **No secrets storage** policy

---

## 📋 Use Cases

- **Personal AI assistants** - Long-term memory across conversations
- **Project management** - Track tasks, insights, and technical decisions
- **Knowledge base** - Semantic routing for domain-specific information
- **Agent memory** - Stateful agents with persistent knowledge

---

## 🚧 Roadmap

### Phase 1: Core Improvements (v1.1)
- [x] **Semantic search** - Beyond full-text (embeddings, cosine similarity)
- [x] **Memory compression** - Efficient storage for long-running agents
- [x] **Time-based expiry** - Automatic cleanup of old low-importance memories
- [ ] **Bulk operations** - Import/export multiple transactions at once

### Phase 2: Integration (v1.2)
- [x] **Web UI** - Visual dashboard for memory management
- [ ] **REST API** - HTTP endpoints for external systems
- [ ] **Multi-language support** - Translations (EN, FR, etc.)
- [x] **Docker container** - Easy deployment

### Phase 3: Advanced Features (v2.0)
- [ ] **Memory consolidation** - Automatic summarization and merging
- [ ] **Context-aware retrieval** - Query enhancement with context
- [ ] **Collaborative sharing** - Secure memory sharing between agents
- [ ] **Blockchain backup** - Immutable memory snapshots (experimental)

---

## 📝 License

Apache-2.0. See [LICENSE](LICENSE).

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, standards and PR workflow.

---

For security disclosures, see [SECURITY.md](SECURITY.md).
