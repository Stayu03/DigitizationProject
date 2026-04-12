"""SQLite data access layer for the Digitization Process Management System."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB_PATH = "data/digitization.db"

DEFAULT_COLLECTION_OPTIONS = [
    "Chula Publications",
    "Funeral Memorial Books",
    "Manuscripts",
    "Prince Dhani Nivat's Collection",
    "Prince Kitiyakara Voralaksana's Collection",
    "Rare Books",
    "Rare Newspapers and Magazines",
    "Thailand and Southeast Asia in the Cold War period",
]

INITIAL_USERS = [
    {
        "email": "somyingjd@gmail.com",
        "user_name": "สมหญิง ใจดี",
        "password": "12345678",
        "role": "Staff",
        "note": "",
        "created_at": "2025-05-10",
        "account_status": "Active",
    },
    {
        "email": "chaichaichai555@gmail.com",
        "user_name": "สมชาย ใจบุญ",
        "password": "87654321",
        "role": "Staff",
        "note": "นิสิตจุฬาปี 3",
        "created_at": "2025-05-09",
        "account_status": "Inactive",
    },
    {
        "email": "admindigisys1_cu@gmail.com",
        "user_name": "ชาลี ชีลา",
        "password": "adad1234",
        "role": "Admin",
        "note": "",
        "created_at": "2025-05-01",
        "account_status": "Active",
    },
]

INITIAL_DOCUMENTS = [
    {
        "file_name": "RA-00001",
        "bib": "b12345678",
        "call_number": "[RA] 121 224",
        "collection": "Rare Books",
        "title": "กถาสริตสาคร",
        "publish_date": 2499,
        "file_path": "",
        "created_at": "2025-09-04T14:00:00",
        "user_name": "สมหญิง ใจดี",
    },
    {
        "file_name": "TIC-00999-ENG",
        "bib": "T12345678",
        "call_number": "[TIC] 999 000",
        "collection": "Thailand and Southeast Asia in the Cold War period",
        "title": "Thailand in the Cold War",
        "publish_date": 2558,
        "file_path": "",
        "created_at": "2025-09-06T10:00:00",
        "user_name": "สมหญิง ใจดี",
    },
    {
        "file_name": "KI-00050",
        "bib": "K12345678",
        "call_number": "[KI] 818 181",
        "collection": "Prince Kitiyakara Voralaksana's Collection",
        "title": "จันทกุมารชาดก",
        "publish_date": 2530,
        "file_path": "",
        "created_at": "2025-09-18T15:50:00",
        "user_name": "สมชาย ใจบุญ",
    },
]

INITIAL_PROCESS_TRACKING = [
    {
        "file_name": "RA-00001",
        "status": "คัดเลือกเอกสาร",
        "completed_at": "2025-09-04T14:00:00",
        "note": "เล่มแรกที่เข้าระบบ",
        "updated_by_email": "somyingjd@gmail.com",
    },
    {
        "file_name": "RA-00001",
        "status": "สแกนเอกสาร",
        "completed_at": "2025-09-15T16:00:00",
        "note": "",
        "updated_by_email": "somyingjd@gmail.com",
    },
    {
        "file_name": "TIC-00999-ENG",
        "status": "คัดเลือกเอกสาร",
        "completed_at": "2025-09-06T10:00:00",
        "note": "",
        "updated_by_email": "somyingjd@gmail.com",
    },
    {
        "file_name": "KI-00050",
        "status": "คัดเลือกเอกสาร",
        "completed_at": "2025-09-18T15:50:00",
        "note": "",
        "updated_by_email": "chaichaichai555@gmail.com",
    },
]


def _iso_now() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.utcnow().replace(microsecond=0).isoformat()


def _tracking_has_updated_by(conn: sqlite3.Connection) -> bool:
    """Check whether process_tracking has updated_by column."""
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(process_tracking)").fetchall()]
    return "updated_by" in cols


def _tracking_has_note(conn: sqlite3.Connection) -> bool:
    """Check whether process_tracking has note column."""
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(process_tracking)").fetchall()]
    return "note" in cols


def _tracking_has_updated_by_email(conn: sqlite3.Connection) -> bool:
    """Check whether process_tracking has updated_by_email column."""
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(process_tracking)").fetchall()]
    return "updated_by_email" in cols


def _documents_has_user_fk(conn: sqlite3.Connection) -> bool:
    """Check whether documents.user_name still has a foreign key to users."""
    fks = conn.execute("PRAGMA foreign_key_list(documents)").fetchall()
    for fk in fks:
        if fk[2] == "users" and fk[3] == "user_name":
            return True
    return False


def hash_password(raw_password: str) -> str:
    """Hash raw password using SHA-256 for simple authentication flows."""
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create database connection with row access by column name."""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Flask may serve requests in different threads; allow shared connection usage.
    conn = sqlite3.connect(db_file, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


def init_database(conn: sqlite3.Connection) -> None:
    """Create tables and migrate documents schema when needed."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            user_name TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('Staff', 'Admin')),
            account_status TEXT NOT NULL DEFAULT 'Active' CHECK (account_status IN ('Active', 'Inactive')),
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS documents (
            file_name TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            bib TEXT NOT NULL DEFAULT '',
            call_number TEXT NOT NULL DEFAULT '',
            collection TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            publish_date INTEGER,
            file_path TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_name) REFERENCES users(user_name)
        );

        CREATE TABLE IF NOT EXISTS process_tracking (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            status TEXT NOT NULL,
            completed_at TEXT,
            updated_by TEXT,
            updated_by_email TEXT,
            note TEXT DEFAULT '',
            FOREIGN KEY (file_name) REFERENCES documents(file_name),
            FOREIGN KEY (updated_by_email) REFERENCES users(email)
        );

        CREATE TABLE IF NOT EXISTS collection_options (
            option_text TEXT PRIMARY KEY,
            sort_order INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_documents_user_name ON documents(user_name);
        CREATE INDEX IF NOT EXISTS idx_process_tracking_file_name_tx
            ON process_tracking(file_name, transaction_id DESC);
        CREATE INDEX IF NOT EXISTS idx_process_tracking_status ON process_tracking(status);
        CREATE INDEX IF NOT EXISTS idx_process_tracking_updated_by_email ON process_tracking(updated_by_email);
        """
    )

    option_count = conn.execute("SELECT COUNT(*) AS total FROM collection_options").fetchone()["total"]
    if option_count == 0:
        conn.executemany(
            "INSERT INTO collection_options (option_text, sort_order) VALUES (?, ?)",
            [(name, idx) for idx, name in enumerate(DEFAULT_COLLECTION_OPTIONS, start=1)],
        )

    tracking_cols = [row["name"] for row in conn.execute("PRAGMA table_info(process_tracking)").fetchall()]
    if "updated_by" not in tracking_cols:
        try:
            conn.execute("ALTER TABLE process_tracking ADD COLUMN updated_by TEXT;")
        except sqlite3.OperationalError:
            # If another process locks schema during startup, keep app running.
            pass

    tracking_cols = [row["name"] for row in conn.execute("PRAGMA table_info(process_tracking)").fetchall()]
    if "note" not in tracking_cols:
        try:
            conn.execute("ALTER TABLE process_tracking ADD COLUMN note TEXT DEFAULT '';")
        except sqlite3.OperationalError:
            # If another process locks schema during startup, keep app running.
            pass

    tracking_cols = [row["name"] for row in conn.execute("PRAGMA table_info(process_tracking)").fetchall()]
    if "updated_by_email" not in tracking_cols:
        try:
            conn.execute("ALTER TABLE process_tracking ADD COLUMN updated_by_email TEXT;")
            conn.execute(
                """
                UPDATE process_tracking
                SET updated_by_email = (
                    SELECT email FROM users u
                    WHERE u.user_name = process_tracking.updated_by
                    LIMIT 1
                )
                WHERE (updated_by_email IS NULL OR updated_by_email = '')
                  AND (updated_by IS NOT NULL AND updated_by <> '');
                """
            )
        except sqlite3.OperationalError:
            pass

    user_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "note" not in user_cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN note TEXT DEFAULT '';")
        except sqlite3.OperationalError:
            pass

    user_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in user_cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Staff';")
        except sqlite3.OperationalError:
            pass

    user_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "password" not in user_cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT '';")
        except sqlite3.OperationalError:
            pass

    user_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "user_name" not in user_cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN user_name TEXT DEFAULT '';")
        except sqlite3.OperationalError:
            pass

    user_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "created_at" not in user_cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN created_at TEXT;")
            conn.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL OR created_at = '';")
        except sqlite3.OperationalError:
            # If another process locks schema during startup, keep app running.
            pass

    user_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "web_link" not in user_cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN web_link TEXT DEFAULT '';")
        except sqlite3.OperationalError:
            pass

    user_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "account_status" not in user_cols:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN account_status TEXT DEFAULT 'Active';")
            conn.execute(
                "UPDATE users SET account_status = 'Active' WHERE account_status IS NULL OR account_status = '';"
            )
        except sqlite3.OperationalError:
            pass

    conn.execute(
        "UPDATE users SET note = '' WHERE note IN ('Default admin account', 'Default staff account');"
    )
    conn.commit()

    doc_cols = [row["name"] for row in conn.execute("PRAGMA table_info(documents)").fetchall()]
    required_doc_columns = {
        "bib": "TEXT NOT NULL DEFAULT ''",
        "call_number": "TEXT NOT NULL DEFAULT ''",
        "collection": "TEXT NOT NULL DEFAULT ''",
        "title": "TEXT NOT NULL DEFAULT ''",
        "publish_date": "INTEGER",
        "file_path": "TEXT NOT NULL DEFAULT ''",
        "created_at": "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }
    for col_name, col_def in required_doc_columns.items():
        if col_name not in doc_cols:
            try:
                conn.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_def};")
            except sqlite3.OperationalError:
                pass

    tracking_cols = [row["name"] for row in conn.execute("PRAGMA table_info(process_tracking)").fetchall()]
    if "completed_at" not in tracking_cols:
        try:
            conn.execute("ALTER TABLE process_tracking ADD COLUMN completed_at TEXT;")
        except sqlite3.OperationalError:
            pass

    doc_cols = [row["name"] for row in conn.execute("PRAGMA table_info(documents)").fetchall()]
    needs_migration = (
        ("name" in doc_cols)
        or ("user_name" not in doc_cols)
        or ("title" not in doc_cols)
        or _documents_has_user_fk(conn)
    )

    if needs_migration:
        user_col = "name" if "name" in doc_cols else "user_name"
        title_expr = "title" if "title" in doc_cols else "''"

        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute("DROP TABLE IF EXISTS documents_new;")
        conn.execute(
            """
            CREATE TABLE documents_new (
                file_name TEXT PRIMARY KEY,
                user_name TEXT NOT NULL DEFAULT '',
                bib TEXT NOT NULL DEFAULT '',
                call_number TEXT NOT NULL DEFAULT '',
                collection TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                publish_date INTEGER,
                file_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            f"""
            INSERT OR IGNORE INTO documents_new
                (file_name, user_name, bib, call_number, collection, title, publish_date, file_path, created_at)
            SELECT
                file_name,
                {user_col},
                bib,
                call_number,
                collection,
                {title_expr},
                publish_date,
                file_path,
                created_at
            FROM documents;
            """
        )
        conn.execute("DROP TABLE documents;")
        conn.execute("ALTER TABLE documents_new RENAME TO documents;")
        conn.execute("PRAGMA foreign_keys = ON;")

    conn.commit()


def _validate_password(password: str) -> None:
    """Require password to be exactly 8 alphanumeric characters."""
    if not re.fullmatch(r"[A-Za-z0-9]{8}", password or ""):
        raise ValueError("รหัสผ่านต้องเป็นตัวอักษรและตัวเลข จำนวน 8 ตัว (A-Z, a-z, 0-9)")


def _seed_initial_data(conn: sqlite3.Connection) -> None:
    """Seed baseline records when all core tables are empty."""
    user_count = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    doc_count = conn.execute("SELECT COUNT(*) AS total FROM documents").fetchone()["total"]
    tracking_count = conn.execute("SELECT COUNT(*) AS total FROM process_tracking").fetchone()["total"]

    if any((user_count, doc_count, tracking_count)):
        return

    for user in INITIAL_USERS:
        conn.execute(
            """
            INSERT INTO users (email, user_name, password, role, account_status, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["email"],
                user["user_name"],
                hash_password(user["password"]),
                user["role"],
                user["account_status"],
                user["note"],
                user["created_at"],
            ),
        )

    for doc in INITIAL_DOCUMENTS:
        conn.execute(
            """
            INSERT INTO documents (
                file_name, user_name, bib, call_number, collection, title, publish_date, file_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc["file_name"],
                doc["user_name"],
                doc["bib"],
                doc["call_number"],
                doc["collection"],
                doc["title"],
                doc["publish_date"],
                doc["file_path"],
                doc["created_at"],
            ),
        )

    for item in INITIAL_PROCESS_TRACKING:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, updated_by, updated_by_email, note)
            VALUES (
                ?,
                ?,
                ?,
                (SELECT user_name FROM users WHERE email = ?),
                ?,
                ?
            )
            """,
            (
                item["file_name"],
                item["status"],
                item["completed_at"],
                item["updated_by_email"],
                item["updated_by_email"],
                item["note"],
            ),
        )

    conn.commit()


