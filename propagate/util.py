from models import ExecutiveOrder, Summary, Categories
from federalregister import fetch_all_executive_orders
from pathlib import Path
import json
from config import CLAUDE_API_KEY
import anthropic
import sys
import base64

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


"""
This is the function that gets the summaries for all the executive orders.
It fetches all the executive orders from the Federal Register and then gets the summaries for each of them.
It then returns a list of Summary objects. It will only return summaries that already exist.
"""


def get_summaries() -> list[Summary]:
    eos = fetch_all_executive_orders()
    summaries = []
    for eo in eos:
        summary_path = eo.get_summary_path()
        if not summary_path.exists():
            continue

        with open(summary_path, "r") as f:
            summary = json.load(f)
            summaries.append(Summary(**summary))

    return summaries


def get_pdf_data(order: ExecutiveOrder) -> str:
    with open(order.pdf_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


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
        president=order.president,
        categories=categories,
    )
