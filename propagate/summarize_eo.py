#!/usr/bin/env python3

from config import MODEL, PDF_DIR, SUMMARIES_DIR, MAX_SUMMARY_LENGTH
from executive_order import ExecutiveOrder
from pathlib import Path
from summary import Summary, Categories
from typing import Optional
from util import convert_to_json, get_claude_json_path, get_summary_path
from util import get_client
import anthropic
import base64
import json
import sys


def save_claude_json(json_data: dict, json_path: Path) -> Path:
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    return json_path


def summarize_with_claude(order: ExecutiveOrder) -> Summary:
    """
    Send PDF file to Claude API for summarization.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with summary and metadata
    """

    prompt = f"""The response should be a valid JSON object with the following fields. Escape all quotes in the response. Validate it's a valid JSON object. There should be no other text in the response. Do not include ```json or ``` in the response:
    - summary: Create summary with {MAX_SUMMARY_LENGTH} characters or less
    - purpose: What is the stated purpose of the Executive Order?
    - effective_date: What is the stated effective date of the Executive Order?
    - expiration_date: What is the stated expiration date of the Executive Order?
    - economic_effects: Highlight potential economic effects
    - geopolitical_effects: Highlight potential geopolitical effects
    - deeper_dive: A deeper dive into what the Executive Order does and broader effects
    - positive_impacts: What are the potential positive impacts of the Executive Order?
    - negative_impacts: What are the potential negative impacts of the Executive Order?
    - key_industries: What industries are most likely to be impacted by the Executive Order? Only select from the following list of industries:
        - Government & Public Administration
        - Defense & National Security
        - Technology & Cybersecurity
        - Financial Services
        - Healthcare & Pharmaceuticals
        - Energy & Utilities
        - Manufacturing & Industry
        - Education & Research
        - Legal Services & Compliance
        - Agriculture & Natural Resources
    - categories: Qualify the executive order picking a value for each of the following categories:
        - policy_domain: Economic, Defense, Healthcare, Education, Environmental, Immigration, Energy, Transportation, Civil Rights, Foreign Relations
        - regulatory_impact: Deregulatory, Regulatory, Guidance-oriented, Agency reorganization
        - constitutional_authority: National security powers, Emergency powers, Administrative powers, Treaty implementation
        - duration: Temporary/time-limited, Permanent, Contingent on specific conditions
        - scope_of_impact: Federal agencies only, State/local government coordinination, Private sector involvement, Individual rights
        - political_context: Campaign promise fulfillment, Response to crisis, Reversal of predecessor's policy, Congressional gridlock workaround
        - legal_framework: Statutory interpretation, Constitutional interpretation, International law implementation, Agency rulemaking direction
        - budgetary_implications: Budget neutral, Requires new appropriations, Reallocates existing funds, Cost-saving measures
        - implementation_timeline: Immediate effect, Phased implementation, Delayed effective date, Contingent implementation
        - precedential_value: Novel/first-of-its-kind, Consistent with historical practice, Expansion of existing policy, Restatement of existing authority
    """

    pdf_data = None
    try:
        with open(order.pdf_path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

    message: anthropic.Message | None = None
    try:
        # Create message with PDF attachment using file path
        message = get_client().messages.create(
            model=MODEL,
            max_tokens=1024,
            system="You are a helpful assistant that summarizes executive orders concisely.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
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


def process_pdf(order: ExecutiveOrder) -> Optional[Summary]:
    summary_path = get_summary_path(order)

    # Skip if summary already exists
    if summary_path.exists():
        print(f"Summary already exists for {order.pdf_path}, skipping...")
        return None

    print(f"Processing {order.pdf_path}...")

    # if claude json exists, use the claude json
    claude_json_path = get_claude_json_path(order)
    summary_data = None
    if claude_json_path.exists():
        with open(claude_json_path, "r") as f:
            summary_data = json.load(f)
    else:
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
    """Main function to summarize Executive Order PDFs."""
    from util import fetch_all_executive_orders

    # Get API key from environment variable
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch all executive orders (this will also download PDFs if needed)
    print("Fetching Executive Orders...")
    orders = fetch_all_executive_orders()

    # Process all orders for summarization
    print("Starting to summarize Executive Order PDFs...")
    processed_count = 0
    skipped_count = 0

    for order in orders:
        result = process_pdf(order)
        if result is None:
            skipped_count += 1
        else:
            processed_count += 1

    print(f"\nCompleted! Processed: {processed_count}, Skipped: {skipped_count}")
    print("Summaries are saved in the summaries directory.")


if __name__ == "__main__":
    main()
