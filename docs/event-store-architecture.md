# Event Store Architecture: Deep Dive

## The Core Problem

An event store must solve several challenges:

1. **Append Performance** - Writing events must be fast (workflow hot path)
2. **Read Performance** - Reading event streams must be fast (dashboard queries)
3. **Storage Growth** - Events accumulate forever without compaction
4. **Concurrency** - Multiple workflows writing simultaneously
5. **Ordering** - Events must be totally ordered per workflow
6. **Durability** - No data loss on crash
7. **Query Patterns** - Support both sequential reads and projections
8. **Audit Requirements** - Events are immutable, never deleted

---

## Event Store Options Analysis

### Option 1: File-Based JSONL (Append-Only Log)

**Structure:**
```
events/
├── beads-y97.events          # One file per workflow
│   └── {event}\n{event}\n    # Newline-delimited JSON
├── beads-7gq.events
└── beads-400.events
```

**Implementation:**
```python
class JSONLEventStore:
    def __init__(self, base_path: Path):
        self.base_path = base_path / "events"
        self.base_path.mkdir(exist_ok=True)
        self._locks = {}  # Per-workflow file locks

    def append(self, event: WorkflowEvent) -> None:
        """Append event to workflow's log file."""
        log_file = self.base_path / f"{event.workflow_id}.events"

        # Get or create lock for this workflow
        lock = self._locks.setdefault(event.workflow_id, threading.Lock())

        with lock:
            with log_file.open('a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(event)) + '\n')
                f.flush()  # Ensure written to disk
                os.fsync(f.fileno())  # Force OS to write to disk

    def get_events(self, workflow_id: str,
                   since_sequence: int = 0) -> list[WorkflowEvent]:
        """Read events for workflow."""
        log_file = self.base_path / f"{workflow_id}.events"

        if not log_file.exists():
            return []

        events = []
        with log_file.open('r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= since_sequence and line.strip():
                    event_data = json.loads(line)
                    events.append(WorkflowEvent(**event_data))

        return events
```

**Pros:**
- ✅ Simple, no dependencies
- ✅ Human-readable (can inspect with `cat`, `jq`)
- ✅ Easy to backup (just copy files)
- ✅ Natural append-only semantics
- ✅ One file per workflow = natural partitioning

