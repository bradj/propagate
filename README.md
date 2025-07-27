# Propagate

A tool for aggregating, downloading, and summarizing Executive Orders from the Federal Register with support for batch processing via Anthropic's API.

## Quick Start

### Prerequisites

- Python 3.7+
- Node.js & npm
- Anthropic API key

### Environment Variables

Create `.envrc` file:

```bash
export PROPAGATE_ANTHROPIC_API_KEY="your-api-key-here"
export PROPAGATE_SUMMARIES_DIR="eo/"
export PROPAGATE_PDF_DIR="eo/pdf"
export PROPAGATE_MODEL="claude-sonnet-4-20250514"
```

### Setup & Run

```bash
# Clone and setup
git clone https://github.com/username/propagate.git
cd propagate
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd web && npm install && cd ..

# Fetch and process executive orders
make run

# Build and view website
make web
```

## Summary

Propagate is a Python-based utility that enables users to:

1. Fetch Executive Orders from the Federal Register API for multiple presidents
2. Download all associated PDF documents
3. Automatically generate structured summaries using Claude AI
4. Create a searchable web interface for exploring orders
5. Support batch processing for cost-effective API usage

## Makefile Commands

### Core Commands

- `make run` - Fetch and process EOs for default president (Donald Trump)
- `make run-batch` - Create batch API request for default president
- `make build` - Build aggregated JSON and web frontend
- `make web` - Build and start development server
- `make deploy` - Deploy to Netlify

### President Selection

- `make run-president` - Interactive prompt to select president
- `make run-batch-president` - Batch process specific president
- `make run-force` - Force reprocess all orders (overwrites existing)
- `make run-force-president` - Force reprocess specific president

### Batch Management

- `make batch-list` - List all recent batches
- `make batch-status` - Check specific batch status (interactive)
- `make batch-process` - Download and process batch results (interactive)

## Advanced Usage

### Command Line Options

```bash
# Process specific president
python propagate/main.py --president joe-biden

# Process all presidents
python propagate/main.py --president all

# Force reprocess (overwrites existing summaries)
python propagate/main.py --force

# Batch mode
python propagate/main.py batch --president barack-obama

# Combine options
python propagate/main.py batch --president all --force
```

### Batch Processing Workflow

1. Create a batch request:

   ```bash
   python propagate/main.py batch --president joe-biden
   # Note the Batch ID displayed
   ```

2. Check batch status:

   ```bash
   python propagate/batch_manager.py status <batch_id>
   ```

3. Process completed batch:
   ```bash
   python propagate/batch_manager.py process <batch_id>
   ```

### Available Presidents

- `donald-trump` (default)
- `joe-biden`
- `barack-obama`
- `george-w-bush`
- `all` (process all presidents)

## Project Structure

### Core Python Modules

- `main.py` - Fetches orders and manages processing workflow
- `models.py` - Data models for Executive Orders and Summaries
- `summarize_eo.py` - AI summarization with Claude API
- `build.py` - Aggregates summaries into final JSON
- `batch_manager.py` - Manages batch API requests
- `federalregister.py` - Federal Register API integration
- `util.py` - Shared utilities and helper functions

### Data Structure

- `eo/pdf/` - Downloaded PDF files
- `eo/*.json` - Individual order summaries
- `eo/eo.json` - Aggregated data for web frontend
- `request_ids_*.txt` - Batch request tracking
- `batch_results/` - Downloaded batch results

### Web Frontend

- `web/src/` - TypeScript source code
- `web/public/` - Static assets
- `web/dist/` - Built frontend

## Features

- **Multi-President Support**: Process orders from multiple presidents
- **Incremental Processing**: Skip already-processed orders automatically
- **Batch API Support**: Cost-effective processing of large order sets
- **Force Reprocessing**: Update existing summaries with new AI models
- **Structured Categorization**: AI categorizes orders across multiple dimensions
- **Fuzzy Search**: Real-time search across all order fields
- **Responsive Web UI**: Mobile-friendly interface for exploring orders

## Development

### Adding New Presidents

Edit `propagate/models.py` and add to the `PRESIDENTS` list:

```python
President(name="New President", key="new-president")
```

### Customizing AI Prompts

Edit `propagate/prompts.py` to modify how Claude analyzes executive orders.

### Frontend Development

```bash
cd web
npm run dev  # Development server with hot reload
npm run build  # Production build
```
