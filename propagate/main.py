#!/usr/bin/env python3
import sys
import requests
import uuid
from config import PDF_DIR
from summarize_eo import process_pdf, batch_summarize_with_claude
import traceback
from util import fetch_all_executive_orders


def main():
    """Main function to fetch and download executive orders."""
    batch = False
    if len(sys.argv) == 2:
        batch = sys.argv[1] == "batch"

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    orders = []
    try:
        print("Starting to fetch and download all executive orders...")
        orders = fetch_all_executive_orders()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

    if batch:
        response, request_ids = batch_summarize_with_claude(orders)
        print(response)

        # save request ids to a file
        with open("request_ids.txt", "w") as f:
            for request_id in request_ids:
                f.write(request_id + "\n")

        sys.exit(0)

    try:
        for order in orders:
            process_pdf(order)
    except Exception as e:
        print(f"Error processing PDF: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
