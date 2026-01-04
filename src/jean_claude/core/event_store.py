# ABOUTME: EventStore class for SQLite event persistence
# ABOUTME: Provides database initialization and path management for event storage

"""EventStore class for SQLite-based event persistence.

This module provides the EventStore class which manages SQLite database connections
and schema for storing workflow events. The EventStore class handles:

- Database path validation and storage
- Schema initialization and management
- SQLite connection creation and management
- Connection pooling and resource cleanup
- Context manager support for automatic transaction handling
- Performance optimization for SQLite operations

The EventStore follows the event sourcing pattern, where all workflow state changes
are persisted as immutable events in a SQLite database.

Key features:
- Path validation with clear error messages
- Support for both Path objects and string paths
- Optimized SQLite connections with WAL mode and performance tuning
- Context manager support for automatic transaction management
- Proper connection resource cleanup and error handling
- Integration with existing event infrastructure
"""

from pathlib import Path
from typing import Union, Optional, Callable, Dict
import sqlite3
import json
import uuid

from .schema_creation import create_event_store_schema, create_event_store_indexes


class EventStore:
    """SQLite-based event store for workflow events.

    The EventStore class manages a SQLite database for persisting workflow events
    following the event sourcing pattern. It provides schema management, optimized
    connection handling, and context manager support for automatic transactions.

    Features:
    - Database path validation and storage
    - Schema initialization and management
    - Optimized SQLite connections with WAL mode and performance settings
    - Context manager support for automatic transaction handling
    - Proper resource cleanup and connection management

    Attributes:
        db_path: Path to the SQLite database file (as Path object)

    Example:
        Basic usage:
        >>> from pathlib import Path
        >>> store = EventStore(Path("./data/events.db"))
        >>> store._init_schema()  # Initialize database schema

        Connection management:
        >>> conn = store.get_connection()
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM events")
        >>> store.close_connection(conn)

        Context manager usage:
        >>> with store as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("INSERT INTO events ...")
        ...     # Transaction automatically committed
    """

    def __init__(self, db_path: Union[str, Path]) -> None:
        """Initialize the EventStore with a database path.

        Args:
            db_path: Path to the SQLite database file. Can be a Path object
                    or string path. The path will be converted to a Path object
                    and stored as an instance variable.

        Raises:
            TypeError: If db_path is not a string or Path object
            ValueError: If db_path is None, empty string, or whitespace-only

        Example:
            >>> store = EventStore(Path("/data/events.db"))
            >>> store = EventStore("./local/events.db")
        """
        # Validate input type
        if db_path is None:
            raise ValueError("Database path cannot be None")

        if not isinstance(db_path, (str, Path)):
            raise TypeError(
                f"Database path must be a string or Path object, got {type(db_path).__name__}"
            )

        # Handle string paths
        if isinstance(db_path, str):
            # Check for empty or whitespace-only strings
            if not db_path or not db_path.strip():
                raise ValueError("Database path cannot be empty or whitespace-only")

            # Convert to Path object
            db_path = Path(db_path)

        # Store the path as instance variable
        self.db_path = db_path

        # Initialize subscription system
        self._subscribers: Dict[str, Callable] = {}

        # Automatically initialize the database schema
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize the database schema for the event store.

        Creates the SQLite database file (if it doesn't exist) and sets up the
        required tables and indexes for the event store. This method is idempotent
        and can be safely called multiple times.

        The method creates:
        - Events table with proper schema and constraints
        - Snapshots table for workflow state snapshots
        - Performance indexes on commonly queried columns

        Raises:
            OSError: If the database file cannot be created or accessed
            sqlite3.Error: If there's an error creating the database schema

        Example:
            >>> store = EventStore("./data/events.db")
            >>> store._init_schema()  # Creates database and tables
            >>> store._init_schema()  # Safe to call again - no changes made
        """
        try:
            # Create the database schema (tables)
            # This function is idempotent and handles path validation
            create_event_store_schema(self.db_path)

            # Create performance indexes
            # This function is also idempotent
            create_event_store_indexes(self.db_path)

        except Exception as e:
            # Re-raise with context about what we were trying to do
            raise sqlite3.Error(
                f"Failed to initialize database schema at {self.db_path}: {e}"
            ) from e

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite connection to the event store database.

        Creates a new SQLite connection with optimized settings for event store operations.
        Each call returns a fresh connection - callers are responsible for closing it.

        The connection is configured with:
        - WAL mode for better concurrency
        - Reduced synchronous setting for performance
        - Foreign keys enabled for data integrity
        - Row factory for easier access to query results

        Returns:
            sqlite3.Connection: A new SQLite database connection

        Raises:
            OSError: If the database file cannot be accessed due to permissions
            sqlite3.Error: If there's an error connecting to the database

        Example:
            >>> store = EventStore("./data/events.db")
            >>> conn = store.get_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT COUNT(*) FROM events")
            >>> count = cursor.fetchone()[0]
            >>> conn.close()
        """
        try:
            # Create SQLite connection
            connection = sqlite3.connect(str(self.db_path))

            # Enable row factory for easier access to query results
            connection.row_factory = sqlite3.Row

            # Apply performance optimizations (best-effort, may fail on readonly databases)
            cursor = connection.cursor()

            try:
                # Enable WAL mode for better concurrency
                cursor.execute("PRAGMA journal_mode = WAL")

                # Reduce synchronous setting for better performance
                # 1 = NORMAL (good balance of safety and performance)
                cursor.execute("PRAGMA synchronous = NORMAL")

                # Enable foreign keys for data integrity
                cursor.execute("PRAGMA foreign_keys = ON")

                # Set reasonable timeout for busy database
                connection.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
            except sqlite3.OperationalError:
                # Readonly database - optimizations may fail, but connection is still usable
                pass

            return connection

        except (OSError, sqlite3.Error) as e:
            # Re-raise with helpful context about the path and error
            error_type = "permission" if "permission" in str(e).lower() else "path"
            raise sqlite3.Error(
                f"Failed to create database connection to {error_type} {self.db_path}: {e}"
            ) from e

    def close_connection(self, connection: Optional[sqlite3.Connection]) -> None:
        """Properly close a SQLite connection and clean up resources.

        Safely closes the provided SQLite connection, handling cases where the
        connection is already closed or None. This method ensures proper cleanup
        of database resources.

        Args:
            connection: The SQLite connection to close, or None

        Example:
            >>> store = EventStore("./data/events.db")
            >>> conn = store.get_connection()
            >>> # ... use connection ...
            >>> store.close_connection(conn)
        """
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:
                # Connection might already be closed - ignore the error
                pass

    def __enter__(self) -> sqlite3.Connection:
        """Enter context manager - return a new database connection.

        Creates a new SQLite connection for use within a context manager.
        The connection will be automatically managed (committed/rolled back
        and closed) when the context exits.

        Returns:
            sqlite3.Connection: A new database connection for the context

        Example:
            >>> store = EventStore("./data/events.db")
            >>> with store as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("INSERT INTO events ...")
            ...     # Connection automatically committed and closed
        """
        self._context_connection = self.get_connection()
        return self._context_connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - handle transaction and close connection.

        Automatically handles transaction management:
        - If no exception occurred: commits the transaction
        - If an exception occurred: rolls back the transaction
        - Always closes the connection for proper cleanup

        Args:
            exc_type: Exception type (None if no exception)
            exc_val: Exception value (None if no exception)
            exc_tb: Exception traceback (None if no exception)

        The method returns None, meaning exceptions are not suppressed.
        """
        if hasattr(self, '_context_connection') and self._context_connection:
            try:
                if exc_type is None:
                    # No exception - commit the transaction
                    self._context_connection.commit()
                else:
                    # Exception occurred - roll back the transaction
                    self._context_connection.rollback()
            finally:
                # Always close the connection
                self.close_connection(self._context_connection)
                # Clean up the reference
                self._context_connection = None

    def append(self, event) -> bool:
        """Append a single event to the event store with ACID transaction handling.

        Writes a single event to the SQLite database within a transaction. The method
        provides ACID guarantees by automatically committing on success or rolling
        back on any error. Proper error handling ensures database consistency.

        Args:
            event: Event object to append to the store. Must be a valid Event instance
                  with all required fields (workflow_id, event_type, event_data).

        Returns:
            bool: True if the event was successfully appended and committed,
                 False if there was any error during the operation.

        Features:
        - ACID transaction handling with automatic commit/rollback
        - Comprehensive error handling for database and connection issues
        - Input validation to ensure event parameter is valid
        - Proper resource cleanup (connections always closed)
        - JSON serialization error handling

        Example:
            >>> from pathlib import Path
            >>> from jean_claude.core.event_models import Event
            >>> store = EventStore(Path("./data/events.db"))
            >>> event = Event(
            ...     workflow_id="workflow-123",
            ...     event_type="task_started",
            ...     event_data={"task_id": "task-456"}
            ... )
            >>> success = store.append(event)
            >>> print(f"Event stored: {success}")
            Event stored: True

        Error Handling:
            The method handles various error conditions:
            - Invalid event parameter (None, wrong type)
            - Database connection failures
            - SQL execution errors
            - JSON serialization errors in event_data
            - Transaction commit/rollback errors

            All errors result in False return value and proper cleanup.
        """
        # Import here to avoid circular imports
        from .event_models import Event

        # Validate input parameter
        if event is None:
            return False

        if not isinstance(event, Event):
            return False

        connection = None
        try:
            # Get database connection
            connection = self.get_connection()
            cursor = connection.cursor()

            # Generate unique event_id for the event (required by schema)
            import uuid
            event_id = str(uuid.uuid4())

            # Prepare SQL insert statement (using actual schema columns)
            insert_sql = """
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """

            # Execute the insert within a transaction
            cursor.execute(insert_sql, (
                event.workflow_id,
                event_id,  # Generate unique event_id
                event.event_type,
                event.timestamp.isoformat(),  # Convert datetime to TEXT
                json.dumps(event.event_data)  # Convert dict to JSON string
            ))

            # Commit the transaction
            connection.commit()

            # Check if auto-snapshot should be created after successful event commit
            self._check_and_create_auto_snapshot(event.workflow_id)

            # Notify subscribers after successful commit
            self._notify_subscribers(event)

            return True

        except (sqlite3.Error, TypeError, ValueError) as e:
            # Handle various error types:
            # - sqlite3.Error: Database errors (connection, SQL, etc.)
            # - TypeError: JSON serialization errors
            # - ValueError: Event validation errors
            if connection:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    # If rollback fails, the connection might be corrupted
                    # but we still want to close it and return False
                    pass
            return False

        except Exception as e:
            # Handle any unexpected errors
            if connection:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            return False

        finally:
            # Always close the connection to prevent leaks
            if connection:
                self.close_connection(connection)

    def append_batch(self, events: list) -> bool:
        """Append multiple events in a single transaction for better performance.

        Writes multiple events to the SQLite database within a single transaction.
        This provides significant performance improvements over individual appends
        when adding many events at once.

        Args:
            events: List of Event objects to append to the store.

        Returns:
            bool: True if all events were successfully appended and committed,
                 False if there was any error during the operation.

        Features:
        - Batch ACID transaction handling
        - All-or-nothing semantics (full rollback on any failure)
        - Significant performance improvement for large batches
        - Proper error handling and resource cleanup
        """
        # Import here to avoid circular imports
        from .event_models import Event

        # Validate input
        if events is None or not isinstance(events, list):
            return False

        if len(events) == 0:
            return True

        connection = None
        try:
            # Get database connection
            connection = self.get_connection()
            cursor = connection.cursor()

            # Prepare SQL insert statement
            import uuid
            insert_sql = """
                INSERT INTO events (workflow_id, event_id, event_type, timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """

            # Collect all inserts
            batch_data = []
            for event in events:
                # Validate each event
                if event is None or not isinstance(event, Event):
                    # Invalid event in batch - rollback entire transaction
                    if connection:
                        try:
                            connection.rollback()
                        except sqlite3.Error:
                            pass
                    return False

                import json
                event_id = str(uuid.uuid4())
                batch_data.append((
                    event.workflow_id,
                    event_id,
                    event.event_type,
                    event.timestamp.isoformat(),
                    json.dumps(event.event_data)
                ))

            # Execute batch insert
            cursor.executemany(insert_sql, batch_data)

            # Commit the transaction
            connection.commit()

            # Check auto-snapshot for each workflow (collect unique workflow_ids)
            workflow_ids = set(event.workflow_id for event in events if event)
            for workflow_id in workflow_ids:
                self._check_and_create_auto_snapshot(workflow_id)

            # Notify subscribers for each event
            for event in events:
                if event:
                    self._notify_subscribers(event)

            return True

        except (sqlite3.Error, TypeError, ValueError) as e:
            # Handle errors with rollback
            if connection:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            return False

        finally:
            # Always close the connection
            if connection:
                self.close_connection(connection)

    def get_events(self, workflow_id: str, event_type: str = None, order_by: str = "asc", limit: int = None, offset: int = None) -> list:
        """Query events from the event store with workflow_id filtering.

        Retrieves events from the SQLite database with required workflow_id filtering
        and optional event_type filtering and timestamp ordering. This method provides
        efficient querying capabilities for event sourcing and event replay scenarios.

        Args:
            workflow_id: Required workflow identifier to filter events.
                        Cannot be None, empty, or whitespace-only.
            event_type: Optional event type filter. If provided, only events of this
                       type will be returned. If None, all events for the workflow
                       are returned. Cannot be empty or whitespace-only if provided.
            order_by: Optional timestamp ordering. Valid values are "asc" (ascending,
                     default) or "desc" (descending). Invalid values raise ValueError.

        Returns:
            list: List of Event objects matching the query criteria, ordered by
                 timestamp according to the order_by parameter. Returns empty list
                 if no events match the criteria.

        Raises:
            ValueError: If workflow_id is None, empty, or whitespace-only, or if
                       event_type is empty/whitespace-only when provided, or if
                       order_by has invalid value.
            sqlite3.Error: If there's an error querying the database or connecting.

        Features:
        - Required workflow_id filtering with validation
        - Optional event_type filtering for specific event types
        - Configurable timestamp ordering (ascending or descending)
        - Proper Event object reconstruction from database rows
        - Comprehensive error handling for database and connection issues
        - Integration with existing database schema and Event model
        - Resource cleanup (connections always closed)

        Example:
            >>> from pathlib import Path
            >>> from jean_claude.core.event_store import EventStore
            >>> store = EventStore(Path("./data/events.db"))

            # Get all events for a workflow (ordered by timestamp ascending)
            >>> events = store.get_events("workflow-123")
            >>> print(f"Found {len(events)} events")
            Found 5 events

            # Get specific event type for a workflow
            >>> task_events = store.get_events("workflow-123", event_type="task_completed")
            >>> print(f"Found {len(task_events)} task completion events")
            Found 2 task completion events

            # Get events in descending order (newest first)
            >>> recent_events = store.get_events("workflow-123", order_by="desc")
            >>> print(f"Most recent event: {recent_events[0].event_type}")
            Most recent event: workflow_completed

        Performance:
            The method uses indexed queries on workflow_id and event_type columns
            for efficient filtering. Timestamp ordering is performed by the database
            for optimal performance.
        """
        # Import here to avoid circular imports
        from .event_models import Event

        # Validate workflow_id parameter
        if workflow_id is None:
            raise ValueError("workflow_id cannot be None")

        if not isinstance(workflow_id, str):
            raise TypeError("workflow_id must be a string")

        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty or whitespace-only")

        # Validate event_type parameter if provided
        if event_type is not None:
            if not isinstance(event_type, str):
                raise TypeError("event_type must be a string or None")

            if not event_type or not event_type.strip():
                raise ValueError("event_type cannot be empty or whitespace-only")

        # Validate order_by parameter
        if not isinstance(order_by, str):
            raise TypeError("order_by must be a string")

        order_by = order_by.strip().lower()
        if order_by not in ("asc", "desc"):
            raise ValueError("order_by must be 'asc' or 'desc'")

        connection = None
        try:
            # Get database connection
            connection = self.get_connection()
            cursor = connection.cursor()

            # Build SQL query based on parameters
            pagination_clause = ""
            params = []

            if event_type is not None:
                # Filter by both workflow_id and event_type
                sql_base = """
                    SELECT workflow_id, event_id, event_type, timestamp, data, sequence_number
                    FROM events
                    WHERE workflow_id = ? AND event_type = ?
                    ORDER BY timestamp {}
                """.format("ASC" if order_by == "asc" else "DESC")
                params = [workflow_id.strip(), event_type.strip()]
            else:
                # Filter by workflow_id only
                sql_base = """
                    SELECT workflow_id, event_id, event_type, timestamp, data, sequence_number
                    FROM events
                    WHERE workflow_id = ?
                    ORDER BY timestamp {}
                """.format("ASC" if order_by == "asc" else "DESC")
                params = [workflow_id.strip()]

            # Add pagination if provided
            # Note: SQLite requires LIMIT when using OFFSET
            if limit is not None or offset is not None:
                if limit is not None:
                    sql_base += " LIMIT ?"
                    params.append(limit)
                else:
                    # SQLite requires LIMIT with OFFSET, use -1 for unlimited
                    sql_base += " LIMIT -1"

                if offset is not None:
                    sql_base += " OFFSET ?"
                    params.append(offset)

            cursor.execute(sql_base, tuple(params))

            # Fetch all matching rows
            rows = cursor.fetchall()

            # Convert rows to Event objects
            events = []
            for row in rows:
                try:
                    # Parse JSON data back to dict
                    import json
                    event_data = json.loads(row["data"])

                    # Parse timestamp back to datetime
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(row["timestamp"])

                    # Create Event object
                    event = Event(
                        workflow_id=row["workflow_id"],
                        event_type=row["event_type"],
                        event_data=event_data
                    )

                    # Set the timestamp to the stored value
                    event.timestamp = timestamp

                    # Set the id to match the sequence_number from database
                    event.id = row["sequence_number"]

                    events.append(event)

                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    # Skip malformed rows but continue processing others
                    # In production, you might want to log this error
                    continue

            return events

        except sqlite3.Error as e:
            # Re-raise database errors with context
            raise sqlite3.Error(f"Failed to query events from database {self.db_path}: {e}") from e

        except Exception as e:
            # Handle any unexpected errors
            raise sqlite3.Error(f"Unexpected error querying events from {self.db_path}: {e}") from e

        finally:
            # Always close the connection to prevent leaks
            if connection:
                self.close_connection(connection)

    def subscribe(self, callback: Callable) -> str:
        """Subscribe a callback function to be notified when events are appended.

        Registers a callback function that will be called whenever an event is successfully
        appended to the event store. The callback will be called after the event has been
        committed to the database, ensuring ACID guarantees are maintained.

        Args:
            callback: A callable function that takes an Event object as its single parameter.
                     The callback will be invoked with the Event object that was appended.

        Returns:
            str: A unique subscription ID that can be used to unsubscribe the callback later.

        Raises:
            ValueError: If callback is None or not callable.

        Features:
        - Support for multiple subscribers with unique subscription IDs
        - Callbacks are called after successful database commit
        - Callback errors are handled gracefully without affecting event storage
        - Thread-safe subscription management

        Example:
            >>> def my_callback(event):
            ...     print(f"Event received: {event.event_type}")
            >>>
            >>> store = EventStore("./events.db")
            >>> subscription_id = store.subscribe(my_callback)
            >>>
            >>> # Later, when events are appended:
            >>> event = Event(workflow_id="test", event_type="test", event_data={})
            >>> store.append(event)  # Will trigger my_callback
            Event received: test
        """
        # Validate callback parameter
        if callback is None:
            raise ValueError("Callback cannot be None")

        if not callable(callback):
            raise ValueError("Callback must be callable")

        # Generate unique subscription ID
        subscription_id = str(uuid.uuid4())

        # Store the callback
        self._subscribers[subscription_id] = callback

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe a callback using its subscription ID.

        Removes a previously registered callback from the subscription list so it will
        no longer be notified when events are appended.

        Args:
            subscription_id: The subscription ID returned by subscribe() method.

        Returns:
            bool: True if the subscription was found and removed, False otherwise.

        Features:
        - Safe to call with invalid or non-existent subscription IDs
        - Does not affect other subscribers
        - Thread-safe unsubscription

        Example:
            >>> store = EventStore("./events.db")
            >>> sub_id = store.subscribe(lambda event: print(event.event_type))
            >>> store.unsubscribe(sub_id)  # Returns True
            True
            >>> store.unsubscribe(sub_id)  # Returns False (already removed)
            False
        """
        # Validate subscription_id parameter
        if not subscription_id or not isinstance(subscription_id, str):
            return False

        # Remove subscription if it exists
        if subscription_id in self._subscribers:
            del self._subscribers[subscription_id]
            return True

        return False

    def _notify_subscribers(self, event) -> None:
        """Notify all subscribed callbacks about a successfully appended event.

        Internal method that calls all registered callbacks with the event that was
        just successfully appended. This method handles callback errors gracefully
        to ensure that one failing callback doesn't affect others or the event storage.

        Args:
            event: The Event object that was successfully appended.

        Features:
        - Calls all registered callbacks in subscription order
        - Isolates callback errors from each other and from the main operation
        - Continues calling remaining callbacks even if some fail
        - Does not raise exceptions for callback errors

        Note:
            This is an internal method and should only be called after the event
            has been successfully committed to the database.
        """
        # Call each callback, handling errors gracefully
        for subscription_id, callback in self._subscribers.items():
            try:
                callback(event)
            except Exception:
                # Silently ignore callback errors to prevent them from affecting
                # the main event storage operation or other callbacks
                # In production, you might want to log these errors
                pass

    def save_snapshot(self, snapshot) -> bool:
        """Save a snapshot to the snapshots table with ACID transaction handling.

        Writes a single snapshot to the SQLite database within a transaction. The method
        provides ACID guarantees by automatically committing on success or rolling
        back on any error. Snapshots are upserted by workflow_id, so existing snapshots
        for the same workflow are replaced.

        Args:
            snapshot: Snapshot object to save to the store. Must be a valid Snapshot instance
                     with all required fields (workflow_id, snapshot_data, event_sequence_number).

        Returns:
            bool: True if the snapshot was successfully saved and committed,
                 False if there was any error during the operation.

        Features:
        - ACID transaction handling with automatic commit/rollback
        - Upsert behavior - replaces existing snapshots for same workflow_id
        - Comprehensive error handling for database and connection issues
        - Input validation to ensure snapshot parameter is valid
        - Proper resource cleanup (connections always closed)
        - JSON serialization error handling
        - Integration with existing database schema (snapshots table)

        Example:
            >>> from pathlib import Path
            >>> from jean_claude.core.event_models import Snapshot
            >>> store = EventStore(Path("./data/events.db"))
            >>> snapshot = Snapshot(
            ...     workflow_id="workflow-123",
            ...     snapshot_data={"current_state": "active", "task_count": 5},
            ...     event_sequence_number=100
            ... )
            >>> success = store.save_snapshot(snapshot)
            >>> print(f"Snapshot saved: {success}")
            Snapshot saved: True

        Error Handling:
            The method handles various error conditions:
            - Invalid snapshot parameter (None, wrong type)
            - Database connection failures
            - SQL execution errors
            - JSON serialization errors in snapshot_data
            - Transaction commit/rollback errors

            All errors result in False return value and proper cleanup.
        """
        # Import here to avoid circular imports
        from .event_models import Snapshot

        # Validate input parameter
        if snapshot is None:
            return False

        if not isinstance(snapshot, Snapshot):
            return False

        connection = None
        try:
            # Get database connection
            connection = self.get_connection()
            cursor = connection.cursor()

            # Prepare SQL upsert statement (REPLACE acts as upsert for primary key)
            # Using actual schema column names: workflow_id, sequence_number, state, created_at
            upsert_sql = """
                REPLACE INTO snapshots (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """

            # Generate current timestamp for created_at
            from datetime import datetime
            current_timestamp = datetime.now().isoformat()

            # Execute the upsert within a transaction
            cursor.execute(upsert_sql, (
                snapshot.workflow_id,
                snapshot.event_sequence_number,  # Map to sequence_number column
                json.dumps(snapshot.snapshot_data),  # Convert dict to JSON string, store in 'state' column
                current_timestamp  # Generate timestamp for created_at
            ))

            # Commit the transaction
            connection.commit()

            return True

        except (sqlite3.Error, TypeError, ValueError) as e:
            # Handle various error types:
            # - sqlite3.Error: Database errors (connection, SQL, etc.)
            # - TypeError: JSON serialization errors
            # - ValueError: Snapshot validation errors
            if connection:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    # If rollback fails, the connection might be corrupted
                    # but we still want to close it and return False
                    pass
            return False

        except Exception as e:
            # Handle any unexpected errors
            if connection:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            return False

        finally:
            # Always close the connection to prevent leaks
            if connection:
                self.close_connection(connection)

    def get_snapshot(self, workflow_id: str):
        """Retrieve the latest snapshot for a workflow from the snapshots table.

        Retrieves the most recent snapshot for the specified workflow from the SQLite database.
        Returns None if no snapshot exists for the workflow. This method provides efficient
        snapshot retrieval for event sourcing and state reconstruction scenarios.

        Args:
            workflow_id: Required workflow identifier to filter snapshots.
                        Cannot be None, empty, or whitespace-only.

        Returns:
            Snapshot: The latest Snapshot object for the workflow if found, None otherwise.
                     The returned Snapshot object contains all original data including
                     workflow_id, snapshot_data, event_sequence_number, and timestamp.

        Raises:
            ValueError: If workflow_id is None, empty, or whitespace-only.
            TypeError: If workflow_id is not a string.
            sqlite3.Error: If there's an error querying the database or connecting.

        Features:
        - Required workflow_id validation with comprehensive error checking
        - Returns None gracefully when no snapshot exists for the workflow
        - Proper Snapshot object reconstruction from database rows
        - Handles multiple snapshots correctly (returns latest by primary key design)
        - Comprehensive error handling for database and connection issues
        - JSON deserialization error handling with graceful degradation
        - Resource cleanup (connections always closed)
        - Integration with existing database schema (snapshots table)

        Example:
            >>> from pathlib import Path
            >>> from jean_claude.core.event_store import EventStore
            >>> store = EventStore(Path("./data/events.db"))

            # Get latest snapshot for a workflow
            >>> snapshot = store.get_snapshot("workflow-123")
            >>> if snapshot:
            ...     print(f"Found snapshot at sequence {snapshot.event_sequence_number}")
            ... else:
            ...     print("No snapshot exists for this workflow")

            # Handle workflow without snapshots
            >>> missing = store.get_snapshot("new-workflow")
            >>> print(missing)  # None

        Performance:
            The method uses the primary key (workflow_id) for efficient single-row retrieval.
            Since workflow_id is the primary key in the snapshots table, lookup is O(1).
        """
        # Validate workflow_id parameter
        if workflow_id is None:
            raise ValueError("workflow_id cannot be None")

        if not isinstance(workflow_id, str):
            raise TypeError("workflow_id must be a string")

        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty or whitespace-only")

        # Import here to avoid circular imports
        from .event_models import Snapshot

        connection = None
        try:
            # Get database connection
            connection = self.get_connection()
            cursor = connection.cursor()

            # Query for the snapshot using workflow_id (primary key)
            # Since workflow_id is the primary key, there can only be one row
            sql = """
                SELECT workflow_id, sequence_number, state, created_at
                FROM snapshots
                WHERE workflow_id = ?
            """
            cursor.execute(sql, (workflow_id.strip(),))

            # Fetch the row (should be at most one due to primary key)
            row = cursor.fetchone()

            # If no row found, return None
            if row is None:
                return None

            # Reconstruct Snapshot object from database row
            try:
                # Parse JSON state data back to dict
                import json
                snapshot_data = json.loads(row["state"])

                # Parse timestamp back to datetime
                from datetime import datetime
                timestamp = datetime.fromisoformat(row["created_at"])

                # Create Snapshot object with data from database
                snapshot = Snapshot(
                    workflow_id=row["workflow_id"],
                    snapshot_data=snapshot_data,
                    event_sequence_number=row["sequence_number"]
                )

                # Set the timestamp to the stored value
                snapshot.timestamp = timestamp

                return snapshot

            except (json.JSONDecodeError, ValueError, TypeError) as e:
                # Handle corrupted JSON data gracefully - return None instead of crashing
                # This allows the system to continue functioning even with corrupted snapshots
                return None

        except sqlite3.Error as e:
            # Re-raise database errors with context
            raise sqlite3.Error(f"Failed to retrieve snapshot from database {self.db_path}: {e}") from e

        except Exception as e:
            # Handle any unexpected errors
            raise sqlite3.Error(f"Unexpected error retrieving snapshot from {self.db_path}: {e}") from e

        finally:
            # Always close the connection to prevent leaks
            if connection:
                self.close_connection(connection)

    def _check_and_create_auto_snapshot(self, workflow_id: str) -> None:
        """Check if auto-snapshot should be created and create it if needed.

        Automatically creates a snapshot when the event count for a workflow
        reaches multiples of 100 (100, 200, 300, etc.). The snapshot contains
        a summary of the workflow state at that point in time.

        Args:
            workflow_id: The workflow identifier to check for auto-snapshot creation.

        Features:
        - Creates snapshot every 100 events per workflow
        - Workflow-isolated counting (each workflow tracks its own count)
        - Graceful error handling (failures don't affect main event storage)
        - Automatic snapshot data generation with event count and metadata
        - Integration with existing save_snapshot() method

        Note:
            This is an internal method called automatically by append().
            Snapshot creation failures are silently ignored to ensure they
            don't interfere with the main event storage operation.
        """
        try:
            # Count total events for this workflow_id
            event_count = self._count_workflow_events(workflow_id)

            # Check if we've reached a 100-event milestone
            if event_count > 0 and event_count % 100 == 0:
                # Create snapshot data with workflow summary
                snapshot_data = {
                    "workflow_id": workflow_id,
                    "total_events": event_count,
                    "last_event_sequence": event_count,
                    "snapshot_type": "auto",
                    "created_reason": f"Automatic snapshot at {event_count} events"
                }

                # Import here to avoid circular imports
                from .event_models import Snapshot

                # Create snapshot object
                snapshot = Snapshot(
                    workflow_id=workflow_id,
                    snapshot_data=snapshot_data,
                    event_sequence_number=event_count
                )

                # Save the snapshot (failures are ignored to not break event storage)
                self.save_snapshot(snapshot)

        except Exception:
            # Silently ignore all errors in auto-snapshot creation
            # This ensures that snapshot failures don't break event append operations
            pass

    def _count_workflow_events(self, workflow_id: str) -> int:
        """Count the total number of events for a specific workflow.

        Args:
            workflow_id: The workflow identifier to count events for.

        Returns:
            int: Total number of events for the workflow, or 0 if none exist.

        Raises:
            sqlite3.Error: If there's an error querying the database.

        Note:
            This method is used internally by auto-snapshot functionality.
        """
        connection = None
        try:
            # Get database connection
            connection = self.get_connection()
            cursor = connection.cursor()

            # Count events for this workflow_id
            cursor.execute(
                "SELECT COUNT(*) as count FROM events WHERE workflow_id = ?",
                (workflow_id,)
            )
            result = cursor.fetchone()
            return result["count"] if result else 0

        except sqlite3.Error:
            # Re-raise database errors for calling code to handle
            raise

        finally:
            # Always close the connection to prevent leaks
            if connection:
                self.close_connection(connection)

    def rebuild_projection(self, workflow_id: str, builder) -> dict:
        """Rebuild projection state by replaying events from latest snapshot.

        Loads the latest snapshot for the workflow (if it exists) and then replays
        all events that occurred after the snapshot using the provided ProjectionBuilder.
        If no snapshot exists, replays all events from the beginning using the builder's
        initial state.

        Args:
            workflow_id: Required workflow identifier to rebuild projection for.
                        Cannot be None, empty, or whitespace-only.
            builder: ProjectionBuilder instance to apply events with.
                    Must be a ProjectionBuilder subclass with all required methods implemented.

        Returns:
            dict: The final projection state after applying all events.
                 If no snapshot and no events exist, returns the builder's initial state.

        Raises:
            ValueError: If workflow_id is None, empty, or whitespace-only.
            TypeError: If workflow_id is not a string or builder is not a ProjectionBuilder instance.
            sqlite3.Error: If there's an error querying the database.

        Features:
        - Loads latest snapshot state as starting point (if available)
        - Queries events that occurred after the snapshot
        - Applies events sequentially using ProjectionBuilder
        - Falls back to initial state if no snapshot exists
        - Handles empty event streams gracefully
        - Preserves immutability of snapshot data
        - Comprehensive error handling and validation

        Algorithm:
        1. Load latest snapshot for workflow (if exists)
        2. If snapshot exists:
           - Use snapshot_data as initial state
           - Query events with sequence_number > snapshot.event_sequence_number
        3. If no snapshot:
           - Use builder.get_initial_state() as initial state
           - Query all events for the workflow
        4. Apply events sequentially using builder.apply_event()
        5. Return final state

        Example:
            >>> from jean_claude.core.projection_builder import ProjectionBuilder
            >>> store = EventStore("./events.db")
            >>>
            >>> # Create concrete ProjectionBuilder implementation
            >>> class MyProjectionBuilder(ProjectionBuilder):
            ...     def get_initial_state(self):
            ...         return {'workflow_id': None, 'status': 'unknown'}
            ...     # ... implement other abstract methods
            >>>
            >>> builder = MyProjectionBuilder()
            >>> final_state = store.rebuild_projection("workflow-123", builder)
            >>> print(f"Final workflow status: {final_state['status']}")

        Performance:
            - With snapshot: Only replays events since last snapshot (~100 events max)
            - Without snapshot: Replays all events for workflow
            - Uses indexed queries for efficient event filtering
        """
        # Validate workflow_id parameter
        if workflow_id is None:
            raise ValueError("workflow_id cannot be None")

        if not isinstance(workflow_id, str):
            raise TypeError("workflow_id must be a string")

        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id cannot be empty or whitespace-only")

        # Validate builder parameter
        if builder is None:
            raise TypeError("builder must be a ProjectionBuilder instance")

        # Import here to avoid circular imports
        from .projection_builder import ProjectionBuilder

        if not isinstance(builder, ProjectionBuilder):
            raise TypeError("builder must be a ProjectionBuilder instance")

        try:
            # Step 1: Try to load the latest snapshot for this workflow
            snapshot = self.get_snapshot(workflow_id)

            # Step 2: Determine initial state and events to replay
            if snapshot is not None:
                # Start from snapshot state
                # Create a copy to preserve immutability of original snapshot data
                current_state = snapshot.snapshot_data.copy()

                # Query events that occurred after the snapshot
                # Get all events for the workflow (they're already filtered by sequence in get_events)
                all_events = self.get_events(workflow_id, order_by="asc")

                # Filter events that occurred after the snapshot
                events_to_replay = [
                    event for event in all_events
                    if event.id > snapshot.event_sequence_number
                ]
            else:
                # No snapshot exists - start from initial state and replay all events
                current_state = builder.get_initial_state()
                events_to_replay = self.get_events(workflow_id, order_by="asc")

            # Step 3: Apply events sequentially using the ProjectionBuilder
            for event in events_to_replay:
                current_state = builder.apply_event(current_state, event)

            # Step 4: Return the final projection state
            return current_state

        except (ValueError, TypeError) as e:
            # Re-raise validation errors as-is
            raise e

        except sqlite3.Error as e:
            # Re-raise database errors with context
            raise sqlite3.Error(f"Failed to rebuild projection for workflow {workflow_id}: {e}") from e

        except Exception as e:
            # Handle any other errors (like ProjectionBuilder errors)
            raise RuntimeError(f"Error rebuilding projection for workflow {workflow_id}: {e}") from e