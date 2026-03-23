"""SQLite data access layer for the Digitization Process Management System."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB_PATH = "data/digitization.db"


def _iso_now() -> str:
	return datetime.utcnow().replace(microsecond=0).isoformat()


def hash_password(raw_password: str) -> str:
	"""Hash raw password using SHA-256 for simple authentication flows."""
	return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
	"""Create database connection with row access by column name."""
	db_file = Path(db_path)
	db_file.parent.mkdir(parents=True, exist_ok=True)

	conn = sqlite3.connect(db_file)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON;")
	return conn


def init_database(conn: sqlite3.Connection) -> None:
	"""Create tables using the agreed schema from backend design document."""
	conn.executescript(
		"""
		CREATE TABLE IF NOT EXISTS users (
			email TEXT PRIMARY KEY,
			name TEXT NOT NULL UNIQUE,
			password TEXT NOT NULL,
			role TEXT NOT NULL CHECK (role IN ('Staff', 'Admin')),
			note TEXT DEFAULT ''
		);

		CREATE TABLE IF NOT EXISTS documents (
			file_name TEXT PRIMARY KEY,
			name TEXT NOT NULL,
			bib TEXT NOT NULL DEFAULT '',
			call_number TEXT NOT NULL DEFAULT '',
			collection TEXT NOT NULL DEFAULT '',
			publish_date INTEGER,
			file_path TEXT NOT NULL DEFAULT '',
			created_at TEXT NOT NULL,
			FOREIGN KEY (name) REFERENCES users(name)
		);

		CREATE TABLE IF NOT EXISTS process_tracking (
			transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
			file_name TEXT NOT NULL,
			status TEXT NOT NULL,
			completed_at TEXT,
			FOREIGN KEY (file_name) REFERENCES documents(file_name)
		);
		"""
	)
	conn.commit()


def seed_default_users(conn: sqlite3.Connection) -> None:
	"""Insert one admin and one staff account if they do not already exist."""
	seed_rows = [
		{
			"email": "admin@digitization.local",
			"name": "Admin User",
			"password": hash_password("admin123"),
			"role": "Admin",
			"note": "Default admin account",
		},
		{
			"email": "staff@digitization.local",
			"name": "Staff User",
			"password": hash_password("staff123"),
			"role": "Staff",
			"note": "Default staff account",
		},
	]

	conn.executemany(
		"""
		INSERT INTO users (email, name, password, role, note)
		VALUES (:email, :name, :password, :role, :note)
		ON CONFLICT(email) DO NOTHING;
		""",
		seed_rows,
	)
	conn.commit()


def authenticate_user(conn: sqlite3.Connection, email: str, password: str) -> Optional[dict[str, Any]]:
	"""Validate user credentials and return user record when valid."""
	row = conn.execute(
		"SELECT email, name, role, note FROM users WHERE email = ? AND password = ?",
		(email.strip().lower(), hash_password(password)),
	).fetchone()
	return dict(row) if row else None


def _validate_password(password: str) -> None:
    """Require password to be at least 8 characters."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

def add_user(conn: sqlite3.Connection, email: str, name: str, password: str, role: str, note: str = "") -> None:
    """Create a new user account."""
    _validate_password(password)
    conn.execute(
        """
        INSERT INTO users (email, name, password, role, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (email.strip().lower(), name.strip(), hash_password(password), role, note.strip()),
    )
    conn.commit()


def list_users(conn: sqlite3.Connection) -> list[dict[str, Any]]:
	rows = conn.execute(
		"SELECT email, name, role, note FROM users ORDER BY role DESC, name ASC"
	).fetchall()
	return [dict(row) for row in rows]


def add_document(
    conn: sqlite3.Connection,
    file_name: str,
    name: str,
    bib: str,
    call_number: str,
    collection: str,
    publish_date: Optional[int],
    file_path: str,
    created_at: Optional[str] = None,
) -> None:
    """Create a new document and initialize process status as Pending."""
    created_at_value = created_at or _iso_now()

    conn.execute(
        """
        INSERT INTO documents (
            file_name, name, bib, call_number, collection, publish_date, file_path, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file_name.strip(),
            name.strip(),
            bib.strip(),
            call_number.strip(),
            collection.strip(),
            publish_date,
            file_path.strip(),
            created_at_value,
        ),
    )

    conn.execute(
        """
        INSERT INTO process_tracking (file_name, status, completed_at)
        VALUES (?, ?, ?)
        """,
        (file_name.strip(), "Pending", None),
    )

    conn.commit()

