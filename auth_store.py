from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any


class AuthStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    payload TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS help_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    alias TEXT NOT NULL,
                    city TEXT NOT NULL,
                    post_type TEXT NOT NULL DEFAULT '求助',
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS help_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL REFERENCES help_posts(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    alias TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS sessions_expiry_idx ON sessions(expires_at);
                """
            )
            columns = {
                row["name"]
                for row in db.execute("PRAGMA table_info(help_posts)").fetchall()
            }
            if "post_type" not in columns:
                db.execute(
                    "ALTER TABLE help_posts ADD COLUMN post_type TEXT NOT NULL DEFAULT '求助'"
                )
            existing_posts = db.execute("SELECT COUNT(*) FROM help_posts").fetchone()[0]
            if existing_posts == 0:
                db.execute(
                    "INSERT INTO help_posts(user_id, alias, city, post_type, topic, content, created_at) VALUES(NULL,?,?,?,?,?,?)",
                    (
                        "归程志愿者",
                        "北京",
                        "求助",
                        "材料核对",
                        "可以帮你把要带的材料按办理地点再核对一遍。请不要在这里留下证件号码或联系电话。",
                        int(time.time()),
                    ),
                )

    @staticmethod
    def _password_hash(password: str, salt: bytes) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000).hex()

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_user(self, email: str, password: str, display_name: str) -> dict[str, Any]:
        salt = secrets.token_bytes(16)
        now = int(time.time())
        try:
            with self._connect() as db:
                cursor = db.execute(
                    "INSERT INTO users(email, display_name, password_hash, password_salt, created_at) VALUES(?,?,?,?,?)",
                    (email.lower(), display_name, self._password_hash(password, salt), salt.hex(), now),
                )
                user_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError("该邮箱已经注册") from exc
        return {"id": user_id, "email": email.lower(), "display_name": display_name}

    def authenticate(self, email: str, password: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)).fetchone()
        if not row:
            return None
        expected = self._password_hash(password, bytes.fromhex(row["password_salt"]))
        if not hmac.compare_digest(expected, row["password_hash"]):
            return None
        return {"id": row["id"], "email": row["email"], "display_name": row["display_name"]}

    def create_session(self, user_id: int, lifetime_seconds: int = 60 * 60 * 24 * 30) -> str:
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        with self._connect() as db:
            db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            db.execute(
                "INSERT INTO sessions(token_hash, user_id, expires_at, created_at) VALUES(?,?,?,?)",
                (self._token_hash(token), user_id, now + lifetime_seconds, now),
            )
        return token

    def user_for_session(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None
        now = int(time.time())
        with self._connect() as db:
            row = db.execute(
                """SELECT users.id, users.email, users.display_name
                   FROM sessions JOIN users ON users.id = sessions.user_id
                   WHERE sessions.token_hash = ? AND sessions.expires_at > ?""",
                (self._token_hash(token), now),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, token: str | None) -> None:
        if not token:
            return
        with self._connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (self._token_hash(token),))

    def save_progress(self, user_id: int, payload: dict[str, Any]) -> None:
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        with self._connect() as db:
            db.execute(
                """INSERT INTO user_progress(user_id, payload, updated_at) VALUES(?,?,?)
                   ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
                (user_id, serialized, int(time.time())),
            )

    def load_progress(self, user_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT payload, updated_at FROM user_progress WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return None
        value = json.loads(row["payload"])
        value["updated_at"] = row["updated_at"]
        return value

    def list_help_posts(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM help_posts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            result = []
            for row in rows:
                replies = db.execute("SELECT * FROM help_replies WHERE post_id = ? ORDER BY created_at", (row["id"],)).fetchall()
                result.append({"id": f"post-{row['id']}", "alias": row["alias"], "city": row["city"], "type": row["post_type"], "topic": row["topic"], "content": row["content"], "created_at": row["created_at"], "replies": [{"id": f"reply-{item['id']}", "alias": item["alias"], "content": item["content"], "created_at": item["created_at"]} for item in replies]})
        return result

    def create_help_post(self, user_id: int | None, alias: str, city: str, topic: str, content: str, post_type: str = "求助") -> dict[str, Any]:
        now = int(time.time())
        with self._connect() as db:
            cursor = db.execute("INSERT INTO help_posts(user_id, alias, city, post_type, topic, content, created_at) VALUES(?,?,?,?,?,?,?)", (user_id, alias, city, post_type, topic, content, now))
            post_id = int(cursor.lastrowid)
        return {"id": f"post-{post_id}", "alias": alias, "city": city, "type": post_type, "topic": topic, "content": content, "created_at": now, "replies": []}

    def create_help_reply(self, post_id: int, user_id: int | None, alias: str, content: str) -> dict[str, Any]:
        now = int(time.time())
        with self._connect() as db:
            exists = db.execute("SELECT 1 FROM help_posts WHERE id = ?", (post_id,)).fetchone()
            if not exists:
                raise ValueError("这条求助不存在或已被移除")
            cursor = db.execute("INSERT INTO help_replies(post_id, user_id, alias, content, created_at) VALUES(?,?,?,?,?)", (post_id, user_id, alias, content, now))
            reply_id = int(cursor.lastrowid)
        return {"id": f"reply-{reply_id}", "alias": alias, "content": content, "created_at": now}
