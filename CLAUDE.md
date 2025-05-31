# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

Propagate is a Python-based tool with a TypeScript web frontend that fetches, downloads, and summarizes Executive Orders from the Federal Register. The system consists of:

- **Python backend** (`propagate/`): Core data processing and AI summarization
- **TypeScript web frontend** (`web/`): VanillaJS UI for viewing Executive Order data
- **Data pipeline**: Federal Register API → PDF downloads → Claude AI summarization → JSON aggregation

### Core Components

- `federal_register.py`: Fetches Executive Orders from Federal Register API and downloads PDFs
- `summarize_eo.py`: Processes PDFs with Claude AI to generate structured summaries with categorization
- `build.py`: Aggregates individual JSON summaries into a single `eo.json` file with date processing
- `executive_order.py` & `summary.py`: Data models for Executive Orders and their AI-generated summaries
- `util.py`: Shared utilities for API clients, file paths, and data conversion

### Data Flow

1. `federal_register.py` fetches EO metadata and downloads PDFs to `eo/pdf/`
2. `summarize_eo.py` processes PDFs with Claude AI, generating JSON summaries in `eo/`
3. `build.py` aggregates summaries into `eo/eo.json` with proper date formatting
4. Web build copies `eo.json` to `web/public/` for frontend consumption

## Common Commands

### Build Process
```bash
make build                    # Full build: aggregate JSON + build web frontend
python propagate/build.py     # Aggregate summaries into eo.json
cd web && npm run build       # Build TypeScript frontend
```

### Data Processing
```bash
python propagate/federal_register.py   # Fetch EOs and download PDFs
python propagate/summarize_eo.py        # Generate AI summaries for PDFs
```

### Web Development
```bash
cd web && npm run dev         # Start development server
cd web && npm run preview     # Preview built site
```

## Environment Configuration

Required environment variables (typically in `.envrc`):
- `PROPAGATE_ANTHROPIC_API_KEY`: Claude AI API key
- `PROPAGATE_SUMMARIES_DIR`: Directory for JSON summaries (e.g., "eo/")
- `PROPAGATE_PDF_DIR`: Directory for PDF downloads (e.g., "eo/pdf")
- `PROPAGATE_MODEL`: Claude model to use (e.g., "claude-3-7-sonnet-20250219")

## Key Implementation Details

- **Date Handling**: `build.py` converts string dates to datetime objects and handles edge cases like "12:01" effective dates and various expiration date formats
- **Categorization**: AI summaries include structured categorization across policy domains, regulatory impact, constitutional authority, duration, scope, and political context
- **PDF Processing**: Uses base64 encoding to send PDFs to Claude API for analysis
- **Incremental Updates**: System skips already-downloaded PDFs and existing summaries to enable cost-effective incremental processing
- **Duplicate Prevention**: `summarize_eo.py` checks for existing summary files before processing to avoid reprocessing and unnecessary API costs