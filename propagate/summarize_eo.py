#!/usr/bin/env python3

import json
import sys
import uuid
from pathlib import Path
from typing import Optional

from anthropic.types.message import Message
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from anthropic.types.messages.message_batch import MessageBatch
from propagate.config import MAX_TOKENS, MODEL
from propagate.logging_config import get_logger, setup_logging
from propagate.models import ExecutiveOrder, Summary
from propagate.prompts import PROMPT, SYSTEM_PROMPT_EXECUTIVE_ORDER
from propagate.util import (
    claude_json_to_summary,
    fetch_all_executive_orders,
    get_client,
    get_pdf_data,
    save_summary,
)

logger = get_logger(__name__)


def save_claude_json(json_data: dict, json_path: Path) -> Path:
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    return json_path


def create_claude_message(order: ExecutiveOrder) -> Message | None:
    """
    Create a Claude message for a given executive order.
    """
    pdf_data = get_pdf_data(order)

    # get size of pdf in bytes
    # pdf should be less than 33554432 bytes
    pdf_size = len(pdf_data)

    if pdf_size > 33554432:
        logger.error("PDF size is too large")
        return None

    message: Message | None = None
    try:
        # Create message with PDF attachment using file path
        message = get_client().messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT_EXECUTIVE_ORDER,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data,
                            },
                        },
                    ],
                }
            ],
        )
    except Exception as e:
        logger.error("Error calling Claude API: %s", e)
        sys.exit(1)

    return message


def create_claude_batch_request(order: ExecutiveOrder, uid: str) -> tuple[Request, int]:
    """
    Create a Claude message for a list of executive orders.
    """

    logger.info("Creating batch request with uid %s", uid)

    pdf_data = get_pdf_data(order)

    # get size of pdf in bytes
    pdf_size = int(len(pdf_data) / 1024 / 1024)  # convert to MB

    return (
        Request(
            custom_id=uid,
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT_EXECUTIVE_ORDER,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data,
                                },
                            },
                        ],
                    }
                ],
            ),
        ),
        pdf_size,
    )


def batch_summarize_with_claude(
    orders: list[ExecutiveOrder],
    president_key: str,
) -> tuple[MessageBatch, list[str]]:
    """
    Batch summarize a list of executive orders with Claude API.
    """

    # uid must be less than 8 characters
    uid_suffix = str(uuid.uuid4())[:8]
    client = get_client()
    requests = []
    request_ids = []
    for order in orders:
        uid = f"eo-{president_key}-{order.executive_order_number}-{uid_suffix}"
        request, _ = create_claude_batch_request(order, uid)
        if request is not None:
            requests.append(request)
            request_ids.append(uid)

    logger.info("Creating batch with %d requests", len(requests))
    response = client.messages.batches.create(requests=requests)
    return response, request_ids


def summarize_with_claude(order: ExecutiveOrder) -> Summary | None:
    """
    Send PDF file to Claude API for summarization.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with summary and metadata
    """

    message = create_claude_message(order)
    if message is None:
        logger.error("Error summarizing %s", order.pdf_path)
        return None

    summary = message.content[0].text
    summary_json = json.loads(summary)
    save_claude_json(summary_json, order.get_claude_json_path())

    return summary_json


def process_pdf(order: ExecutiveOrder, force: bool = False) -> Optional[Summary]:
    summary_path = order.get_summary_path()

    # Skip if summary already exists
    if summary_path.exists() and not force:
        raise Exception(f"Summary already exists for {order.pdf_path}")

    logger.info("Processing %s...", order.pdf_path)

    # Summarize with Claude using the PDF file directly
    summary_data = summarize_with_claude(order)
    if summary_data is None:
        raise Exception(f"Error summarizing {order.pdf_path}")

    summary = claude_json_to_summary(summary_data, order)

    logger.info("President: %s", summary.president)

    # Save summary
    saved_path = save_summary(summary, summary_path)
    logger.info("Summary saved to %s", saved_path)

    return summary


def main():
    """Summarizes the EO based on the executive order number"""
    setup_logging()

    if len(sys.argv) != 2:
        print("Usage: python summarize_eo.py <eo_number>")
        sys.exit(1)

    eo_number = int(sys.argv[1])

    orders = fetch_all_executive_orders()
    for order in orders:
        if order.executive_order_number == eo_number:
            process_pdf(order, force=True)
            break

    logger.info("Summarized %d", eo_number)


if __name__ == "__main__":
    main()
