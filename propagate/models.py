from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Categories:
    policy_domain: str
    regulatory_impact: str
    constitutional_authority: str
    duration: str
    scope_of_impact: str
    political_context: str
    legal_framework: str
    budgetary_implications: str
    implementation_timeline: str
    precedential_value: str


@dataclass
class Summary:
    categories: Categories
    deeper_dive: str
    economic_effects: str
    effective_date: str
    eo_number: int
    expiration_date: str
    geopolitical_effects: str
    key_industries: str
    negative_impacts: str
    original_url: str
    pdf_path: Path
    positive_impacts: str
    publication_date: str
    purpose: str
    signing_date: str
    summary: str
    title: str


@dataclass
class ExecutiveOrder:
    """Represents an Executive Order from the Federal Register."""

    citation: Optional[str] = None
    document_number: Optional[str] = None
    end_page: Optional[int] = None
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_path: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    publication_date: Optional[str] = None
    signing_date: Optional[str] = None
    start_page: Optional[int] = None
    title: Optional[str] = None
    disposition_notes: Optional[str] = None
    executive_order_number: Optional[int] = None
    not_received_for_publication: Optional[bool] = None
    full_text_xml_url: Optional[str] = None
    body_html_url: Optional[str] = None
    json_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutiveOrder":
        """Create an ExecutiveOrder instance from a dictionary."""
        # Convert string dates to date objects if present
        # for date_field in ['publication_date', 'signing_date']:
        #     if data.get(date_field):
        #         try:
        #             # Assuming date format is YYYY-MM-DD
        #             data[date_field] = date.fromisoformat(data[date_field])
        #         except (ValueError, TypeError):
        #             pass

        # Convert string numbers to integers if present
        for int_field in ["end_page", "start_page", "executive_order_number"]:
            if data.get(int_field) and isinstance(data[int_field], str):
                try:
                    data[int_field] = int(data[int_field])
                except (ValueError, TypeError):
                    pass

        # Initialize with the matched fields, ignoring extra fields
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
