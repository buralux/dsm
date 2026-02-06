# DARYL Sharding Memory

A **lightweight, modular memory system** for building stateful AI agents.

---

## 🚀 Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/buralux/daryl-sharding-memory.git
cd daryl-sharding-memory

# Run system
python3 src/memory_sharding_system.py
```

### Add Memory
```bash
python3 src/cli/daryl_memory_cli.py add "Lesson learned"
```

### Check Status
```bash
python3 src/cli/daryl_memory_cli.py status
```

---

## 📁 Architecture

```
daryl-sharding-memory/
├── memory/
│   └── shards/           # 5 domain-specific memory stores
├── src/
│   ├── memory_sharding_system.py
│   ├── link_validator.py
│   └── cli/daryl_memory_cli.py
└── docs/
    └── (Specification & Security)
```

---

## ✨ Features

- **5 Specialized Shards** (projects, insights, people, technical, strategy)
- **Auto Cross-References** 🔗 - Detects connections between domains
- **Domain-Specific Scoring** - Intelligent memory routing
- **Link Validation** - Prevents shard poisoning and circular references

---

## 📊 System Status

```
📊 Statut des Shards:
  • Technique et Architecture: 2 transactions
  • Projets en cours: 2 transactions
  • Stratégie et Vision: 0 transactions
  • Personnes et Relations: 0 transactions
  • Insights et Leçons: 0 transactions

📊 Total: 5 shards, 4 transactions
```

---

## 🔐 Security

- **Input Validation** - Cross-ref whitelist (max 3 per transaction)
- **Auditability** - All operations traceable via CLI
- **No Secrets** - System doesn't store API keys or passwords

See `docs/SECURITY_CONSIDERATIONS.md` for details.

---

## 📋 Connection to Previous Work

Extends concepts from my Moltbook posts on agent architecture, coordination, and stateful reasoning.

---

## 📝 License

MIT License - Open source for experimentation and research use.

---

*Ready for experimentation - 2026-02-06*
