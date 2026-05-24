import sqlite3
import tempfile
from pathlib import Path

from propagate.db import PropagateDB


def test_init_creates_tables():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        PropagateDB(db_path)
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert "runs" in table_names
        assert "eos" in table_names
        conn.close()


def test_init_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        PropagateDB(db_path)
        PropagateDB(db_path)  # should not raise


def test_insert_run():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        db = PropagateDB(db_path)
        run_id = db.start_run(president="donald-trump")
        assert isinstance(run_id, int)
        assert run_id >= 1


def test_finish_run_success():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        db = PropagateDB(db_path)
        run_id = db.start_run(president="donald-trump")
        db.finish_run(
            run_id,
            eos_found=45,
            eos_new=3,
            batch_id="msgbatch_abc123",
            poll_seconds=340,
            status="success",
            deployed=True,
        )
        row = db.get_run(run_id)
        assert row["status"] == "success"
        assert row["eos_new"] == 3
        assert row["batch_id"] == "msgbatch_abc123"
        assert row["deployed"] == 1


def test_finish_run_failed():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        db = PropagateDB(db_path)
        run_id = db.start_run(president="donald-trump")
        db.finish_run(run_id, status="failed", error="connection timeout")
        row = db.get_run(run_id)
        assert row["status"] == "failed"
        assert row["error"] == "connection timeout"


def test_insert_eo():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        db = PropagateDB(db_path)
        run_id = db.start_run(president="donald-trump")
        db.insert_eo(
            run_id, eo_number=14405,
            president="donald-trump", status="success",
        )
        eos = db.get_eos_for_run(run_id)
        assert len(eos) == 1
        assert eos[0]["eo_number"] == 14405


def test_get_recent_runs():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        db = PropagateDB(db_path)
        for i in range(5):
            rid = db.start_run(president="donald-trump")
            db.finish_run(rid, status="success", eos_found=10, eos_new=i)
        runs = db.get_recent_runs(limit=3)
        assert len(runs) == 3
        # most recent first
        assert runs[0]["eos_new"] == 4


def test_get_last_processed_for_eo():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        db = PropagateDB(db_path)
        r1 = db.start_run(president="donald-trump")
        db.insert_eo(r1, eo_number=14405, president="donald-trump", status="success")
        r2 = db.start_run(president="donald-trump")
        db.insert_eo(r2, eo_number=14405, president="donald-trump", status="success")
        last = db.get_last_processed("donald-trump", 14405)
        assert last is not None
        assert last["run_id"] == r2
