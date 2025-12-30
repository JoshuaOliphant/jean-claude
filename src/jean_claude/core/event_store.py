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
from typing import Union, Optional
import sqlite3

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