def add_user(
    conn: sqlite3.Connection,
    email: str,
    user_name: str,
    password: str,
    role: str,
    account_status: str = "Active",
    note: str = "",
) -> None:
    """Create a new user account."""
    _validate_password(password)
    conn.execute(
        """
        INSERT INTO users (email, user_name, password, role, account_status, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email.strip().lower(),
            user_name.strip(),
            hash_password(password),
            role,
            account_status if account_status in {"Active", "Inactive"} else "Active",
            note.strip(),
            _iso_now(),
        ),
    )
    conn.commit()


def authenticate_user(conn: sqlite3.Connection, email: str, password: str) -> Optional[dict[str, Any]]:
    """Validate user credentials and return user record when valid."""
    row = conn.execute(
        "SELECT email, user_name, role, account_status, note FROM users WHERE email = ? AND password = ? AND account_status = 'Active'",
        (email.strip().lower(), hash_password(password)),
    ).fetchone()
    return dict(row) if row else None


def list_users(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """List all users ordered by role and user_name."""
    rows = conn.execute(
        "SELECT email, user_name, role, account_status, note, created_at FROM users ORDER BY created_at DESC, user_name ASC"
    ).fetchall()
    return [dict(row) for row in rows]


def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[dict[str, Any]]:
    """Get a user profile by email for settings/profile view."""
    row = conn.execute(
        "SELECT email, user_name, role, account_status, note, created_at FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    return dict(row) if row else None


def update_user_account(
    conn: sqlite3.Connection,
    current_email: str,
    user_name: str,
    role: str,
    account_status: str,
) -> None:
    """Update basic account information except password."""
    conn.execute(
        """
        UPDATE users
        SET user_name = ?, role = ?, account_status = ?
        WHERE email = ?
        """,
        (
            user_name.strip(),
            role,
            account_status if account_status in {"Active", "Inactive"} else "Active",
            current_email.strip().lower(),
        ),
    )
    conn.commit()


def update_user_status(conn: sqlite3.Connection, email: str, account_status: str) -> None:
    """Update a user's active/inactive status."""
    conn.execute(
        "UPDATE users SET account_status = ? WHERE email = ?",
        (
            account_status if account_status in {"Active", "Inactive"} else "Active",
            email.strip().lower(),
        ),
    )
    conn.commit()


def delete_user_account(conn: sqlite3.Connection, email: str) -> None:
    """Delete a user account by email."""
    conn.execute("DELETE FROM users WHERE email = ?", (email.strip().lower(),))
    conn.commit()


def admin_reset_user_password(conn: sqlite3.Connection, email: str, new_password: str = "12345678") -> None:
    """Reset a user's password to a default value (Admin only)."""
    _validate_password(new_password)
    conn.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        (hash_password(new_password), email.strip().lower()),
    )
    conn.commit()


