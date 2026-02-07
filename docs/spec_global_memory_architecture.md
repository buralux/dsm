# Global Memory Architecture Specification (DARYL Bot)

**Version:** 1.0  
**Date:** 2026-02-05  
**Status:** Spec Design

---

## Overview

DARYL's memory architecture follows a **"source of truth + rich off-chain"** pattern:
- **On-chain (checkpoint):** Immutable proof + coordination anchor
- **Off-chain (database):** Rich, fast, scalable state storage

This architecture supports:
- ✅ Multiple bot instances (multi-shard)
- ✅ Cross-shard coordination
- ✅ Fast read/write operations (off-chain)
- ✅ Provable global state (on-chain)
- ✅ Optimistic conflict resolution

---

## Database Schema

### global_state
The current global state - fast queries for all instances.

```json
{
  "policies": {
    "language": "fr",
    "style": "concise",
    "max_context_tokens": 4000,
    "anti_spam_enabled": true
  },
  "facts": {
    "moltbook_post_history": {
      "last_post_id": "eebaa044...",
      "total_posts": 19
    },
    "moltbook_contacts": {
      "@Jorday": {
        "karma": 526419,
        "engagement_style": "philosophical",
        "expertise": ["frameworks", "architecture"]
      }
    }
  },
  "glossary": {
    "layers": "3-layer architecture pattern",
    "sharding": "Network/Transaction/State partitioning",
    "checkpoint": "On-chain hash of global state"
  },
  "preferences": {
    "user": "Buralux",
    "time_zone": "UTC",
    "default_response_style": "structured"
  },
  "tools": {
    "api_keys": "encrypted_in_env_vars",
    "rate_limits": {
      "moltbook": "1 post / 30 minutes"
    }
  },
  "learned_patterns": {
    "three_layers_performs_well": true,
    "frameworks_with_missing_layer_success": true
  },
  "summary": "DARYL manages 19 Moltbook posts across 3 domains. Best performer: Three Layers (45↑ 27💬). Trust framework pending."
}
```

### global_updates
Append-only log of all state changes.

```json
[
  {
    "update_id": "upd_20260205_190000",
    "timestamp": "2026-02-05T19:00:00Z",
    "version": 1,
    "author_instance": "telegram_instance_eu_west",
    "type": "checkpoint_trigger",
    "changes": {
      "added": [],
      "modified": [],
      "deleted": []
    },
    "previous_checkpoint_hash": "0xabc123...",
    "new_checkpoint_hash": "0xdef456..."
  },
  {
    "update_id": "upd_20260205_190500",
    "timestamp": "2026-02-05T19:00:50Z",
    "version": 1,
    "author_instance": "telegram_instance_eu_west",
    "type": "user_interaction",
    "changes": {
      "added": [
        {
          "key": "facts.moltbook_contacts.@NewExpert",
          "value": {
            "karma": 150000,
            "engagement_style": "technical",
            "expertise": ["reputation", "identity"]
          }
        }
      }
    ],
      "modified": [
        {
          "key": "facts.moltbook_post_history.total_posts",
          "old_value": 19,
          "new_value": 20
        }
      ]
    }
  }
]
```

### checkpoints (on-chain minimal)
Only the minimal proof + coordination anchor.

```json
{
  "checkpoint_id": "chk_20260205_190000",
  "version": 1,
  "timestamp": "2026-02-05T19:00:00Z",
  "author_instance": "telegram_instance_eu_west",
  "checkpoint_hash": "0xdef456789...",
  "pointer": "ipfs://QmXyz123..." OR "offchain_db_checkpoint_123"
}
```

**Field Descriptions:**
- `checkpoint_hash`: Hash of `global_state` at this version
- `pointer`: CID to off-chain DB or internal checkpoint ID
- `version`: Monotonically increasing integer
- `author_instance`: Which bot instance wrote this

---

## Merge Rules (Anti-Conflicts)

### Optimistic Locking
1. Each instance reads latest checkpoint
2. Makes local changes optimistically (assumes no conflicts)
3. Writes new checkpoint
4. Checks for conflicts (version gaps, hash mismatches)
5. If conflict: rolls back and merges

### Conflict Resolution Strategy

**Type 1: Concurrent updates to different paths (MERGE)**
```python
# Both instances update different keys
instance_A: facts.moltbook_posts.total_posts = 20
instance_B: facts.moltbook_contacts.@Jorday.karma = 530000

# Resolution: Keep BOTH
global_state.merged = {
  "facts.moltbook_posts.total_posts": 20,
  "facts.moltbook_contacts.@Jorday.karma": 530000
}
```

**Type 2: Concurrent updates to same key (LATEST_WINS)**
```python
# Both instances update same key
instance_A: preferences.user = "Buralux"
instance_B: preferences.user = "Buralux2"

# Resolution: Keep latest (higher timestamp)
global_state.preferences.user = "Buralux2"
```

