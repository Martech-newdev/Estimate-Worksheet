"""MarTech Job Estimate Worksheet — backend.

Serves the static SPA (index.html + assets) and exposes a tiny shared key/value
store backed by Postgres so that every site visitor sees the same Defaults,
Imported Customers, and Customer Exclusions.

Per-user data (the in-progress worksheet auto-save and the saved worksheet
library) stays in each browser's localStorage.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any

import psycopg2
import psycopg2.extras
import psycopg2.pool
from flask import Flask, Response, jsonify, request, send_from_directory

ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ["DATABASE_URL"]

ALLOWED_KEYS = {
    "defaults": {},
    "defaults_counter": 0,
    "imported_customers": [],
    "customer_exclusions": [],
}

_pool_lock = threading.Lock()
_pool: psycopg2.pool.SimpleConnectionPool | None = None


def _get_pool() -> psycopg2.pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = psycopg2.pool.SimpleConnectionPool(1, 8, dsn=DATABASE_URL)
    return _pool


def _ensure_schema() -> None:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_kv (
                  key TEXT PRIMARY KEY,
                  value JSONB NOT NULL,
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            for k, default in ALLOWED_KEYS.items():
                cur.execute(
                    "INSERT INTO shared_kv (key, value) VALUES (%s, %s::jsonb) "
                    "ON CONFLICT (key) DO NOTHING",
                    (k, json.dumps(default)),
                )
    finally:
        pool.putconn(conn)


def _read(key: str) -> Any:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM shared_kv WHERE key = %s", (key,))
            row = cur.fetchone()
            if row is None:
                return ALLOWED_KEYS[key]
            return row[0]
    finally:
        pool.putconn(conn)


def _write(key: str, value: Any) -> None:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shared_kv (key, value, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (key)
                DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                """,
                (key, json.dumps(value)),
            )
    finally:
        pool.putconn(conn)


app = Flask(__name__, static_folder=None)


@app.after_request
def _no_cache(resp: Response) -> Response:
    # Static SPA + API: never cache, so users always see fresh shared data and
    # the latest HTML/JS without a hard reload.
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/api/store", methods=["GET"])
def get_all_store() -> Response:
    """Bulk fetch — used by the SPA at startup so we issue a single round-trip."""
    out = {}
    for k in ALLOWED_KEYS:
        out[k] = _read(k)
    return jsonify(out)


@app.route("/api/store/<key>", methods=["GET"])
def get_store(key: str):
    if key not in ALLOWED_KEYS:
        return jsonify({"error": "unknown key"}), 404
    return jsonify({"key": key, "value": _read(key)})


@app.route("/api/store/<key>", methods=["PUT"])
def put_store(key: str):
    if key not in ALLOWED_KEYS:
        return jsonify({"error": "unknown key"}), 404
    if not request.is_json:
        return jsonify({"error": "expected application/json"}), 400
    body = request.get_json(silent=True)
    if body is None or "value" not in body:
        return jsonify({"error": "expected {\"value\": ...}"}), 400
    _write(key, body["value"])
    return jsonify({"ok": True})


@app.route("/api/counter/next", methods=["POST"])
def consume_counter():
    """Atomically increment and return the next counter value.

    Used by the Job Number `{####}` token so two browsers can't claim the
    same counter. Returns the value that was *consumed* (the value the
    counter held before the increment) plus the new stored value.
    """
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn, conn.cursor() as cur:
            # Read-modify-write inside a transaction with row lock so two
            # concurrent requests serialise rather than overwriting each
            # other.
            cur.execute(
                "SELECT value FROM shared_kv WHERE key = 'defaults_counter' "
                "FOR UPDATE"
            )
            row = cur.fetchone()
            try:
                cur_val = int(row[0]) if row and row[0] is not None else 0
            except (TypeError, ValueError):
                cur_val = 0
            consumed = cur_val if cur_val >= 1 else 1
            new_val = consumed + 1
            cur.execute(
                "INSERT INTO shared_kv (key, value, updated_at) "
                "VALUES ('defaults_counter', %s::jsonb, NOW()) "
                "ON CONFLICT (key) DO UPDATE "
                "SET value = EXCLUDED.value, updated_at = NOW()",
                (json.dumps(new_val),),
            )
        return jsonify({"consumed": consumed, "next": new_val})
    finally:
        pool.putconn(conn)


# ── Static file serving ────────────────────────────────────────────────────
SAFE_DIRS = {"assets", "attached_assets"}
ROOT_FILES_ALLOWLIST = {
    "index.html",
    "favicon.ico",
    "robots.txt",
}


def _safe_join(*parts: str) -> str | None:
    """Join paths and reject anything that escapes ROOT or contains traversal."""
    candidate = os.path.normpath(os.path.join(ROOT, *parts))
    root_with_sep = ROOT.rstrip(os.sep) + os.sep
    if candidate != ROOT and not candidate.startswith(root_with_sep):
        return None
    return candidate


@app.route("/")
def index_html():
    return send_from_directory(ROOT, "index.html")


@app.route("/<path:filename>")
def static_files(filename: str):
    # Reject any path containing a traversal segment or NUL byte before we
    # let send_from_directory anywhere near it.
    if not filename or "\x00" in filename:
        return ("Not found", 404)
    norm = filename.replace("\\", "/")
    parts = [p for p in norm.split("/") if p]
    if not parts or any(p in ("..", ".") for p in parts):
        return ("Not found", 404)

    if len(parts) == 1:
        # Root-level file: must be on the allowlist.
        name = parts[0]
        if name not in ROOT_FILES_ALLOWLIST:
            return ("Not found", 404)
        target = _safe_join(name)
        if target is None or not os.path.isfile(target):
            return ("Not found", 404)
        return send_from_directory(ROOT, name)

    # Subdir file: top-level dir must be whitelisted.
    top = parts[0]
    if top not in SAFE_DIRS:
        return ("Not found", 404)
    rel = "/".join(parts)
    target = _safe_join(rel)
    if target is None or not os.path.isfile(target):
        return ("Not found", 404)
    return send_from_directory(ROOT, rel)


if __name__ == "__main__":
    _ensure_schema()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
