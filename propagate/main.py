#!/usr/bin/env python3
import json

import requests
from propagate.config import PDF_DIR
from propagate.federalregister import fetch_all_executive_orders
from propagate.logging_config import get_logger, setup_logging
from propagate.models import President
from propagate.summarize_eo import batch_summarize_with_claude, process_pdf

logger = get_logger(__name__)


def print_last_processed(orders):
    processed = [o for o in orders if o.summary_exists()]
    if not processed:
        logger.info("No previously processed EOs found.")
        return

    last = max(processed, key=lambda o: o.signing_date or "")
    summary_path = last.get_summary_path()
    signing_date = last.signing_date
    title = last.title
    if summary_path.exists():
        with open(summary_path) as f:
            data = json.load(f)
            signing_date = data.get("signing_date", signing_date)
            title = data.get("title", title)

    logger.info(
        "Last processed EO: %s - %s (signed %s)",
        last.executive_order_number, title, signing_date,
    )


def print_pending(orders):
    if not orders:
        return
    logger.info("Pending EOs (%d)", len(orders))
    for order in sorted(orders, key=lambda o: o.signing_date or ""):
        logger.info("  EO %s: %s (%s)", order.executive_order_number, order.title, order.signing_date)


def fetch_and_process_president(
    president: President, batch: bool = False, force: bool = False
):
    orders = []
    try:
        logger.info("Starting to fetch and download executive orders for %s", president.name)
        orders = fetch_all_executive_orders(president=president.key, force=force)
    except requests.exceptions.RequestException as e:
        logger.error("Error fetching data: %s", e)

    # Set president information on each order
    for order in orders:
        order.president = president.name

    print_last_processed(orders)

    if not force:
        orders = [order for order in orders if not order.summary_exists()]

    print_pending(orders)

    if len(orders) == 0:
        logger.info("No orders to process for %s", president.name)
        return

    # find duplicate orders
    for order in orders:
        if order.executive_order_number in [
            o.executive_order_number for o in orders if o != order
        ]:
            logger.error("Duplicate order found: %s", order.executive_order_number)
            # remove the duplicate
            orders.remove(order)

    if batch:
        # For batch mode with force, we need to pass all orders
        # For batch mode without force, orders are already filtered
        response, request_ids = batch_summarize_with_claude(orders, president.key)

        logger.info(
            "Batch created: id=%s president=%s orders=%d",
            response.id, president.name, len(request_ids),
        )
        logger.info("Check status: python propagate/batch_manager.py status %s", response.id)
        logger.info("Process when ready: python propagate/batch_manager.py process %s", response.id)

        # append request ids to a file with batch ID as header
        with open(f"request_ids_{president.key}.txt", "a") as f:
            f.write(f"\n# Batch ID: {response.id}\n")
            for request_id in request_ids:
                f.write(request_id + "\n")

        logger.info("Saved request ids to request_ids_%s.txt", president.key)
        return

    try:
        for order in orders:
            process_pdf(order, force=force)
            logger.info("Processed %s", order.executive_order_number)
    except Exception as e:
        logger.error("Error processing PDF", exc_info=True)


def main():
    """Main function to fetch and download executive orders."""
    import argparse

    setup_logging()

    from propagate.models import PRESIDENTS

    # Build list of valid president choices
    president_choices = [p.key for p in PRESIDENTS] + ["all"]
    default_president = PRESIDENTS[0].key  # First president in list

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Fetch and process executive orders")
    parser.add_argument(
        "mode", nargs="?", choices=["batch"], help="Processing mode (optional)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of all orders, overwriting existing summaries",
    )
    parser.add_argument(
        "--president",
        choices=president_choices,
        default=default_president,
        help=(
            f"President to process (default: {default_president})."
            ' Use "all" for all presidents.'
        ),
    )

    args = parser.parse_args()

    batch = args.mode == "batch"
    force = args.force

    PDF_DIR.mkdir(parents=True, exist_ok=True)

    # Determine which presidents to process
    if args.president == "all":
        presidents_to_process = PRESIDENTS
    else:
        presidents_to_process = [p for p in PRESIDENTS if p.key == args.president]

    for president in presidents_to_process:
        fetch_and_process_president(president, batch, force)


if __name__ == "__main__":
    main()
