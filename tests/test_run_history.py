import tempfile
from pathlib import Path

from propagate.db import PropagateDB
from propagate.run_history import format_status


def test_format_status_no_runs():
    with tempfile.TemporaryDirectory() as tmp:
        db = PropagateDB(Path(tmp) / "test.db")
        output = format_status(db)
        assert "No runs recorded" in output


def test_format_status_with_runs():
    with tempfile.TemporaryDirectory() as tmp:
        db = PropagateDB(Path(tmp) / "test.db")
        r1 = db.start_run(president="donald-trump")
        db.finish_run(r1, status="success", eos_found=45, eos_new=3,
                      batch_id="msgbatch_abc", poll_seconds=340, deployed=True)
        db.insert_eo(r1, eo_number=14405, president="donald-trump", status="success")
        db.insert_eo(r1, eo_number=14406, president="donald-trump", status="success")
        db.insert_eo(r1, eo_number=14407, president="donald-trump", status="success")

        output = format_status(db)
        assert "success" in output
        assert "45" in output
        assert "3" in output
        assert "msgbatch_abc" in output


def test_format_status_with_failure():
    with tempfile.TemporaryDirectory() as tmp:
        db = PropagateDB(Path(tmp) / "test.db")
        r1 = db.start_run(president="donald-trump")
        db.finish_run(r1, status="failed", error="API timeout")

        output = format_status(db)
        assert "failed" in output
        assert "API timeout" in output
