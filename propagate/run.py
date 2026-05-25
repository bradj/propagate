#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path

from propagate.batch_manager import download_and_process_batch
from propagate.build import build_from_summaries
from propagate.config import PDF_DIR
from propagate.db import PropagateDB
from propagate.federalregister import fetch_all_executive_orders
from propagate.logging_config import get_logger, setup_logging
from propagate.models import PRESIDENTS
from propagate.summarize_eo import batch_summarize_with_claude
from propagate.util import get_client

logger = get_logger(__name__)

MAX_POLL_SECONDS = 4 * 60 * 60  # 4 hours
POLL_INTERVAL = 120  # 2 minutes
DEFAULT_PRESIDENT = PRESIDENTS[0]


class PipelineRunner:
    def __init__(self, db_path: Path | str = "propagate.db"):
        self.db = PropagateDB(db_path)

    def run(self):
        president = DEFAULT_PRESIDENT
        run_id = self.db.start_run(president=president.key)

        try:
            self._execute(run_id, president)
        except Exception as e:
            self.db.finish_run(run_id, status="failed", error=str(e))
            logger.error("Pipeline failed", exc_info=True)

    def _execute(self, run_id: int, president):
        logger.info("Fetching executive orders for %s", president.name)
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        orders = fetch_all_executive_orders(president=president.key)

        for order in orders:
            order.president = president.name

        eos_found = len(orders)
        new_orders = [o for o in orders if not o.summary_exists()]
        eos_new = len(new_orders)

        logger.info("Found %d EOs, %d new", eos_found, eos_new)

        if eos_new == 0:
            self.db.finish_run(
                run_id,
                status="no_new_orders",
                eos_found=eos_found,
                eos_new=0,
            )
            logger.info("No new orders to process")
            return

        logger.info("Submitting batch for %d orders", eos_new)
        response, request_ids = batch_summarize_with_claude(new_orders, president.key)
        batch_id = response.id
        logger.info("Batch submitted: %s", batch_id)

        logger.info("Polling for batch completion...")
        elapsed = 0
        while True:
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            batch = get_client().messages.batches.retrieve(batch_id)
            status = batch.processing_status
            logger.info("Batch poll elapsed=%ds status=%s", elapsed, status)

            if status == "ended":
                break

            if elapsed >= MAX_POLL_SECONDS:
                raise TimeoutError(
                    f"Batch {batch_id} did not complete within {MAX_POLL_SECONDS}s"
                )

        logger.info("Processing batch results...")
        download_and_process_batch(batch_id)

        succeeded = []
        failed = []
        for order in new_orders:
            if order.summary_exists():
                succeeded.append(order)
                self.db.insert_eo(
                    run_id,
                    eo_number=order.executive_order_number,
                    president=president.key,
                    status="success",
                )
            else:
                failed.append(order)
                self.db.insert_eo(
                    run_id,
                    eo_number=order.executive_order_number,
                    president=president.key,
                    status="failed",
                )

        if failed:
            logger.error(
                "%d EOs failed: %s",
                len(failed),
                ", ".join(str(o.executive_order_number) for o in failed),
            )

        if not succeeded:
            logger.error("No EOs were successfully processed. Skipping deploy.")
            self.db.finish_run(
                run_id,
                status="failed",
                eos_found=eos_found,
                eos_new=eos_new,
                batch_id=batch_id,
                poll_seconds=elapsed,
                deployed=False,
            )
            return

        logger.info("Building eo.json...")
        build_from_summaries()

        logger.info("Deploying...")
        subprocess.run(
            ["cp", "eo/eo.json", "web/public/"],
            check=True,
        )
        subprocess.run(
            ["npm", "run", "build"],
            cwd="web/",
            check=True,
        )
        subprocess.run(
            ["netlify", "deploy", "--prod"],
            cwd="web/",
            check=True,
        )

        status = "partial_failure" if failed else "success"
        self.db.finish_run(
            run_id,
            status=status,
            eos_found=eos_found,
            eos_new=eos_new,
            batch_id=batch_id,
            poll_seconds=elapsed,
            deployed=True,
        )

        logger.info("Pipeline complete: %d/%d EOs processed and deployed", len(succeeded), eos_new)


def main():
    setup_logging()
    runner = PipelineRunner()
    runner.run()


if __name__ == "__main__":
    main()