def list_documents(conn: sqlite3.Connection) -> list[dict[str, Any]]:
	"""List documents with their latest tracking status."""
	rows = conn.execute(
		"""
		SELECT
			d.file_name,
			d.name,
			d.bib,
			d.call_number,
			d.collection,
			d.publish_date,
			d.file_path,
			d.created_at,
			COALESCE(pt.status, 'Pending') AS current_status,
			pt.completed_at AS last_completed_at
		FROM documents d
		LEFT JOIN (
			SELECT p1.file_name, p1.status, p1.completed_at
			FROM process_tracking p1
			INNER JOIN (
				SELECT file_name, MAX(transaction_id) AS max_id
				FROM process_tracking
				GROUP BY file_name
			) p2 ON p1.file_name = p2.file_name AND p1.transaction_id = p2.max_id
		) pt ON d.file_name = pt.file_name
		ORDER BY d.created_at DESC
		"""
	).fetchall()
	return [dict(row) for row in rows]


def get_document(conn: sqlite3.Connection, file_name: str) -> Optional[dict[str, Any]]:
	row = conn.execute(
		"""
		SELECT file_name, name, bib, call_number, collection, publish_date, file_path, created_at
		FROM documents
		WHERE file_name = ?
		""",
		(file_name,),
	).fetchone()
	return dict(row) if row else None


def add_process_tracking(conn: sqlite3.Connection, file_name: str, status: str, completed_at: Optional[str] = None) -> None:
	"""Append a status transaction for the given document."""
	conn.execute(
		"INSERT INTO process_tracking (file_name, status, completed_at) VALUES (?, ?, ?)",
		(file_name, status, completed_at),
	)
	conn.commit()


def get_process_history(conn: sqlite3.Connection, file_name: str) -> list[dict[str, Any]]:
	rows = conn.execute(
		"""
		SELECT transaction_id, file_name, status, completed_at
		FROM process_tracking
		WHERE file_name = ?
		ORDER BY transaction_id DESC
		""",
		(file_name,),
	).fetchall()
	return [dict(row) for row in rows]


def list_status_counts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
	"""Return summary counts based on latest status of each document."""
	rows = conn.execute(
		"""
		WITH latest AS (
			SELECT p1.file_name, p1.status
			FROM process_tracking p1
			INNER JOIN (
				SELECT file_name, MAX(transaction_id) AS max_id
				FROM process_tracking
				GROUP BY file_name
			) p2 ON p1.file_name = p2.file_name AND p1.transaction_id = p2.max_id
		)
		SELECT status, COUNT(*) AS total
		FROM latest
		GROUP BY status
		ORDER BY total DESC, status ASC
		"""
	).fetchall()
	return [dict(row) for row in rows]

# The above function initializes the database and seeds default users. Below is an extended version that also adds a sample user and document for testing purposes.

def run_startup(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Initialize database and return ready-to-use connection."""
    conn = get_connection(db_path)
    init_database(conn)
    seed_default_users(conn)

    try:
        add_user(
            conn,
            "somyingjd@gmail.com",
            "สมหญิง ใจดี",
            "12345678",
            "Staff",
            "manual test user",
        )
    except (sqlite3.IntegrityError, ValueError):
        pass

    try:
        add_document(
            conn,
            "doc001",
            "สมหญิง ใจดี",  # ต้องตรงกับ users.name (foreign key)
            "BIB001",
            "QA123 .P9",
            "General Collection",
            2024,
            "/tmp/doc001.pdf",
        )
    except sqlite3.IntegrityError:
        pass

    return conn