**Type 3: Version rollback (REPLAY)**
```python
# Instance A is behind
instance_A.version = 99
instance_B.version = 100

# Resolution: Replay missing updates
for update in global_updates[99:100]:
    apply_to_global_state(update)
```

### Validation Rules

Before accepting a checkpoint as final:
1. Verify checkpoint hash matches computed hash of global_state
2. Verify monotonic version increase
3. Verify author_instance is trusted (or all instances for now)
4. Verify no version gaps in sequence
5. Verify timestamp is reasonable (no future timestamps)

Only after ALL validations pass → mark as "finalized" in DB.

---

## Smart Contract Interface (Minimal)

### Function: setCheckpoint
**Purpose:** Write a new checkpoint to chain

```solidity
function setCheckpoint(
    uint256 version,
    bytes32 checkpointHash,
    bytes pointer,
    address authorInstance
) public onlyCheckpointer returns (uint256) {
    // Validation
    require(version > lastVersion, "Version must increase");
    require(checkpointHash != bytes32(0), "Hash cannot be zero");
    
    // Store
    checkpoints[version] = Checkpoint({
        hash: checkpointHash,
        pointer: pointer,
        author: authorInstance,
        timestamp: block.timestamp
    });
    
    lastVersion = version;
    lastCheckpointPointer = pointer;
    
    emit CheckpointCreated(version, checkpointHash, pointer, msg.sender);
}
```

**Permission:** `onlyCheckpointer` - Only authorized checkpointer instance can write

### Function: getCheckpoint
**Purpose:** Read a checkpoint from chain

```solidity
function getCheckpoint(uint256 version) public view returns (
    bytes32 hash,
    bytes pointer,
    address author,
    uint256 timestamp
) {
    Checkpoint memory c = checkpoints[version];
    return (c.hash, c.pointer, c.author, c.timestamp);
}

function getLatestCheckpoint() public view returns (
    uint256 version,
    bytes32 hash,
    bytes pointer
) {
    return (lastVersion, checkpoints[lastVersion].hash, lastCheckpointPointer);
}
```

**Gas Optimization:**
- Store only minimal data on-chain
- Use `bytes32` for hashes (fixed size)
- No arrays/loops in view functions

---

## Leader Checkpointer Strategy

### Simple, Robust Design

**Single Writer Model:**
- One authorized wallet/instance writes all checkpoints
- Eliminates cross-shard race conditions
- Reduces on-chain gas costs
- Simpler verification logic

**Implementation:**
```python
class LeaderCheckpointer:
    def __init__(self, wallet_address, private_key):
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.is_leader = (wallet_address == AUTHORIZED_CHECKPOINTER)
    
    def should_write_checkpoint(self, version, hash, pointer):
        """Only authorized checkpointer writes"""
        if not self.is_leader:
            return False
        return True
    
    def batch_checkpoint_writes(self, checkpoint_list):
        """Write multiple checkpoints in one transaction to save gas"""
        if not self.is_leader:
            raise Exception("Not authorized to batch write")
        
        # Build calldata for all checkpoints
        checkpoint_ids = []
        for cp in checkpoint_list:
            checkpoint_id = self._submit_checkpoint(cp)
            checkpoint_ids.append(checkpoint_id)
        
        return checkpoint_ids
    
    def verify_checkpoint(self, version):
        """Verify checkpoint exists on chain"""
        try:
            hash, pointer, author, timestamp = contract.getCheckpoint(version)
            return True
        except:
            return False
```

**Why this works:**
- **No contention:** Single writer = no race conditions
- **Verifiable:** Anyone can verify the checkpointer's writes
- **Cross-shard:** All instances trust the same checkpoint chain
- **Fallback:** If checkpointer fails, use multi-sig or rotate leadership

---

## Bot Side Flow

### Global Memory Injection (Telegram Example)

```
┌─────────────────────────────────────────────────────────────┐
│                 Telegram Bot Instance                    │
└─────────────────────────────────────────────────────────────┘

1. User sends message
   ↓
2. READ: global_summary (from off-chain DB)
   - policies: response rules
   - facts: relevant knowledge
   - summary: 1-2k chars context
   ↓
3. GENERATE: Response (using summary as prompt)
   ↓
4. READ: Current global_state version
   ↓
5. CREATE: Delta (minimal update)
   - Added: new contact / updated fact
   - Modified: total_posts count, etc.
   - Deleted: (rare) outdated data
   ↓
6. WRITE: Delta to global_updates (append-only)
   ↓
7. WRITE: Delta to global_state (fast DB update)
   ↓
8. CALCULATE: New hash = H(global_state_versioned)
   ↓
9. SEND: To leader checkpointer (or write directly if authorized)
   {
     "version": N,
     "hash": new_hash,
     "pointer": "offchain_checkpoint_N",
     "author": "this_instance_id"
   }
   ↓
10. PUBLISH: Checkpoint (if checkpointer)
    - SetCheckpoint(version, hash, pointer, author)
    - OR: send to leader's API
   ↓
11. POLL: Checkpoint status (if cross-shard)
    - Every 5 seconds: checkCheckpoint(version)
    - Timeout: 30 seconds
    - On confirmation: mark as "finalized"
    - On timeout: use optimistic update, retry later
   ↓
12. RESPOND: To user (latency < 2s total)
   - Already sent at step 3
   - Just confirm checkpoint finalization if needed
```

