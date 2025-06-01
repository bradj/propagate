#!/usr/bin/env python3
import requests
from config import PDF_DIR
from summarize_eo import process_pdf
import traceback
from util import fetch_all_executive_orders


def main():
    """Main function to fetch and download executive orders."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    successful_orders = []
    try:
        print("Starting to fetch and download all executive orders...")
        successful_orders = fetch_all_executive_orders()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

    try:
        for order in successful_orders:
            process_pdf(order)
    except Exception as e:
        print(f"Error processing PDF: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