**Cons:**
- ❌ No built-in compaction
- ❌ Full file scan to read all events
- ❌ No indexing (can't query by event type efficiently)
- ❌ Large files over time (100K+ events)
- ❌ Concurrent append needs explicit locking

**Best for:** Small-medium scale (<10K events per workflow)

---

### Option 2: SQLite Event Store

**Structure:**
```sql
CREATE TABLE events (
    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data JSON NOT NULL,

    -- Indexes for common queries
    INDEX idx_workflow_sequence ON events(workflow_id, sequence_number),
    INDEX idx_event_type ON events(event_type),
    INDEX idx_timestamp ON events(timestamp)
);

-- Separate table for snapshots (compaction)
CREATE TABLE snapshots (
    workflow_id TEXT PRIMARY KEY,
    sequence_number INTEGER NOT NULL,
    state JSON NOT NULL,
    created_at TEXT NOT NULL
);
```

**Implementation:**
```python
import sqlite3
from contextlib import contextmanager

class SQLiteEventStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data JSON NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow_sequence
                ON events(workflow_id, sequence_number)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    workflow_id TEXT PRIMARY KEY,
                    sequence_number INTEGER NOT NULL,
                    state JSON NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    @contextmanager
    def _connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, isolation_level='IMMEDIATE')
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def append(self, event: WorkflowEvent) -> None:
        """Append event (ACID guarantees)."""
        with self._connection() as conn:
            conn.execute("""
                INSERT INTO events (workflow_id, event_id, event_type,
                                   timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.workflow_id,
                event.event_id,
                event.event_type,
                event.timestamp.isoformat(),
                json.dumps(event.data)
            ))

    def get_events(self, workflow_id: str,
                   since_sequence: int = 0) -> list[WorkflowEvent]:
        """Read events for workflow (fast with index)."""
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM events
                WHERE workflow_id = ? AND sequence_number > ?
                ORDER BY sequence_number ASC
            """, (workflow_id, since_sequence))

            events = []
            for row in cursor:
                events.append(WorkflowEvent(
                    event_id=row['event_id'],
                    workflow_id=row['workflow_id'],
                    event_type=row['event_type'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    data=json.loads(row['data'])
                ))

            return events

    def get_events_by_type(self, event_type: str) -> list[WorkflowEvent]:
        """Query events by type (fast with index)."""
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM events
                WHERE event_type = ?
                ORDER BY sequence_number ASC
            """, (event_type,))

            return [self._row_to_event(row) for row in cursor]

    def save_snapshot(self, workflow_id: str, state: dict,
                     sequence_number: int) -> None:
        """Save snapshot for compaction."""
        with self._connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO snapshots
                (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                workflow_id,
                sequence_number,
                json.dumps(state),
                datetime.now().isoformat()
            ))

    def get_snapshot(self, workflow_id: str) -> tuple[dict, int] | None:
        """Get latest snapshot for workflow."""
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT state, sequence_number FROM snapshots
                WHERE workflow_id = ?
            """, (workflow_id,))

            row = cursor.fetchone()
            if row:
                return json.loads(row['state']), row['sequence_number']
            return None

    def rebuild_projection(self, workflow_id: str) -> dict:
        """Build state efficiently using snapshot + events."""
        # Get latest snapshot
        snapshot_result = self.get_snapshot(workflow_id)

        if snapshot_result:
            state, sequence_number = snapshot_result
            # Only read events after snapshot
            events = self.get_events(workflow_id, since_sequence=sequence_number)
        else:
            # No snapshot, read all events
            state = {}
            events = self.get_events(workflow_id)

        # Apply events to state
        for event in events:
            state = apply_event(state, event)

        return state
```

**Pros:**
- ✅ ACID guarantees (transactions)
- ✅ Efficient indexing (fast queries by workflow, type, time)
- ✅ Built-in snapshot support
- ✅ Can query across workflows
- ✅ Single file (easy to backup)
- ✅ Concurrent reads/writes handled by SQLite
- ✅ Mature, battle-tested

**Cons:**
- ❌ Binary format (not human-readable)
- ❌ Requires SQL knowledge
- ❌ More complex than flat files

**Best for:** Production use with thousands of events

---

### Option 3: Hybrid (JSONL + SQLite Index)

**Concept:** Store events in human-readable JSONL, index in SQLite for queries.

```
events/
├── beads-y97.events        # Source of truth (JSONL)
├── beads-7gq.events
└── index.db                # SQLite index (can rebuild)
```

**Implementation:**
```python
class HybridEventStore:
    """JSONL for storage, SQLite for indexing."""

    def __init__(self, base_path: Path):
        self.jsonl_store = JSONLEventStore(base_path)
        self.index = SQLiteEventIndex(base_path / "index.db")

    def append(self, event: WorkflowEvent) -> None:
        """Write to both stores."""
        # Write to JSONL (source of truth)
        self.jsonl_store.append(event)

        # Index in SQLite (for fast queries)
        self.index.index_event(event)

    def get_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Read from JSONL (always correct)."""
        return self.jsonl_store.get_events(workflow_id)

    def query_events_by_type(self, event_type: str) -> list[WorkflowEvent]:
        """Query using SQLite index."""
        # Get event locations from index
        locations = self.index.get_event_locations(event_type)

        # Read from JSONL files
        return [self._read_event_at(loc) for loc in locations]

    def rebuild_index(self) -> None:
        """Rebuild SQLite index from JSONL files."""
        self.index.clear()

        for event_file in (self.base_path / "events").glob("*.events"):
            with event_file.open('r') as f:
                for line in f:
                    event = WorkflowEvent(**json.loads(line))
                    self.index.index_event(event)
```

**Pros:**
- ✅ Human-readable source of truth (JSONL)
- ✅ Fast queries (SQLite index)
- ✅ Index can be rebuilt if corrupted
- ✅ Best of both worlds

**Cons:**
- ❌ More complex (two systems)
- ❌ Potential inconsistency (index out of sync)
- ❌ Double storage overhead

---

## Compaction Strategies

### Problem: Unbounded Growth

Event streams grow forever. A long-running workflow might have:
- 1,000 events (small workflow)
- 10,000 events (medium)
- 100,000+ events (large, long-running)

Reading all events every time is slow.

### Solution 1: Snapshots (Event Sourcing Classic)

**Concept:** Periodically save a snapshot of current state, then only replay events after snapshot.

```
Event Stream:
[E1] [E2] [E3] ... [E100] [SNAPSHOT] [E101] [E102] ... [E200]
                      ↑
                    Rebuild state = Load snapshot + replay E101-E200
```

**Implementation:**
```python
class SnapshotStrategy:
    SNAPSHOT_INTERVAL = 100  # Snapshot every 100 events

    def should_snapshot(self, event_count: int) -> bool:
        """Should we create a snapshot?"""
        return event_count > 0 and event_count % self.SNAPSHOT_INTERVAL == 0

    def create_snapshot(self, workflow_id: str, state: dict,
                       sequence_number: int) -> None:
        """Create snapshot of current state."""
        self.event_store.save_snapshot(workflow_id, state, sequence_number)

    def load_state(self, workflow_id: str) -> dict:
        """Load state efficiently using snapshot."""
        # Try to load snapshot
        snapshot_result = self.event_store.get_snapshot(workflow_id)

        if snapshot_result:
            state, last_sequence = snapshot_result
            # Only replay events after snapshot
            events = self.event_store.get_events(
                workflow_id,
                since_sequence=last_sequence
            )
        else:
            # No snapshot, load all events
            state = self._initial_state()
            events = self.event_store.get_events(workflow_id)

        # Apply remaining events
        for event in events:
            state = apply_event(state, event)

        return state
```

**Benefits:**
- ✅ Bounded replay time (max N events where N = snapshot interval)
- ✅ Events still preserved (audit trail intact)
- ✅ Can adjust snapshot frequency based on workflow size

**Tradeoffs:**
- ⚠️ Snapshots take storage space
- ⚠️ Snapshot creation has CPU cost

**Optimization:** Adaptive snapshots based on event count:
```python
def adaptive_snapshot_interval(event_count: int) -> int:
    """Adaptive interval: more events = more frequent snapshots."""
    if event_count < 1000:
        return 100
    elif event_count < 10000:
        return 500
    else:
        return 1000
```

---

### Solution 2: Event Archival (Cold Storage)

**Concept:** Move old events to cold storage (compressed, slower access).

```
Hot Storage (fast):
events/beads-y97.events    [last 1000 events]

Cold Storage (compressed):
archive/beads-y97.events.gz    [older events, compressed]
```

**Implementation:**
```python
class EventArchiver:
    ARCHIVE_THRESHOLD = 1000  # Keep last 1000 events hot

    def archive_old_events(self, workflow_id: str) -> None:
        """Move old events to cold storage."""
        events = self.event_store.get_events(workflow_id)

        if len(events) > self.ARCHIVE_THRESHOLD:
            # Split into hot/cold
            cold_events = events[:-self.ARCHIVE_THRESHOLD]
            hot_events = events[-self.ARCHIVE_THRESHOLD:]

            # Archive old events (compressed)
            archive_file = self.archive_path / f"{workflow_id}.archive.gz"
            with gzip.open(archive_file, 'wt') as f:
                for event in cold_events:
                    f.write(json.dumps(asdict(event)) + '\n')

            # Rewrite hot file with recent events only
            hot_file = self.events_path / f"{workflow_id}.events"
            with hot_file.open('w') as f:
                for event in hot_events:
                    f.write(json.dumps(asdict(event)) + '\n')

    def get_all_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Get all events (hot + cold)."""
        events = []

        # Read from cold storage (if exists)
        archive_file = self.archive_path / f"{workflow_id}.archive.gz"
        if archive_file.exists():
            with gzip.open(archive_file, 'rt') as f:
                for line in f:
                    events.append(WorkflowEvent(**json.loads(line)))

        # Read from hot storage
        hot_events = self.event_store.get_events(workflow_id)
        events.extend(hot_events)

        return events
```

**Benefits:**
- ✅ Hot storage stays small (fast)
- ✅ Compression saves disk space (5-10x reduction)
- ✅ Complete audit trail preserved

**Tradeoffs:**
- ⚠️ Cold reads are slower (uncompress + read)
- ⚠️ Archival process takes time

---

### Solution 3: Event Deletion (Controversial!)

**Concept:** After snapshot, actually delete old events.

**⚠️ WARNING:** This violates event sourcing principles! Use only if:
- No audit trail required
- Storage severely constrained
- Snapshots are trusted

```python
class EventPruner:
    """Delete events older than snapshot (DANGEROUS!)."""

    def prune_events(self, workflow_id: str) -> None:
        """Delete events older than latest snapshot."""
        snapshot_result = self.event_store.get_snapshot(workflow_id)

        if snapshot_result:
            _, sequence_number = snapshot_result

            # Delete events older than snapshot
            with self.event_store._connection() as conn:
                conn.execute("""
                    DELETE FROM events
                    WHERE workflow_id = ? AND sequence_number <= ?
                """, (workflow_id, sequence_number))
```

**Only use if:** You're absolutely certain you don't need audit trail.

---

## Recommended Architecture for Jean Claude

### Event Store: SQLite

**Why:**
- ✅ Single-file database (easy backup/restore)
- ✅ ACID transactions (no data loss)
- ✅ Excellent query performance (indexes)
- ✅ Built-in snapshot support
- ✅ Handles concurrency
- ✅ Python stdlib (no dependencies)
- ✅ Battle-tested reliability

**Why not JSONL:**
- ❌ No built-in indexing
- ❌ Manual locking required
- ❌ Full file scans for queries
- ❌ No snapshot support

### Compaction: Snapshots Every 100 Events

**Why:**
- ✅ Bounded replay time (< 100 events)
- ✅ Preserves audit trail (events not deleted)
- ✅ Automatic (no manual intervention)
- ✅ Adjustable (can tune per workflow size)

**Implementation:**
```python
# In run_two_agent_workflow()
async def run_two_agent_workflow(...):
    event_store = SQLiteEventStore(project_root / "events.db")

    # ... workflow execution ...

    # After each feature
    await event_store.append(FeatureCompleted(...))

    # Check if snapshot needed
    event_count = len(event_store.get_events(workflow_id))
    if event_count % 100 == 0:
        state = build_projection(event_store.get_events(workflow_id))
        event_store.save_snapshot(workflow_id, state, event_count)
```

---

## Storage Growth Analysis

### Typical Workflow:
- 7 features
- ~30 events per feature (planning, start, tests, complete)
- Total: ~200 events

### Event Size:
```python
{
    "event_id": "uuid-...",  # 36 bytes
    "workflow_id": "beads-y97",  # 10-20 bytes
    "event_type": "feature.completed",  # 10-30 bytes
    "timestamp": "2025-12-29T...",  # 20 bytes
    "data": {...}  # 100-500 bytes (feature details)
}
# Average: ~300 bytes per event
```

### Storage Calculation:
```
1 workflow = 200 events × 300 bytes = 60 KB
100 workflows = 6 MB
1000 workflows = 60 MB

With snapshots (every 100 events):
1000 workflows × 2 snapshots avg = 2000 snapshots
Average snapshot size: 5 KB
Total snapshots: 10 MB

Total for 1000 workflows: 60 MB (events) + 10 MB (snapshots) = 70 MB
```

**Conclusion:** Storage is NOT a problem. Even 10,000 workflows = 700 MB (trivial).

---

## Query Performance Analysis

### SQLite with Index:
```sql
-- Query workflow events (with index)
SELECT * FROM events
WHERE workflow_id = 'beads-y97'
ORDER BY sequence_number
```

**Performance:**
- 200 events: < 1ms
- 10,000 events: < 10ms
- 100,000 events: < 100ms

### With Snapshot:
```python
# Load snapshot (1 query)
snapshot, sequence = get_snapshot('beads-y97')  # < 1ms

# Load events after snapshot (indexed query)
events = get_events('beads-y97', since_sequence=sequence)  # < 5ms

# Total: < 6ms for any workflow size
```

**Conclusion:** Query performance is excellent even at scale.

---

## Final Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Event Store: events.db (SQLite)                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Table: events                                               │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ sequence | workflow_id | event_type | timestamp | data  ││
│ │ 1        | beads-y97   | started    | 2025...   | {...} ││
│ │ 2        | beads-y97   | planned    | 2025...   | {...} ││
│ │ 3        | beads-y97   | completed  | 2025...   | {...} ││
│ │ ...                                                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Table: snapshots                                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ workflow_id | sequence | state              | created  ││
│ │ beads-y97   | 100      | {features:[...]}   | 2025...  ││
│ │ beads-7gq   | 200      | {phase:"impl",...} | 2025...  ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Indexes:                                                    │
│ - idx_workflow_sequence (workflow_id, sequence_number)     │
│ - idx_event_type (event_type)                              │
│ - idx_timestamp (timestamp)                                │
└─────────────────────────────────────────────────────────────┘

Compaction Strategy:
- Snapshot every 100 events
- Events never deleted (audit trail)
- Queries use snapshot + recent events (fast)

Storage: 70 MB for 1000 workflows (negligible)
Query Time: < 6ms for any workflow size
```

---

## Migration from Current System

### Phase 1: Add Event Store Alongside Current State
```python
# In run_two_agent_workflow()
# Write to both systems
event_store.append(FeatureCompleted(...))  # NEW
state.save()  # OLD (keep for compatibility)
```

### Phase 2: Dashboard Reads from Events
```python
# In dashboard
# Read from events, not state.json
events = event_store.get_events(workflow_id)
state = build_projection(events)
```

### Phase 3: Remove state.json Writes
```python
# Only events
event_store.append(FeatureCompleted(...))
# state.save()  ← remove
```

---

## Testing Strategy

### Event Store Tests
```python
def test_append_and_read():
    store = SQLiteEventStore(tmp_path / "test.db")
    event = WorkflowEvent(workflow_id="test", event_type="started", ...)

    store.append(event)
    events = store.get_events("test")

    assert len(events) == 1
    assert events[0].event_type == "started"

def test_snapshot_compaction():
    store = SQLiteEventStore(tmp_path / "test.db")

    # Add 150 events
    for i in range(150):
        store.append(WorkflowEvent(...))

    # Create snapshot at 100
    state = build_projection(store.get_events("test")[:100])
    store.save_snapshot("test", state, 100)

    # Load state efficiently
    rebuilt_state = store.rebuild_projection("test")

    # Should only replay 50 events (after snapshot)
    assert rebuilt_state == expected_state

def test_concurrent_writes():
    store = SQLiteEventStore(tmp_path / "test.db")

    # Multiple threads writing to different workflows
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(write_events, store, f"workflow-{i}")
            for i in range(100)
        ]
        wait(futures)

    # All events should be present
    assert total_events == 1000
```

---

## Summary

**Recommended Event Store:** SQLite with snapshots

**Why:**
- Single-file simplicity
- ACID guarantees
- Excellent performance
- Built-in snapshot support
- No external dependencies

**Compaction:** Snapshots every 100 events
- Fast reads (< 6ms)
- Audit trail preserved
- Storage efficient (70 MB for 1000 workflows)

**Migration:** Incremental (3 phases)
- Phase 1: Dual-write (events + state.json)
- Phase 2: Dashboard reads events
- Phase 3: Remove state.json

This architecture scales to 10,000+ workflows while maintaining:
- ✅ Complete audit trail
- ✅ Fast queries (< 10ms)
- ✅ Real-time monitoring
- ✅ Time-travel debugging
- ✅ Minimal storage overhead
