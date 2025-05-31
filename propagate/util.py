from executive_order import ExecutiveOrder
from summary import Summary
from pathlib import Path
import json
from typing import List
import requests
from config import PDF_DIR, SUMMARIES_DIR, CLAUDE_API_KEY
import anthropic
import sys


CHUNK_SIZE = 8192  # Size of chunks when downloading files
BASE_URL = "https://www.federalregister.gov/api/v1/documents.json"

client: anthropic.Anthropic | None = None


def get_client():
    global client

    if not CLAUDE_API_KEY:
        print(
            "Claude API key is required. Set the ANTHROPIC_API_KEY environment variable."
        )
        sys.exit(1)

    if client is None:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    return client


def convert_to_json(obj):
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def download_pdf(order: ExecutiveOrder, force: bool = False) -> Path:
    if not order.pdf_url:
        raise ValueError("No PDF URL available")

    filename = f"EO-{order.executive_order_number or 'unknown'}.pdf"
    filepath = PDF_DIR / filename

    # Check if file already exists
    if filepath.exists() and not force:
        return filepath

    response = requests.get(order.pdf_url, stream=True)
    response.raise_for_status()

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            f.write(chunk)

    return filepath


def download_all_pdfs(
    orders: List[ExecutiveOrder], force: bool = False
) -> list[ExecutiveOrder]:
    success_orders = []
    for order in orders:
        pdf_path = download_pdf(order, force)
        if not pdf_path:
            continue

        order.pdf_path = pdf_path
        success_orders.append(order)

    return success_orders


def fetch_all_executive_orders(
    president: str = "donald-trump",
    start_date: str = "01/20/2025",
    end_date: str = "05/31/2025",
    per_page: int = 1000,
) -> List[ExecutiveOrder]:
    params = {
        "conditions[correction]": 0,
        "conditions[president]": president,
        "conditions[presidential_document_type]": "executive_order",
        "conditions[signing_date][gte]": start_date,
        "conditions[signing_date][lte]": end_date,
        "conditions[type][]": "PRESDOCU",
        "fields[]": [
            "citation",
            "document_number",
            "end_page",
            "html_url",
            "pdf_url",
            "type",
            "subtype",
            "publication_date",
            "signing_date",
            "start_page",
            "title",
            "disposition_notes",
            "executive_order_number",
            "not_received_for_publication",
            "full_text_xml_url",
            "body_html_url",
            "json_url",
        ],
        "include_pre_1994_docs": "true",
        "order": "executive_order",
        "per_page": per_page,
    }

    success_orders = []
    page_number = 1
    current_url = BASE_URL

    while current_url:
        print(f"Fetching page {page_number}...")

        # Use the current_url (which might be a next_page_url from previous response)
        if page_number == 1:
            response = requests.get(current_url, params=params)
        else:
            response = requests.get(current_url)

        response.raise_for_status()
        data = response.json()

        # Extract and process results
        results = data.get("results", [])
        if results:
            orders = [ExecutiveOrder.from_dict(item) for item in results]
            print(f"  Found {len(orders)} executive orders on page {page_number}")

            # Download PDFs for this page immediately
            orders = download_all_pdfs(orders)
            success_orders.extend(orders)

        # Check for next page
        next_page_url = data.get("next_page_url")
        if next_page_url:
            current_url = next_page_url
            page_number += 1
        else:
            break

    return success_orders


def get_claude_json_path(order: ExecutiveOrder) -> Path:
    return Path(f"{SUMMARIES_DIR}/EO-{order.executive_order_number}-claude.json")


def get_summary_path(order: ExecutiveOrder) -> Path:
    return Path(f"{SUMMARIES_DIR}/EO-{order.executive_order_number}.json")


def get_summary_path_eo(eo_number: str) -> Path:
    return Path(f"{SUMMARIES_DIR}/EO-{eo_number}.json")


"""
This is the function that gets the summaries for all the executive orders.
It fetches all the executive orders from the Federal Register and then gets the summaries for each of them.
It then returns a list of Summary objects. It will only return summaries that already exist.
"""


def get_summaries() -> list[Summary]:
    eos = fetch_all_executive_orders()
    summaries = []
    for eo in eos:
        summary_path = get_summary_path(eo)
        if not summary_path.exists():
            continue

        with open(summary_path, "r") as f:
            summary = json.load(f)
            summaries.append(Summary(**summary))

    return summaries
