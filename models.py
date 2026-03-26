"""Domain models for the Digitization Process Management System."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class User:
    """Represents a system user."""

    email: str
    name: str
    password: str
    role: str
    note: str = ""


@dataclass(slots=True)
class Document:
    """Represents a document registered in the digitization workflow."""

    file_name: str
    user_name: str
    bib: str
    call_number: str
    collection: str
    title: str
    publish_date: Optional[int]
    file_path: str
    created_at: datetime


@dataclass(slots=True)
class ProcessTracking:
    """Represents one process tracking transaction for a document."""

    transaction_id: Optional[int]
    file_name: str
    status: str
    completed_at: Optional[datetime]
