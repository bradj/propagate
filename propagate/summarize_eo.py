#!/usr/bin/env python3

from executive_order import ExecutiveOrder
from summary import Summary
import os
import json
import base64
from pathlib import Path
from typing import Optional
import anthropic
import sys


MODEL: str = os.environ.get("PROPAGATE_MODEL")
PDF_DIR: Path = Path(os.environ.get("PROPAGATE_PDF_DIR"))
SUMMARIES_DIR: Path = Path(os.environ.get("PROPAGATE_SUMMARIES_DIR"))
api_key: str | None = os.environ.get("PROPAGATE_ANTHROPIC_API_KEY")
MAX_SUMMARY_LENGTH: int = 250
client: anthropic.Anthropic | None = None

def get_client():
    global client
    
    if not api_key:
        print("Claude API key is required. Set the ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)
    
    if client is None:
        client = anthropic.Anthropic(api_key=api_key)
    return client


def summarize_with_claude(order: ExecutiveOrder) -> Summary:
    """
    Send PDF file to Claude API for summarization.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with summary and metadata
    """
    
    prompt = f"""The response should be a valid JSON object with the following fields. There should be no other text in the response. Do not include ```json or ``` in the response:
    - summary: Create summary with {MAX_SUMMARY_LENGTH} characters or less
    - purpose: What is the stated purpose of the Executive Order?
    - effective_date: What is the stated effective date of the Executive Order?
    - expiration_date: What is the stated expiration date of the Executive Order?
    - economic_effects: Highlight potential economic effects
    - geopolitical_effects: Highlight potential geopolitical effects
    - deeper_dive: A deeper dive into what the Executive Order does and broader effects
    - positive_impacts: What are the potential positive impacts of the Executive Order?
    - negative_impacts: What are the potential negative impacts of the Executive Order?
    - key_industries: What industries are most likely to be impacted by the Executive Order?
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
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        sys.exit(1)
    
    summary = message.content[0].text
    print(summary)
    summary_json = json.loads(summary)
    
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
    )


def save_summary(summary: Summary, json_path: Path) -> Path:
    """
    Save the summary to a JSON file.
    
    Args:
        summary_data: The summary data
        pdf_path: Path to the PDF file
        
    Returns:
        Path to the saved summary file
    """
    summary_file = json_path
    
    with open(summary_file, "w") as f:
        json.dump(
            {
                "deeper_dive": summary.deeper_dive,
                "economic_effects": summary.economic_effects,
                "effective_date": summary.effective_date,
                "expiration_date": summary.expiration_date,
                "geopolitical_effects": summary.geopolitical_effects,
                "pdf_file": str(summary.pdf_path),
                "publication_date": summary.publication_date,
                "purpose": summary.purpose,
                "signing_date": summary.signing_date,
                "summary": summary.summary,
                "timestamp": str(os.path.getmtime(summary.pdf_path)),
                "title": summary.title,
            },
            f,
            indent=2
        )
    
    return summary_file

def process_pdf(order: ExecutiveOrder, force: bool = False) -> Optional[Summary]:
    summary_file = SUMMARIES_DIR / f"{order.pdf_path}.json"
    
    # Skip if summary exists and force is False
    if summary_file.exists() and not force:
        print(f"Summary for {order.pdf_path} already exists. Skipping.")
        return None
    
    print(f"Processing {order.pdf_path}...")
    
    # Summarize with Claude using the PDF file directly
    summary_data = summarize_with_claude(order)

    if summary_data is None:
        print(f"Error summarizing {order.pdf_path}")
        return None
    
    # Save summary
    saved_path = save_summary(summary_data, f'{SUMMARIES_DIR}/EO-{order.executive_order_number}.json')
    print(f"  Summary saved to {saved_path}")
    
    return summary_data


def main():
    """Main function to summarize Executive Order PDFs."""
    # Get API key from environment variable
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process all PDFs
    print("Starting to summarize all Executive Order PDFs...")
    for pdf_path in PDF_DIR.glob("*.pdf"):
        process_pdf(pdf_path)
        break
    
    print("\nCompleted! Summaries are saved in the eo/summaries directory.")


if __name__ == "__main__":
    main()
