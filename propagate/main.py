#!/usr/bin/env python3
import sys
import requests
from config import PDF_DIR
from summarize_eo import process_pdf, batch_summarize_with_claude
import traceback
from federalregister import fetch_all_executive_orders
from models import President


def fetch_and_process_president(
    president: President, batch: bool = False, force: bool = False
):
    orders = []
    try:
        print(
            f"Starting to fetch and download executive orders for {president.name}..."
        )
        orders = fetch_all_executive_orders(president=president.key, force=force)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

    # Set president information on each order
    for order in orders:
        order.president = president.name

    if not force:
        orders = [order for order in orders if not order.summary_exists()]

    print(f"Found {len(orders)} orders to process for {president.name}")

    if len(orders) == 0:
        print(f"No orders to process for {president.name}")
        return

    # find duplicate orders
    for order in orders:
        if order.executive_order_number in [
            o.executive_order_number for o in orders if o != order
        ]:
            print(f"Duplicate order found: {order.executive_order_number}")
            # remove the duplicate
            orders.remove(order)

    if batch:
        # For batch mode with force, we need to pass all orders
        # For batch mode without force, orders are already filtered
        response, request_ids = batch_summarize_with_claude(orders)

        print("\n" + "=" * 60)
        print(f"BATCH CREATED SUCCESSFULLY")
        print(f"Batch ID: {response.id}")
        print(f"President: {president.name}")
        print(f"Orders: {len(request_ids)}")
        print("=" * 60)
        print(
            f"\nTo check status: python propagate/batch_manager.py status {response.id}"
        )
        print(
            f"To process when ready: python propagate/batch_manager.py process {response.id}"
        )

        # append request ids to a file with batch ID as header
        with open(f"request_ids_{president.key}.txt", "a") as f:
            f.write(f"\n# Batch ID: {response.id}\n")
            for request_id in request_ids:
                f.write(request_id + "\n")

        print(f"\nSaved request ids to request_ids_{president.key}.txt")
        return

    try:
        for order in orders:
            process_pdf(order, force=force)
            print(f"Processed {order.executive_order_number}")
    except Exception as e:
        print(f"Error processing PDF: {e}")
        traceback.print_exc()


def main():
    """Main function to fetch and download executive orders."""
    import argparse
    from models import PRESIDENTS

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
        help=f'President to process (default: {default_president}). Use "all" for all presidents.',
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
