# DSM — Daryl Sharding Memory

A **lightweight, Python-based semantic memory system** for building stateful AI agents with intelligent routing and cross-references.

---

## 🚀 Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/daryl-labs/dsm.git
cd dsm

# Run system
python3 src/memory_sharding_system.py
```

### CLI Usage
```bash
# Add memory with automatic routing
python3 src/cli/daryl_memory_cli.py add "Projet actif: Finaliser GitHub release" --importance 0.9

# Search across all shards
python3 src/cli/daryl_memory_cli.py query "GitHub" --limit 5

# Search in specific shard
python3 src/cli/daryl_memory_cli.py search shard_projects "GitHub"

# Check system status
python3 src/cli/daryl_memory_cli.py status

# Get help
python3 src/cli/daryl_memory_cli.py help
```

---

## 📁 Architecture

```
dsm/
├── memory/
│   └── shards/           # 5 domain-specific memory stores (JSON)
├── src/
│   ├── memory_sharding_system.py   # Core sharding logic
│   ├── link_validator.py          # Cross-reference validation
│   └── cli/
│       └── daryl_memory_cli.py    # Command-line interface
├── docs/
│   ├── SECURITY_CONSIDERATIONS.md  # Security model
│   ├── spec_global_memory_architecture.md
│   └── daryl_sharding_critique_analysis.md
└── docs/                           # Specs, API, security
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
- [ ] **Semantic search** - Beyond full-text (embeddings, cosine similarity)
- [ ] **Memory compression** - Efficient storage for long-running agents
- [ ] **Time-based expiry** - Automatic cleanup of old low-importance memories
- [ ] **Bulk operations** - Import/export multiple transactions at once

### Phase 2: Integration (v1.2)
- [ ] **Web UI** - Visual dashboard for memory management
- [ ] **REST API** - HTTP endpoints for external systems
- [ ] **Multi-language support** - Translations (EN, FR, etc.)
- [ ] **Docker container** - Easy deployment

### Phase 3: Advanced Features (v2.0)
- [ ] **Memory consolidation** - Automatic summarization and merging
- [ ] **Context-aware retrieval** - Query enhancement with context
- [ ] **Collaborative sharing** - Secure memory sharing between agents
- [ ] **Blockchain backup** - Immutable memory snapshots (experimental)

---

## 📝 License

MIT License. See [LICENSE](LICENSE).

---

## 🤝 Contributing

Feedback and contributions welcome. See [daryl.md](https://daryl.md) and issues on GitHub.

---

*DARYL-LABS — https://daryl.md — https://github.com/daryl-labs/dsm*
