# DARYL Sharding Memory - API Documentation

**Version:** 1.0
**Date:** 2026-02-07
**Status:** Stable

---

## Overview

DARYL Sharding Memory (DSM) provides a Python-based semantic memory system with intelligent routing and cross-references.

---

## Core Modules

### 1. ShardRouter (`memory_sharding_system.py`)

Main controller for memory operations.

#### Methods

##### `add_memory(content, source="manual", importance=0.5)`
Add a new memory transaction with automatic shard routing.

**Parameters:**
- `content` (str): Memory content
- `source` (str): Origin source ("manual", "moltbook", "system") - default: "manual"
- `importance` (float): Importance score (0.0-1.0) - default: 0.5

**Returns:** `transaction_id` (str)

**Example:**
```python
router = ShardRouter()
router.load_all_shards()
tx_id = router.add_memory(
    "Projet: Finaliser documentation API",
    source="manual",
    importance=0.9
)
print(f"Transaction ID: {tx_id}")
# Output: shard_projects_2_1234567890.123456
```

---

##### `query(query_text, limit=10)`
Search across all shards.

**Parameters:**
- `query_text` (str): Search query
- `limit` (int): Maximum results - default: 10

**Returns:** `list` of transaction objects

**Example:**
```python
results = router.query("GitHub", limit=5)
for r in results:
    print(f"[{r['shard_name']}] {r['content']}")
```

---

##### `cross_shard_search(query_text)`
Advanced search with cross-reference resolution.

**Parameters:**
- `query_text` (str): Search query

**Returns:** `list` of transaction objects with shard info

**Example:**
```python
results = router.cross_shard_search("stratégie")
for r in results:
    print(f"{r['shard_name']}: {r['importance']} - {r['content'][:50]}...")
```

---

##### `export_shards_summary()`
Generate summary of all shards.

**Returns:** `dict` with summary statistics

**Example:**
```python
summary = router.export_shards_summary()
print(f"Total transactions: {summary['total_transactions']}")
print(f"Shards count: {summary['total_shards']}")
```

---

### 2. MemoryShard (`memory_sharding_system.py`)

Individual shard manager.

#### Methods

##### `add_transaction(content, source="manual", importance=0.5, cross_refs=None)`
Add a transaction to this shard.

**Parameters:**
- `content` (str): Transaction content
- `source` (str): Origin source - default: "manual"
- `importance` (float): Importance score - default: 0.5
- `cross_refs` (list): List of shard IDs to reference - default: None

**Returns:** `transaction_id` (str)

**Example:**
```python
shard.add_transaction(
    "Key insight: Semantic routing improves relevance",
    source="moltbook",
    importance=0.8,
    cross_refs=["shard_insights", "shard_strategy"]
)
```

---

##### `query(query_text, limit=10)`
Search within this shard.

**Parameters:**
- `query_text` (str): Search query
- `limit` (int): Maximum results - default: 10

**Returns:** `list` of matching transactions

**Example:**
```python
results = shard.query("memory", limit=3)
for r in results:
    print(f"{r['content'][:60]}...")
```

---

### 3. LinkValidator (`link_validator.py`)

Validate cross-references between shards.

#### Methods

##### `validate_cross_ref(source_shard_id, target_shard_id)`
Check if a cross-reference is valid.

**Parameters:**
- `source_shard_id` (str): Source shard ID
- `target_shard_id` (str): Target shard ID

**Returns:** `bool` (True if valid)

**Example:**
```python
validator = LinkValidator()
if validator.validate_cross_ref("shard_projects", "shard_technical"):
    print("Cross-reference is valid")
```

---

##### `get_cross_refs_from_content(content, max_refs=3)`
Extract cross-references from content.

**Parameters:**
- `content` (str): Content to analyze
- `max_refs` (int): Maximum references to extract - default: 3

**Returns:** `list` of shard IDs

**Example:**
```python
refs = validator.get_cross_refs_from_content(
    "Voir shard technical pour plus de détails",
    max_refs=3
)
print(f"Found cross-refs: {refs}")
# Output: ['shard_technical']
```

---

## Configuration

### Shard Domains

Each shard has specific keywords for automatic routing:

| Shard ID | Domain Name | Keywords |
|-----------|-------------|-----------|
| shard_projects | Projets en cours | projet, task, project, todo, goal, objective |
| shard_insights | Insights et Leçons | leçon, lesson, pattern, insight, décision, decision |
| shard_people | Personnes et Relations | @, contact, person, expert, builder, relation |
| shard_technical | Technique et Architecture | architecture, framework, code, protocol, shard, layer, pillar |
| shard_strategy | Stratégie et Vision | stratégie, vision, priority, strategie, tendance, trend |

### Cross-Reference Patterns

Supported cross-reference patterns:
- `shard:<domain>` (e.g., "shard:projects")
- `voir shard <domain>` (e.g., "voir shard technical")
- `shard <domain>` (e.g., "shard technical")
- `connecte avec shard <domain name>` (e.g., "connecte avec shard Projets en cours")

---

## Error Handling

### Common Exceptions

```python
try:
    router = ShardRouter()
    router.load_all_shards()
    tx_id = router.add_memory(content)
except Exception as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

---

## Best Practices

1. **Use specific keywords** in content for accurate routing
2. **Set appropriate importance** (0.8-1.0 for critical, 0.5-0.7 for standard)
3. **Add cross-references** sparingly (max 3 per transaction)
4. **Regular backups** of `memory/shards/*.json` directory
5. **Validate data integrity** periodically with `daryl-memory status`

---

## Examples

### Example 1: Basic Memory Addition

```python
from memory_sharding_system import ShardRouter

router = ShardRouter()
router.load_all_shards()

# Add a project memory
tx_id = router.add_memory(
    "Projet actif: Finaliser documentation API",
    source="manual",
    importance=0.9
)

print(f"✅ Memory added: {tx_id}")
```

### Example 2: Search and Analysis

```python
# Search across all shards
results = router.query("GitHub", limit=5)

for r in results:
    shard_name = r.get("shard_name", "Unknown")
    content = r["content"][:70] + "..." if len(r["content"]) > 70 else r["content"]
    importance = r.get("importance", 0)
    print(f"[{shard_name}] ({importance:.2f}) {content}")

# Get system summary
summary = router.export_shards_summary()
print(f"\n📊 Total: {summary['total_transactions']} transactions")
```

### Example 3: Cross-Reference Detection

```python
from link_validator import LinkValidator

validator = LinkValidator()

# Extract cross-references
content = "Projet: GitHub release - voir shard technical"
refs = validator.get_cross_refs_from_content(content, max_refs=3)

print(f"Found cross-refs: {refs}")
# Output: ['shard_technical']

# Validate
for ref in refs:
    if validator.validate_cross_ref("shard_projects", ref):
        print(f"✅ Valid: {ref}")
    else:
        print(f"❌ Invalid: {ref}")
```

---

## CLI Reference

See `src/cli/daryl_memory_cli.py` for command-line interface.

Available commands:
- `add` - Add a memory
- `query` - Search across shards
- `search` - Search in specific shard
- `status` - Display shard statistics
- `help` - Show help information

---

*Last updated: 2026-02-07*