### Pseudo-Code Implementation

```python
class GlobalMemoryManager:
    def __init__(self, db_connection, checkpointer_config):
        self.db = db_connection  # Postgres/Redis
        self.checkpointer = LeaderCheckpointer(**checkpointer_config)
    
    async def handle_user_message(self, user_message):
        """Main flow for handling user interactions"""
        
        # Step 1: Read global summary (fast)
        summary = await self.db.get_global_summary()
        
        # Step 2: Generate response (using summary as context)
        response = await self.generate_response(user_message, summary)
        
        # Step 3: Read current state
        current_state = await self.db.get_global_state()
        current_version = current_state["version"]
        
        # Step 4: Create delta
        delta = self._create_delta(user_message, response, current_state)
        
        # Step 5: Write to updates log (append-only)
        await self.db.append_global_updates(delta)
        
        # Step 6: Update global state (fast)
        new_state = self._merge_delta(current_state, delta)
        new_hash = self._compute_hash(new_state)
        
        # Step 7: Prepare checkpoint
        checkpoint = {
            "version": current_version + 1,
            "hash": new_hash,
            "pointer": f"offchain_checkpoint_{current_version + 1}",
            "author": os.getenv("INSTANCE_ID")
        }
        
        # Step 8: Submit checkpoint
        checkpoint_id = await self.checkpointer.write_checkpoint(checkpoint)
        
        # Step 9: Poll for confirmation (cross-shard)
        if self.checkpointer.is_leader:
            # Immediate confirmation if we wrote it
            await self.db.mark_checkpoint_finalized(checkpoint["version"])
        else:
            # Poll for leader's confirmation
            confirmed = await self._poll_checkpoint_confirmation(
                checkpoint["version"], 
                timeout=30
            )
            if confirmed:
                await self.db.mark_checkpoint_finalized(checkpoint["version"])
        
        # Step 10: Return response (already sent in step 2)
        return response
    
    def _create_delta(self, user_message, response, current_state):
        """Create minimal delta for state update"""
        return {
            "update_id": f"upd_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "version": current_state["version"],
            "author_instance": os.getenv("INSTANCE_ID"),
            "type": "user_interaction",
            "changes": {
                "added": self._detect_new_entities(user_message),
                "modified": self._detect_modifications(response)
            }
        }
    
    def _compute_hash(self, state):
        """Compute hash of global state"""
        import hashlib
        state_str = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()
    
    def _poll_checkpoint_confirmation(self, version, timeout=30):
        """Poll blockchain for checkpoint confirmation"""
        for attempt in range(timeout // 5):  # Try 6 times (30s total)
            await asyncio.sleep(5)
            if self.checkpointer.verify_checkpoint(version):
                return True
        return False
```

---

## Cross-Shard Strategy

### Avoiding Asynchronous Latency

**Problem:** If instance A waits for checkpoint confirmation, but instance B already wrote later version → A sees stale data.

**Solution: Optimistic Reads with Eventual Consistency**

```python
class CrossShardManager:
    def __init__(self, db, blockchain):
        self.db = db
        self.blockchain = blockchain
        self.cache_version = 0
        self.cache_valid_until = 0
    
    async def get_global_state(self):
        """Get global state with cache to avoid chain calls"""
        now = time.time()
        
        # Cache valid? Use cached version
        if now < self.cache_valid_until:
            return self.cached_state
        
        # Cache expired? Read from chain
        latest_version, latest_hash, latest_pointer = self.blockchain.getLatestCheckpoint()
        
        # Read state from off-chain DB using pointer
        new_state = await self.db.read_state_from_pointer(latest_pointer)
        
        # Update cache
        self.cached_state = new_state
        self.cache_version = latest_version
        self.cache_valid_until = now + 60  # Cache for 60 seconds
        
        return new_state
    
    async def update_global_state(self, delta):
        """Update state optimistically"""
        current_state = await self.get_global_state()
        
        # Optimistic merge
        new_state = self._optimistic_merge(current_state, delta)
        new_hash = self._compute_hash(new_state)
        
        # Write to DB immediately (fast)
        await self.db.write_global_state(new_state)
        
        # Submit checkpoint (async, non-blocking)
        checkpoint_id = await self.checkpointer.submit_checkpoint({
            "version": new_state["version"] + 1,
            "hash": new_hash,
            "pointer": f"offchain_checkpoint_{new_state['version'] + 1}",
            "author": os.getenv("INSTANCE_ID")
        })
        
        # Poll for confirmation in background
        asyncio.create_task(self._poll_checkpoint_confirmation(new_state["version"] + 1))
        
        return checkpoint_id
```

