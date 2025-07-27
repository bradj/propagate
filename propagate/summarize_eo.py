#!/usr/bin/env python3

from config import MODEL, MAX_TOKENS
from prompts import PROMPT, SYSTEM_PROMPT_EXECUTIVE_ORDER
from pathlib import Path
from models import ExecutiveOrder, Summary
from typing import Optional
from util import (
    fetch_all_executive_orders,
    get_pdf_data,
    save_summary,
    claude_json_to_summary,
)
from util import get_client
import anthropic
from anthropic.types.messages.message_batch import MessageBatch
from anthropic.types.messages.batch_create_params import Request
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.message import Message
import json
import sys
import uuid


def save_claude_json(json_data: dict, json_path: Path) -> Path:
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    return json_path


def create_claude_message(order: ExecutiveOrder) -> Message:
    """
    Create a Claude message for a given executive order.
    """
    pdf_data = get_pdf_data(order)

    message: anthropic.Message | None = None
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
        print(f"Error calling Claude API: {e}")
        sys.exit(1)

    return message


def create_claude_batch_request(order: ExecutiveOrder, uid: str) -> tuple[Request, int]:
    """
    Create a Claude message for a list of executive orders.
    """

    print(f"Creating batch request with uid {uid}")

    pdf_data = get_pdf_data(order)

    # get size of pdf in bytes
    pdf_size = len(pdf_data) / 1024 / 1024  # convert to MB

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
        uid = f"eo-{order.executive_order_number}-{uid_suffix}"
        request, _ = create_claude_batch_request(order, uid)
        if request is not None:
            requests.append(request)
            request_ids.append(uid)

    print("Creating batch...")
    response = client.messages.batches.create(requests=requests)
    return response, request_ids


def summarize_with_claude(order: ExecutiveOrder) -> Summary:
    """
    Send PDF file to Claude API for summarization.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with summary and metadata
    """

    message = create_claude_message(order)
    if message is None:
        print(f"Error summarizing {order.pdf_path}")
        return None

    summary = message.content[0].text
    summary_json = json.loads(summary)
    save_claude_json(summary_json, order.get_claude_json_path())

    return summary_json


def process_pdf(order: ExecutiveOrder, force: bool = False) -> Optional[Summary]:
    summary_path = order.get_summary_path()

    # Skip if summary already exists
    if summary_path.exists() and not force:
        print(f"Summary already exists for {order.pdf_path}, skipping...")
        return None

    print(f"Processing {order.pdf_path}...")

    # Summarize with Claude using the PDF file directly
    summary_data = summarize_with_claude(order)
    if summary_data is None:
        print(f"Error summarizing {order.pdf_path}")
        return None

    summary = claude_json_to_summary(summary_data, order)

    # Save summary
    saved_path = save_summary(summary, summary_path)
    print(f"  Summary saved to {saved_path}")

    return summary


def main():
    """Summarizes the EO based on the executive order number"""
    if len(sys.argv) != 2:
        print("Usage: python summarize_eo.py <eo_number>")
        sys.exit(1)

    eo_number = int(sys.argv[1])

    orders = fetch_all_executive_orders()
    for order in orders:
        if order.executive_order_number == eo_number:
            process_pdf(order, force=True)
            break

    print(f"Summarized {eo_number}")


if __name__ == "__main__":
    main()