def add_document(
    conn: sqlite3.Connection,
    file_name: str,
    created_by_name: str,
    bib: str,
    call_number: str,
    collection: str,
    title: str,
    publish_date: Optional[int],
    file_path: str,
    created_by_email: Optional[str] = None,
    created_at: Optional[str] = None,
) -> None:
    """Create a new document and initialize process status as Pending."""
    created_at_value = created_at or _iso_now()

    conn.execute(
        """
        INSERT INTO documents (
            file_name, user_name, bib, call_number, collection, title, publish_date, file_path, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file_name.strip(),
            (created_by_name or "").strip(),
            bib.strip(),
            call_number.strip(),
            collection.strip(),
            title.strip(),
            publish_date,
            file_path.strip(),
            created_at_value,
        ),
    )

    has_updated_by = _tracking_has_updated_by(conn)
    has_updated_by_email = _tracking_has_updated_by_email(conn)
    has_note = _tracking_has_note(conn)

    if has_updated_by and has_updated_by_email and has_note:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, updated_by, updated_by_email, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                file_name.strip(),
                "คัดเลือกเอกสาร",
                created_at_value,
                (created_by_name or "").strip() or None,
                (created_by_email or "").strip().lower() or None,
                "",
            ),
        )
    elif has_updated_by and has_updated_by_email:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, updated_by, updated_by_email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                file_name.strip(),
                "คัดเลือกเอกสาร",
                created_at_value,
                (created_by_name or "").strip() or None,
                (created_by_email or "").strip().lower() or None,
            ),
        )
    elif has_updated_by:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, updated_by)
            VALUES (?, ?, ?, ?)
            """,
            (file_name.strip(), "คัดเลือกเอกสาร", created_at_value, (created_by_name or "").strip() or None),
        )
    elif has_note:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, note)
            VALUES (?, ?, ?, ?)
            """,
            (file_name.strip(), "คัดเลือกเอกสาร", created_at_value, ""),
        )
    else:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at)
            VALUES (?, ?, ?)
            """,
            (file_name.strip(), "คัดเลือกเอกสาร", created_at_value),
        )

    conn.commit()


