#!/usr/bin/env python3
import requests
from pathlib import Path
from typing import List
from executive_order import ExecutiveOrder
from summarize_eo import process_pdf
import traceback
class FederalRegisterClient:
    """Client for interacting with the Federal Register API."""

    BASE_URL = "https://www.federalregister.gov/api/v1/documents.json"
    PDF_DIR = Path("eo/pdf")
    CHUNK_SIZE = 8192  # Size of chunks when downloading files

    def __init__(self):
        """Initialize the client and ensure the PDF directory exists."""
        self.PDF_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_all_executive_orders(
        self,
        president: str = "donald-trump",
        start_date: str = "01/20/2025",
        end_date: str = "03/29/2025",
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
        current_url = self.BASE_URL

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
                orders = self.download_all_pdfs(orders)
                success_orders.extend(orders)

            # Check for next page
            next_page_url = data.get("next_page_url")
            if next_page_url:
                current_url = next_page_url
                page_number += 1
            else:
                break

        return success_orders

    def download_pdf(
        self, order: ExecutiveOrder, force: bool = False
    ) -> Path:
        if not order.pdf_url:
            raise ValueError("No PDF URL available")

        filename = f"EO-{order.executive_order_number or 'unknown'}.pdf"
        filepath = self.PDF_DIR / filename

        # Check if file already exists
        if filepath.exists() and not force:
            return filepath

        response = requests.get(order.pdf_url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                f.write(chunk)

        return filepath

    def download_all_pdfs(
        self, orders: List[ExecutiveOrder], force: bool = False
    ) -> list[ExecutiveOrder]:
        success_orders = []
        for order in orders:
            pdf_path = self.download_pdf(order, force)
            if not pdf_path:
                continue

            order.pdf_path = pdf_path
            success_orders.append(order)

        return success_orders


def main():
    """Main function to fetch and download executive orders."""
    client = FederalRegisterClient()
    successful_orders = []
    try:
        print("Starting to fetch and download all executive orders...")
        successful_orders = client.fetch_all_executive_orders()

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
