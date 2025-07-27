#!/usr/bin/env python3
"""
Manage Claude batch requests - list, check status, and process results.
"""
import argparse
import os
import requests
from pathlib import Path
from util import get_client
from build import build_from_claude_batch


def list_batches(limit: int = 20):
    """List recent batches from Anthropic API."""
    client = get_client()

    # Get recent batches
    response = client.messages.batches.list(limit=limit)

    print(f"Recent batches (showing up to {limit}):\n")
    for batch in response.data:
        print(f"Batch ID: {batch.id}")
        print(f"  Status: {batch.processing_status}")
        print(f"  Created: {batch.created_at}")
        total = (
            batch.request_counts.processing
            + batch.request_counts.succeeded
            + batch.request_counts.errored
            + batch.request_counts.canceled
            + batch.request_counts.expired
        )
        print(f"  Total requests: {total}")
        print(f"    Processing: {batch.request_counts.processing}")
        print(f"    Succeeded: {batch.request_counts.succeeded}")
        if batch.request_counts.errored > 0:
            print(f"    Errored: {batch.request_counts.errored}")
        if hasattr(batch, "results_url") and batch.results_url:
            print(f"  Results: Available for download")
        print()


def get_batch_status(batch_id: str):
    """Get status of a specific batch."""
    client = get_client()

    try:
        batch = client.messages.batches.retrieve(batch_id)
        print(f"Batch ID: {batch.id}")
        print(f"Status: {batch.processing_status}")
        print(f"Created: {batch.created_at}")
        total = (
            batch.request_counts.processing
            + batch.request_counts.succeeded
            + batch.request_counts.errored
            + batch.request_counts.canceled
            + batch.request_counts.expired
        )
        print(f"Total requests: {total}")
        print(f"  Processing: {batch.request_counts.processing}")
        print(f"  Succeeded: {batch.request_counts.succeeded}")
        if batch.request_counts.errored > 0:
            print(f"  Errored: {batch.request_counts.errored}")
        if batch.request_counts.canceled > 0:
            print(f"  Canceled: {batch.request_counts.canceled}")
        if batch.request_counts.expired > 0:
            print(f"  Expired: {batch.request_counts.expired}")
        if hasattr(batch, "results_url") and batch.results_url:
            print(f"Results URL: {batch.results_url}")
    except Exception as e:
        print(f"Error retrieving batch: {e}")


def download_and_process_batch(batch_id: str):
    """Download batch results and process them."""
    client = get_client()

    # Get batch info
    try:
        batch = client.messages.batches.retrieve(batch_id)
    except Exception as e:
        print(f"Error retrieving batch: {e}")
        return

    if batch.processing_status != "ended":
        print(f"Batch is not complete. Status: {batch.processing_status}")
        return

    if not hasattr(batch, "results_url") or not batch.results_url:
        print("No results URL available for this batch")
        return

    # Download results
    output_dir = Path("batch_results")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"batch_{batch_id}.jsonl"

    print(f"Downloading batch results...")
    # add PROPAGATE_ANTHROPIC_API_KEY to x-api-key header
    response = requests.get(
        batch.results_url,
        headers={
            "anthropic-version": "2023-06-01",
            "x-api-key": os.getenv("PROPAGATE_ANTHROPIC_API_KEY"),
        },
    )
    response.raise_for_status()

    with open(output_file, "wb") as f:
        f.write(response.content)

    print(f"Downloaded to {output_file}")

    # Process the results
    print("\nProcessing batch results...")
    build_from_claude_batch(output_file)
    print("Batch processing complete!")


def main():
    parser = argparse.ArgumentParser(description="Manage Claude batch requests")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List recent batches")
    list_parser.add_argument(
        "--limit", type=int, default=20, help="Number of batches to show"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Get batch status")
    status_parser.add_argument("batch_id", help="Batch ID to check")

    # Process command
    process_parser = subparsers.add_parser("process", help="Download and process batch")
    process_parser.add_argument("batch_id", help="Batch ID to process")

    args = parser.parse_args()

    if args.command == "list":
        list_batches(args.limit)
    elif args.command == "status":
        get_batch_status(args.batch_id)
    elif args.command == "process":
        download_and_process_batch(args.batch_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
