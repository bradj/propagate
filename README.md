# Propagate

A tool for aggregating, downloading, and summarizing Executive Orders from the Federal Register.

## Summary

Propagate is a Python-based utility that enables users to:

1. Fetch Executive Orders from the Federal Register API
2. Download all associated PDF documents
3. Automatically generate concise summaries of each order using Claude AI
4. Store both PDFs and summaries for easy access

The project handles pagination, duplicate downloads, and provides simple status updates as it processes Executive Orders.

## Intent

This project was developed to simplify the process of collecting and understanding Executive Orders. By automating the fetching, storage, and summarization processes, Propagate reduces the time needed to track and analyze government actions. It's designed to be:

- Efficient: Only downloads new PDFs, follows pagination automatically
- Accessible: Provides brief summaries that capture the essence of lengthy documents

## Getting Started

### Prerequisites

- Python 3.7+
- An Anthropic API key for Claude

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/propagate.git
   cd propagate
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

#### Example `.envrc`

```
export PROPAGATE_ANTHROPIC_API_KEY="[your key here]"
export PROPAGATE_SUMMARIES_DIR="eo/"
export PROPAGATE_PDF_DIR="eo/pdf"
export PROPAGATE_MODEL="claude-3-7-sonnet-20250219"
```

#### Fetching and Downloading Executive Orders

To download Executive Orders from the Federal Register:

```bash
python federal_register.py
```

This will:
- Fetch all Executive Orders, following pagination
- Download PDFs to the `eo/pdf` directory
- Skip PDFs that have already been downloaded

#### Generating Summaries

To create summaries for all downloaded Executive Orders:

1. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

2. Run the summarization script:
   ```bash
   python summarize_eo.py
   ```

Summaries will be saved as JSON files in the `eo/summaries` directory.

## Project Structure

- `federal_register.py`: Handles API requests to the Federal Register and PDF downloads
- `executive_order.py`: Defines the data model for Executive Orders
- `summarize_eo.py`: Processes PDFs with Claude AI to generate summaries
- `eo/pdf/`: Directory containing downloaded Executive Order PDFs
- `eo/`: Directory containing JSON summaries of Executive Orders
- `web`: Directory containing a web view for the JSON download. Written in VanillaJS.
