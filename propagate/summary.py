from pathlib import Path
from dataclasses import dataclass


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
