"""Database connection management for SQLite."""
from __future__ import annotations

import sqlite3

from flask import Flask, g


def get_db() -> sqlite3.Connection:
    """Get request-scoped database connection."""
    if 'db' not in g:
        from flask import current_app
        g.db = sqlite3.connect(current_app.config['DB_PATH'])
        g.db.row_factory = sqlite3.Row
        cursor = g.db.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.close()
    return g.db


def close_db(exc: BaseException | None = None) -> None:
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app: Flask) -> None:
    """Register database teardown with the app."""
    app.teardown_appcontext(close_db)
