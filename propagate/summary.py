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
    title: str
    summary: str
    purpose: str
    effective_date: str
    expiration_date: str
    economic_effects: str
    geopolitical_effects: str
    deeper_dive: str
    pdf_path: Path
    publication_date: str
    signing_date: str
    original_url: str
    eo_number: int
    positive_impacts: str
    negative_impacts: str
    key_industries: str
    categories: Categories
