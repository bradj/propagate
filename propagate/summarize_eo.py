#!/usr/bin/env python3

from config import MODEL, MAX_TOKENS
from prompts import PROMPT, SYSTEM_PROMPT
from pathlib import Path
from models import ExecutiveOrder, Summary, Categories
from typing import Optional
from util import (
    convert_to_json,
    get_claude_json_path,
    get_summary_path,
    fetch_all_executive_orders,
    get_pdf_data,
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
            system=SYSTEM_PROMPT,
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


def create_claude_batch_request(order: ExecutiveOrder, uid: str) -> Request:
    """
    Create a Claude message for a list of executive orders.
    """

    uid = f"eo-{order.executive_order_number}-{uid}"
    print(f"Creating batch request with uid {uid}")

    pdf_data = get_pdf_data(order)

    return Request(
        custom_id=uid,
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
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
    )


def batch_summarize_with_claude(
    orders: list[ExecutiveOrder],
) -> tuple[MessageBatch, list[str]]:
    """
    Batch summarize a list of executive orders with Claude API.
    """

    # uid must be less than 8 characters
    uid = str(uuid.uuid4())[:8]
    client = get_client()
    requests = []
    request_ids = []
    for order in orders:
        r = create_claude_batch_request(order, uid)
        if r is not None:
            requests.append(r)
            request_ids.append(r["custom_id"])

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
    save_claude_json(summary_json, get_claude_json_path(order))

    return summary_json


def claude_json_to_summary(summary_json: dict, order: ExecutiveOrder) -> Summary:
    categories = Categories(
        policy_domain=summary_json["categories"]["policy_domain"],
        regulatory_impact=summary_json["categories"]["regulatory_impact"],
        constitutional_authority=summary_json["categories"]["constitutional_authority"],
        duration=summary_json["categories"]["duration"],
        scope_of_impact=summary_json["categories"]["scope_of_impact"],
        political_context=summary_json["categories"]["political_context"],
        legal_framework=summary_json["categories"]["legal_framework"],
        budgetary_implications=summary_json["categories"]["budgetary_implications"],
        implementation_timeline=summary_json["categories"]["implementation_timeline"],
        precedential_value=summary_json["categories"]["precedential_value"],
    )

    return Summary(
        title=order.title,
        summary=summary_json["summary"],
        purpose=summary_json["purpose"],
        effective_date=summary_json["effective_date"],
        expiration_date=summary_json["expiration_date"],
        economic_effects=summary_json["economic_effects"],
        geopolitical_effects=summary_json["geopolitical_effects"],
        deeper_dive=summary_json["deeper_dive"],
        pdf_path=order.pdf_path,
        publication_date=order.publication_date,
        signing_date=order.signing_date,
        original_url=order.html_url,
        eo_number=int(order.executive_order_number),
        positive_impacts=summary_json["positive_impacts"],
        negative_impacts=summary_json["negative_impacts"],
        key_industries=summary_json["key_industries"],
        categories=categories,
    )


def save_summary(summary: Summary, summary_path: Path) -> Path:
    """
    Save the summary to a JSON file.

    Args:
        summary_data: The summary data
        pdf_path: Path to the PDF file

    Returns:
        Path to the saved summary file
    """
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=convert_to_json)

    return summary_path


def process_pdf(order: ExecutiveOrder, force: bool = False) -> Optional[Summary]:
    summary_path = get_summary_path(order)

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
