import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class PropagateDB:
    def __init__(self, db_path: Path | str = "propagate.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                president TEXT NOT NULL,
                eos_found INTEGER,
                eos_new INTEGER,
                batch_id TEXT,
                poll_seconds INTEGER,
                status TEXT NOT NULL DEFAULT 'running',
                error TEXT,
                deployed INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS eos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id),
                eo_number INTEGER NOT NULL,
                president TEXT NOT NULL,
                status TEXT NOT NULL,
                processed_at TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def start_run(self, president: str) -> int:
        conn = self._connect()
        cursor = conn.execute(
            "INSERT INTO runs (started_at, president, status) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), president, "running"),
        )
        conn.commit()
        run_id = cursor.lastrowid
        conn.close()
        return run_id

    def finish_run(
        self,
        run_id: int,
        status: str,
        eos_found: int | None = None,
        eos_new: int | None = None,
        batch_id: str | None = None,
        poll_seconds: int | None = None,
        error: str | None = None,
        deployed: bool = False,
    ):
        conn = self._connect()
        conn.execute(
            """UPDATE runs SET
                finished_at = ?, eos_found = ?, eos_new = ?,
                batch_id = ?, poll_seconds = ?, status = ?,
                error = ?, deployed = ?
            WHERE id = ?""",
            (
                datetime.now(timezone.utc).isoformat(),
                eos_found,
                eos_new,
                batch_id,
                poll_seconds,
                status,
                error,
                1 if deployed else 0,
                run_id,
            ),
        )
        conn.commit()
        conn.close()

    def insert_eo(self, run_id: int, eo_number: int, president: str, status: str):
        conn = self._connect()
        conn.execute(
            "INSERT INTO eos"
            " (run_id, eo_number, president, status, processed_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                run_id, eo_number, president, status,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def get_run(self, run_id: int) -> dict | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_eos_for_run(self, run_id: int) -> list[dict]:
        conn = self._connect()
        rows = conn.execute("SELECT * FROM eos WHERE run_id = ?", (run_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_recent_runs(self, limit: int = 10) -> list[dict]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_last_processed(self, president: str, eo_number: int) -> dict | None:
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM eos WHERE president = ? AND eo_number = ?"
            " ORDER BY id DESC LIMIT 1",
            (president, eo_number),
        ).fetchone()
        conn.close()
        return dict(row) if row else None