def list_documents(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """List documents with their latest tracking status."""
    rows = conn.execute(
        """
        SELECT
            d.file_name,
            d.user_name,
            d.bib,
            d.call_number,
            d.collection,
            d.title,
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
            ) p2
                ON p1.file_name = p2.file_name
               AND p1.transaction_id = p2.max_id
        ) pt
            ON d.file_name = pt.file_name
        ORDER BY d.created_at DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_document(conn: sqlite3.Connection, file_name: str) -> Optional[dict[str, Any]]:
    """Retrieve a single document by file_name."""
    row = conn.execute(
        """
        SELECT
            file_name,
            user_name,
            bib,
            call_number,
            collection,
            title,
            publish_date,
            file_path,
            created_at
        FROM documents
        WHERE file_name = ?
        """,
        (file_name,),
    ).fetchone()
    return dict(row) if row else None


def add_process_tracking(
    conn: sqlite3.Connection,
    file_name: str,
    status: str,
    completed_at: Optional[str] = None,
    updated_by: Optional[str] = None,
    note: str = "",
    updated_by_email: Optional[str] = None,
) -> None:
    """Append a status transaction for the given document."""
    has_updated_by = _tracking_has_updated_by(conn)
    has_updated_by_email = _tracking_has_updated_by_email(conn)
    has_note = _tracking_has_note(conn)

    if has_updated_by and has_updated_by_email and has_note:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, updated_by, updated_by_email, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                file_name.strip(),
                status.strip(),
                completed_at,
                (updated_by or "").strip() or None,
                (updated_by_email or "").strip().lower() or None,
                (note or "").strip(),
            ),
        )
    elif has_updated_by and has_updated_by_email:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, updated_by, updated_by_email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                file_name.strip(),
                status.strip(),
                completed_at,
                (updated_by or "").strip() or None,
                (updated_by_email or "").strip().lower() or None,
            ),
        )
    elif has_updated_by:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, updated_by)
            VALUES (?, ?, ?, ?)
            """,
            (file_name.strip(), status.strip(), completed_at, (updated_by or "").strip() or None),
        )
    elif has_note:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at, note)
            VALUES (?, ?, ?, ?)
            """,
            (file_name.strip(), status.strip(), completed_at, (note or "").strip()),
        )
    else:
        conn.execute(
            """
            INSERT INTO process_tracking (file_name, status, completed_at)
            VALUES (?, ?, ?)
            """,
            (file_name.strip(), status.strip(), completed_at),
        )
    conn.commit()


def update_document_details(
    conn: sqlite3.Connection,
    file_name: str,
    user_name: str,
    bib: str,
    call_number: str,
    collection: str,
    title: str,
    publish_date: Optional[int],
    file_path: str,
) -> None:
    """Update editable document details for admin workflows."""
    conn.execute(
        """
        UPDATE documents
        SET user_name = ?,
            bib = ?,
            call_number = ?,
            collection = ?,
            title = ?,
            publish_date = ?,
            file_path = ?
        WHERE file_name = ?
        """,
        (
            user_name.strip(),
            bib.strip(),
            call_number.strip(),
            collection.strip(),
            title.strip(),
            publish_date,
            file_path.strip(),
            file_name.strip(),
        ),
    )
    conn.commit()


def list_document_updates(conn: sqlite3.Connection, file_name: str) -> list[dict[str, Any]]:
    """List all update transactions for a document with responsible user."""
    has_updated_by = _tracking_has_updated_by(conn)
    has_note = _tracking_has_note(conn)

    has_updated_by_email = _tracking_has_updated_by_email(conn)

    if has_updated_by and has_updated_by_email and has_note:
        rows = conn.execute(
            """
            SELECT
                p.transaction_id,
                p.status,
                p.completed_at,
                COALESCE(u.user_name, p.updated_by, d.user_name) AS user_name,
                COALESCE(p.note, '') AS note,
                d.created_at
            FROM process_tracking p
            INNER JOIN documents d
                ON d.file_name = p.file_name
            LEFT JOIN users u
                ON u.email = p.updated_by_email
            WHERE p.file_name = ?
            ORDER BY p.transaction_id DESC
            """,
            (file_name,),
        ).fetchall()
    elif has_updated_by and has_updated_by_email:
        rows = conn.execute(
            """
            SELECT
                p.transaction_id,
                p.status,
                p.completed_at,
                COALESCE(u.user_name, p.updated_by, d.user_name) AS user_name,
                '' AS note,
                d.created_at
            FROM process_tracking p
            INNER JOIN documents d
                ON d.file_name = p.file_name
            LEFT JOIN users u
                ON u.email = p.updated_by_email
            WHERE p.file_name = ?
            ORDER BY p.transaction_id DESC
            """,
            (file_name,),
        ).fetchall()
    elif has_updated_by and has_note:
        rows = conn.execute(
            """
            SELECT
                p.transaction_id,
                p.status,
                p.completed_at,
                COALESCE(p.updated_by, d.user_name) AS user_name,
                COALESCE(p.note, '') AS note,
                d.created_at
            FROM process_tracking p
            INNER JOIN documents d
                ON d.file_name = p.file_name
            WHERE p.file_name = ?
            ORDER BY p.transaction_id DESC
            """,
            (file_name,),
        ).fetchall()
    elif has_updated_by:
        rows = conn.execute(
            """
            SELECT
                p.transaction_id,
                p.status,
                p.completed_at,
                COALESCE(p.updated_by, d.user_name) AS user_name,
                '' AS note,
                d.created_at
            FROM process_tracking p
            INNER JOIN documents d
                ON d.file_name = p.file_name
            WHERE p.file_name = ?
            ORDER BY p.transaction_id DESC
            """,
            (file_name,),
        ).fetchall()
    elif has_note:
        rows = conn.execute(
            """
            SELECT
                p.transaction_id,
                p.status,
                p.completed_at,
                d.user_name,
                COALESCE(p.note, '') AS note,
                d.created_at
            FROM process_tracking p
            INNER JOIN documents d
                ON d.file_name = p.file_name
            WHERE p.file_name = ?
            ORDER BY p.transaction_id DESC
            """,
            (file_name,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT
                p.transaction_id,
                p.status,
                p.completed_at,
                d.user_name,
                '' AS note,
                d.created_at
            FROM process_tracking p
            INNER JOIN documents d
                ON d.file_name = p.file_name
            WHERE p.file_name = ?
            ORDER BY p.transaction_id DESC
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
            ) p2
                ON p1.file_name = p2.file_name
               AND p1.transaction_id = p2.max_id
        )
        SELECT status, COUNT(*) AS total
        FROM latest
        GROUP BY status
        ORDER BY total DESC, status ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_collection_options(conn: sqlite3.Connection) -> list[str]:
    """Return configured collection dropdown options in display order."""
    rows = conn.execute(
        "SELECT option_text FROM collection_options ORDER BY sort_order ASC, option_text ASC"
    ).fetchall()
    return [str(row["option_text"]).strip() for row in rows if str(row["option_text"]).strip()]


def replace_collection_options(conn: sqlite3.Connection, options: list[str]) -> None:
    """Replace all collection dropdown options with a new ordered list."""
    cleaned = []
    seen = set()
    for opt in options:
        value = (opt or "").strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)

    if not cleaned:
        cleaned = DEFAULT_COLLECTION_OPTIONS[:]

    conn.execute("DELETE FROM collection_options")
    conn.executemany(
        "INSERT INTO collection_options (option_text, sort_order) VALUES (?, ?)",
        [(name, idx) for idx, name in enumerate(cleaned, start=1)],
    )
    conn.commit()


def run_startup(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Initialize database and return ready-to-use connection."""
    conn = get_connection(db_path)
    init_database(conn)
    _seed_initial_data(conn)

    return conn