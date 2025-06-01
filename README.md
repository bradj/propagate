# Propagate

A tool for aggregating, downloading, and summarizing Executive Orders from the Federal Register.

## Summary

Propagate is a Python-based utility that enables users to:

1. Fetch Executive Orders from the Federal Register API
2. Download all associated PDF documents
3. Automatically generate concise summaries of each order using Claude AI
4. Store both PDFs and summaries for easy access

The project handles pagination, duplicate downloads, and provides simple status updates as it processes Executive Orders.

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

4. Get PDF's and process them

   ```bash
   make run
   ```

5. Build & Run Website

   ```bash
   make web
   ```

### Usage

#### Example `.envrc`

```
export PROPAGATE_ANTHROPIC_API_KEY="[your key here]"
export PROPAGATE_SUMMARIES_DIR="eo/"
export PROPAGATE_PDF_DIR="eo/pdf"
export PROPAGATE_MODEL="claude-3-7-sonnet-20250219"
```

## Project Structure

- `main.py`: Handles API requests to the Federal Register and PDF downloads
- `models.py`: Data models for Executive Orders and AI-generated summaries
- `summarize_eo.py`: Processes PDFs with Claude AI to generate summaries
- `eo/pdf/`: Directory containing downloaded Executive Order PDFs
- `eo/`: Directory containing JSON summaries of Executive Orders
- `web/`: TypeScript web frontend with search functionality powered by fuse.js
