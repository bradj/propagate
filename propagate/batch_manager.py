#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

import requests
from propagate.build import build_from_claude_batch
from propagate.logging_config import get_logger, setup_logging
from propagate.util import get_client

logger = get_logger(__name__)


def list_batches(limit: int = 20):
    """List recent batches from Anthropic API."""
    client = get_client()

    response = client.messages.batches.list(limit=limit)

    logger.info("Recent batches (showing up to %d)", limit)
    for batch in response.data:
        total = (
            batch.request_counts.processing
            + batch.request_counts.succeeded
            + batch.request_counts.errored
            + batch.request_counts.canceled
            + batch.request_counts.expired
        )
        logger.info(
            "Batch %s status=%s created=%s total=%d succeeded=%d processing=%d",
            batch.id, batch.processing_status, batch.created_at,
            total, batch.request_counts.succeeded, batch.request_counts.processing,
        )
        if batch.request_counts.errored > 0:
            logger.error("Batch %s errored=%d", batch.id, batch.request_counts.errored)
        if hasattr(batch, "results_url") and batch.results_url:
            logger.info("Batch %s results available for download", batch.id)


def get_batch_status(batch_id: str):
    """Get status of a specific batch."""
    client = get_client()

    try:
        batch = client.messages.batches.retrieve(batch_id)
        total = (
            batch.request_counts.processing
            + batch.request_counts.succeeded
            + batch.request_counts.errored
            + batch.request_counts.canceled
            + batch.request_counts.expired
        )
        logger.info(
            "Batch %s status=%s created=%s total=%d succeeded=%d processing=%d",
            batch.id, batch.processing_status, batch.created_at,
            total, batch.request_counts.succeeded, batch.request_counts.processing,
        )
        if batch.request_counts.errored > 0:
            logger.error("Batch %s errored=%d", batch.id, batch.request_counts.errored)
        if batch.request_counts.canceled > 0:
            logger.info("Batch %s canceled=%d", batch.id, batch.request_counts.canceled)
        if batch.request_counts.expired > 0:
            logger.info("Batch %s expired=%d", batch.id, batch.request_counts.expired)
        if hasattr(batch, "results_url") and batch.results_url:
            logger.info("Batch %s results_url=%s", batch.id, batch.results_url)
    except Exception as e:
        logger.error("Error retrieving batch: %s", e)


def download_and_process_batch(batch_id: str):
    """Download batch results and process them."""
    client = get_client()

    # Get batch info
    try:
        batch = client.messages.batches.retrieve(batch_id)
    except Exception as e:
        logger.error("Error retrieving batch %s: %s", batch_id, e)
        return

    if batch.processing_status != "ended":
        logger.error("Batch is not complete. Status: %s", batch.processing_status)
        return

    if not hasattr(batch, "results_url") or not batch.results_url:
        logger.error("No results URL available for batch %s", batch_id)
        return

    output_dir = Path("batch_results")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"batch_{batch_id}.jsonl"

    logger.info("Downloading batch results...")
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

    logger.info("Downloaded to %s", output_file)

    logger.info("Processing batch results...")
    build_from_claude_batch(output_file)
    logger.info("Batch processing complete")


def main():
    setup_logging()
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
