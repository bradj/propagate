import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from propagate.run import PipelineRunner


def _make_runner(tmp_dir: str) -> PipelineRunner:
    db_path = Path(tmp_dir) / "test.db"
    return PipelineRunner(db_path=db_path)


def _mock_order(eo_number: int, has_summary: bool = False):
    order = MagicMock()
    order.executive_order_number = eo_number
    order.title = f"EO {eo_number}"
    order.signing_date = "2026-01-20"
    order.president = "Donald Trump"
    order.summary_exists.return_value = has_summary
    return order


@patch("propagate.run.fetch_all_executive_orders")
def test_no_new_orders_skips_batch(mock_fetch):
    with tempfile.TemporaryDirectory() as tmp:
        runner = _make_runner(tmp)
        order = _mock_order(14405, has_summary=True)
        mock_fetch.return_value = [order]

        runner.run()

        run = runner.db.get_recent_runs(1)[0]
        assert run["status"] == "no_new_orders"
        assert run["eos_found"] == 1
        assert run["eos_new"] == 0
        assert run["batch_id"] is None


@patch("propagate.run.time.sleep")
@patch("propagate.run.subprocess")
@patch("propagate.run.build_from_summaries")
@patch("propagate.run.download_and_process_batch")
@patch("propagate.run.batch_summarize_with_claude")
@patch("propagate.run.fetch_all_executive_orders")
def test_new_orders_full_pipeline(
    mock_fetch, mock_batch, mock_process, mock_build, mock_subprocess, mock_sleep
):
    with tempfile.TemporaryDirectory() as tmp:
        runner = _make_runner(tmp)
        orders = [_mock_order(14405), _mock_order(14406)]
        for o in orders:
            o.summary_exists.side_effect = [False, True]
        mock_fetch.return_value = orders

        mock_batch_response = MagicMock()
        mock_batch_response.id = "msgbatch_test123"
        mock_batch.return_value = (mock_batch_response, ["req1", "req2"])

        mock_client = MagicMock()
        mock_status = MagicMock()
        mock_status.processing_status = "ended"
        mock_client.messages.batches.retrieve.return_value = mock_status

        with patch("propagate.run.get_client", return_value=mock_client):
            runner.run()

        run = runner.db.get_recent_runs(1)[0]
        assert run["status"] == "success"
        assert run["batch_id"] == "msgbatch_test123"
        assert run["eos_new"] == 2
        mock_process.assert_called_once()
        mock_build.assert_called_once()


@patch("propagate.run.fetch_all_executive_orders")
def test_fetch_failure_records_error(mock_fetch):
    with tempfile.TemporaryDirectory() as tmp:
        runner = _make_runner(tmp)
        mock_fetch.side_effect = Exception("API down")

        runner.run()

        run = runner.db.get_recent_runs(1)[0]
        assert run["status"] == "failed"
        assert "API down" in run["error"]
