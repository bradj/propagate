from pathlib import Path


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

    def __init__(self, title: str, summary: str, purpose: str, effective_date: str, expiration_date: str, economic_effects: str, geopolitical_effects: str, deeper_dive: str, pdf_path: Path, publication_date: str, signing_date: str, original_url: str, eo_number: int):
        self.title = title
        self.summary = summary
        self.purpose = purpose
        self.effective_date = effective_date
        self.expiration_date = expiration_date
        self.economic_effects = economic_effects
        self.geopolitical_effects = geopolitical_effects
        self.deeper_dive = deeper_dive
        self.pdf_path = pdf_path
        self.publication_date = publication_date
        self.signing_date = signing_date
        self.original_url = original_url
        self.eo_number = eo_number
