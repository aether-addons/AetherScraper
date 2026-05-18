from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

from .kodi.settings import ADDON_ID
from .kodi.storage import ProfilePaths
from .release import parse_keyword_list

CACHE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CacheRecord:
    namespace: str
    key: str
    value: Any
    created_at: float
    expires_at: float | None = None

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= time.time()


class SQLiteCache:
    """Small SQLite persistence layer stored under Kodi profile/addon_data.

    Values are JSON payloads. Secrets must not be stored here unless a consumer has a
    clear reason and handles redaction itself.
    """

    def __init__(
        self, db_path: str | None = None, paths: ProfilePaths | None = None
    ) -> None:
        self.paths = paths or ProfilePaths.create(addon_id=ADDON_ID)
        self.db_path = db_path or os.path.join(self.paths.cache, "aetherscraper.sqlite3")
        self._ensure_parent()
        self._init_schema()

    @classmethod
    def from_profile(
        cls, addon_id: str = ADDON_ID, base_path: str | None = None
    ) -> SQLiteCache:
        paths = ProfilePaths.create(addon_id=addon_id, base_path=base_path)
        return cls(paths=paths)

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        record = self.get_record(namespace, key)
        return default if record is None else record.value

    def get_record(self, namespace: str, key: str) -> CacheRecord | None:
        now = time.time()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT value, created_at, expires_at
                FROM cache_entries
                WHERE namespace = ? AND key = ?
                """,
                (namespace, key),
            ).fetchone()
        if row is None:
            return None
        expires_at = float(row[2]) if row[2] is not None else None
        if expires_at is not None and expires_at <= now:
            self.delete(namespace, key)
            return None
        try:
            value = json.loads(str(row[0]))
        except json.JSONDecodeError:
            self.delete(namespace, key)
            return None
        return CacheRecord(namespace, key, value, float(row[1]), expires_at)

    def set(
        self, namespace: str, key: str, value: Any, ttl: float | None = None
    ) -> None:
        created_at = time.time()
        expires_at = created_at + ttl if ttl is not None and ttl > 0 else None
        payload = json.dumps(value, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cache_entries(namespace, key, value, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    value = excluded.value,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (namespace, key, payload, created_at, expires_at),
            )

    def delete(self, namespace: str, key: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE namespace = ? AND key = ?",
                (namespace, key),
            )
            return cursor.rowcount > 0

    def invalidate(self, namespace: str, key_prefix: str | None = None) -> int:
        with self._connect() as conn:
            if key_prefix is None:
                cursor = conn.execute(
                    "DELETE FROM cache_entries WHERE namespace = ?", (namespace,)
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM cache_entries WHERE namespace = ? AND key LIKE ?",
                    (namespace, f"{key_prefix}%"),
                )
            return int(cursor.rowcount)

    def cleanup(self, now: float | None = None) -> int:
        cutoff = time.time() if now is None else now
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at <= ?",
                (cutoff,),
            )
            return int(cursor.rowcount)

    def clear(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM cache_entries")
            return int(cursor.rowcount)

    def get_provider_state(self, provider_id: str, default: Any = None) -> Any:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM provider_state WHERE provider_id = ?", (provider_id,)
            ).fetchone()
        if row is None:
            return default
        try:
            return json.loads(str(row[0]))
        except json.JSONDecodeError:
            self.delete_provider_state(provider_id)
            return default

    def set_provider_state(self, provider_id: str, value: Any) -> None:
        payload = json.dumps(value, sort_keys=True)
        updated_at = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO provider_state(provider_id, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(provider_id) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (provider_id, payload, updated_at),
            )

    def delete_provider_state(self, provider_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM provider_state WHERE provider_id = ?", (provider_id,)
            )
            return cursor.rowcount > 0

    def get_undesirable_keywords(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT keyword FROM undesirable_keywords ORDER BY keyword COLLATE NOCASE"
            ).fetchall()
        return [str(row[0]) for row in rows]

    def set_undesirable_keywords(
        self, keywords: str | list[str] | tuple[str, ...]
    ) -> list[str]:
        parsed = parse_keyword_list(keywords)
        created_at = time.time()
        with self._connect() as conn:
            conn.execute("DELETE FROM undesirable_keywords")
            conn.executemany(
                "INSERT OR IGNORE INTO undesirable_keywords(keyword, created_at) VALUES (?, ?)",
                [(keyword, created_at) for keyword in parsed],
            )
        return parsed

    def add_undesirable_keyword(self, keyword: str) -> bool:
        parsed = parse_keyword_list([keyword])
        if not parsed:
            return False
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO undesirable_keywords(keyword, created_at) VALUES (?, ?)",
                (parsed[0], time.time()),
            )
            return cursor.rowcount > 0

    def remove_undesirable_keyword(self, keyword: str) -> bool:
        parsed = parse_keyword_list([keyword])
        if not parsed:
            return False
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM undesirable_keywords WHERE keyword = ?", (parsed[0],)
            )
            return cursor.rowcount > 0

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_parent(self) -> None:
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_info (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cache_entries (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL,
                    PRIMARY KEY(namespace, key)
                );
                CREATE INDEX IF NOT EXISTS idx_cache_entries_expires_at
                    ON cache_entries(expires_at);
                CREATE TABLE IF NOT EXISTS provider_state (
                    provider_id TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS undesirable_keywords (
                    keyword TEXT PRIMARY KEY,
                    created_at REAL NOT NULL
                );
                """
            )
            conn.execute(
                "INSERT OR REPLACE INTO schema_info(key, value) VALUES ('version', ?)",
                (str(CACHE_SCHEMA_VERSION),),
            )


def cache_from_profile(
    addon_id: str = ADDON_ID, base_path: str | None = None
) -> SQLiteCache:
    return SQLiteCache.from_profile(addon_id=addon_id, base_path=base_path)
