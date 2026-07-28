"""Database module for MicroFlask API.

BUG: Connection leak — every call to get_db() opens a new connection
but close() is never called. Over time this exhausts file descriptors
and causes the service to hang.
"""

import sqlite3
import os

DATABASE_PATH = os.environ.get("DB_PATH", "var/microflask.db")
_MAX_CONNECTIONS = int(os.environ.get("MAX_CONNECTIONS", "32"))


def get_db():
    """Return a new SQLite connection.

    BUG: Creates a new connection every call. No caching, no pooling,
    no close(). After _MAX_CONNECTIONS requests, further connections
    are silently refused by SQLite.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        INSERT INTO items (name, price) VALUES
            ('Widget', 9.99),
            ('Gadget', 24.99),
            ('Doohickey', 14.99),
            ('Thingamajig', 39.99),
            ('Whatchamacallit', 7.99),
            ('Flux Capacitor', 299.99),
            ('Self-Sealing Stem Bolt', 149.99),
            ('Hyperdrive Motivator', 499.99),
            ('Tricorder', 899.99),
            ('Replicator', 1499.99),
            ('Phaser', 599.99),
            ('Shields', 799.99),
            ('Warp Core', 2499.99);
    """)
    conn.commit()
