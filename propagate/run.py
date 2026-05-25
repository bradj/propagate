#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path

from propagate.batch_manager import download_and_process_batch
from propagate.build import build_from_summaries
from propagate.config import PDF_DIR
from propagate.db import PropagateDB
from propagate.federalregister import fetch_all_executive_orders
from propagate.models import PRESIDENTS
from propagate.summarize_eo import batch_summarize_with_claude
from propagate.util import get_client

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
            print(f"Pipeline failed: {e}")

    def _execute(self, run_id: int, president):
        print(f"Fetching executive orders for {president.name}...")
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        orders = fetch_all_executive_orders(president=president.key)

        for order in orders:
            order.president = president.name

        eos_found = len(orders)
        new_orders = [o for o in orders if not o.summary_exists()]
        eos_new = len(new_orders)

        print(f"Found {eos_found} EOs, {eos_new} new")

        if eos_new == 0:
            self.db.finish_run(
                run_id,
                status="no_new_orders",
                eos_found=eos_found,
                eos_new=0,
            )
            print("No new orders to process")
            return

        print(f"Submitting batch for {eos_new} orders...")
        response, request_ids = batch_summarize_with_claude(new_orders, president.key)
        batch_id = response.id
        print(f"Batch submitted: {batch_id}")

        print("Polling for batch completion...")
        elapsed = 0
        while True:
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            batch = get_client().messages.batches.retrieve(batch_id)
            status = batch.processing_status
            print(f"  [{elapsed}s] Status: {status}")

            if status == "ended":
                break

            if elapsed >= MAX_POLL_SECONDS:
                raise TimeoutError(
                    f"Batch {batch_id} did not complete within {MAX_POLL_SECONDS}s"
                )

        print("Processing batch results...")
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
            print(
                f"{len(failed)} EOs failed: "
                f"{', '.join(str(o.executive_order_number) for o in failed)}"
            )

        if not succeeded:
            print("No EOs were successfully processed. Skipping deploy.")
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

        print("Building eo.json...")
        build_from_summaries()

        print("Deploying...")
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

        print(
            f"Pipeline complete. {len(succeeded)}/{eos_new} EOs processed and deployed."
        )


def main():
    runner = PipelineRunner()
    runner.run()


if __name__ == "__main__":
    main()