**Strategies:**

1. **Cache layer:** Store latest state locally for N seconds
2. **Optimistic writes:** Don't wait for checkpoint before using new state
3. **Background polling:** Check for finalization asynchronously
4. **Version-aware reads:** Always prefer latest confirmed version
5. **Stale detection:** If cached version < chain version → invalidate cache

---

## Deployment Strategy

### Phase 1: Single Shard, Single Instance
1. Deploy off-chain DB (Postgres/Redis)
2. Deploy smart contract (minimal 2-function interface)
3. Deploy bot with global memory manager
4. **No sharding yet** - validates core architecture

### Phase 2: Multi-Instance, Single Shard
1. Deploy 2-3 bot instances (different regions)
2. All use same off-chain DB
3. Leader checkpointer writes all checkpoints
4. Others poll for confirmations
5. **Test conflict resolution**

### Phase 3: Multi-Shard (Future)
1. Each shard has its own DB instance
2. Global state replicated across shards
3. Cross-shard merge protocol
4. Shard-specific checkpoints

---

## Monitoring & Debugging

### Key Metrics to Track

1. **Checkpoint latency:** Time from submit to confirmation
2. **Conflict rate:** Percentage of checkpoints with version conflicts
3. **DB read/write latency:** Off-chain operation performance
4. **Cache hit rate:** Percentage of reads served from cache
5. **Cross-shard sync:** Time for shards to catch up to latest checkpoint

### Alert Thresholds

- **Checkpoint latency > 60s** → Check network or checkpointer
- **Conflict rate > 5%** → Review merge strategy
- **DB latency > 100ms** → Optimize queries/indexing
- **Cache hit rate < 70%** → Increase cache TTL

---

## Security Considerations

### On-Chain Security
- **Access control:** Only authorized checkpointer writes
- **Verification:** All instances can verify checkpoints
- **Immutability:** Once confirmed, cannot be altered
- **Replay protection:** Version monotonicity prevents rollback attacks

### Off-Chain Security
- **Database encryption:** At rest encryption for sensitive data
- **Access controls:** Role-based access for DB operations
- **Input validation:** Sanitize all user inputs before DB writes
- **Rate limiting:** Prevent spam abuse of update operations

---

## Next Steps

1. ✅ Review and approve this spec
2. ⏳ Implement off-chain DB schema (Postgres recommended)
3. ⏳ Implement smart contract (Solidity)
4. ⏳ Implement bot-side global memory manager
5. ⏳ Deploy to testnet
6. ⏳ Test conflict resolution scenarios
7. ⏳ Deploy to mainnet
8. ⏳ Monitor and optimize based on metrics

---

## Appendix: Example State Flow

### Scenario: Two concurrent users

```
Time 0s:
├─ Instance A: Reads global_state v=100, hash=0xabc
└─ Instance B: Reads global_state v=100, hash=0xabc

Time 1s:
├─ Instance A: User1 asks "How many posts?"
├─ Instance A: Generates response "19 posts"
├─ Instance A: Creates delta (total_posts=20)
├─ Instance A: Writes to DB (total_posts=20, v=101)
├─ Instance A: Computes hash=0xdef, submits checkpoint v=101
└─ Instance B: User2 adds contact @Expert

Time 2s:
├─ Instance A: Polling checkpoint v=101 (not yet confirmed)
└─ Instance B: Creates delta (adds contact), writes to DB (v=102)

Time 3s:
├─ Instance A: Polling checkpoint v=101 (not yet confirmed)
├─ Instance A: User1 already received response
└─ Instance B: Computes hash=0xghi, submits checkpoint v=102

Time 30s:
├─ Instance A: Checkpoint v=101 confirmed
├─ Instance A: Detects stale (chain shows v=102)
├─ Instance A: Replays updates 101-102 from DB
└─ Instance A: Merges with local changes (if any)

Time 60s:
├─ Instance A: Cache expires, reads v=102 from chain
├─ Instance A: Updates cache with latest state
└─ System: Both instances consistent at v=102
```

---

*Specification created: 2026-02-05 19:05 UTC*  
*Author: DARYL*  
*Status: Ready for implementation*
