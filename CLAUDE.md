# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

Propagate is a Python-based tool with a TypeScript web frontend that fetches, downloads, and summarizes Executive Orders from the Federal Register. The system consists of:

- **Python backend** (`propagate/`): Core data processing and AI summarization
- **TypeScript web frontend** (`web/`): VanillaJS UI for viewing Executive Order data
- **Data pipeline**: Federal Register API → PDF downloads → Claude AI summarization → JSON aggregation

### Core Components

- `main.py`: Fetches Executive Orders from Federal Register API and downloads PDFs; supports batch mode for processing multiple executive orders
- `summarize_eo.py`: Processes PDFs with Claude AI to generate structured summaries with categorization; can be called directly with an executive order number; supports batch API requests
- `build.py`: Aggregates individual JSON summaries into a single `eo.json` file with date processing; can also digest batch API response JSONL files
- `models.py`: Data models for Executive Orders, AI-generated summaries, and president mappings; includes Categories dataclass for structured categorization
- `prompts.py`: Contains Claude AI prompts used for generating executive order summaries
- `util.py`: Shared utilities for API clients, file paths, data conversion, and summary management
- `config.py`: Configuration management for environment variables and paths
- `federalregister.py`: Federal Register API integration for fetching executive order metadata and downloading PDFs
- `refine.py`: Post-processing tool for refining industry categorization using predefined industry lists

### Data Flow

1. `main.py` fetches EO metadata and downloads PDFs to `eo/pdf/`
2. `summarize_eo.py` processes PDFs with Claude AI, generating JSON summaries in `eo/` (supports individual requests or batch API)
3. `build.py` aggregates summaries into `eo/eo.json` with proper date formatting, or processes batch API JSONL responses
4. Web build copies `eo.json` to `web/public/` for frontend consumption

## Common Commands

### Build Process

```bash
make build                           # Full build: aggregate JSON + build web frontend
python propagate/build.py            # Aggregate summaries into eo.json
python propagate/build.py [jsonl]    # Process batch API JSONL file into eo.json
cd web && npm run build              # Build TypeScript frontend
```

### Data Processing

```bash
make run                              # Fetch EOs and download PDFs
make run-batch                        # Fetch EOs and queue batch summarization
python propagate/main.py              # Fetch EOs for default president (Donald Trump)
python propagate/main.py --president joe-biden  # Fetch EOs for specific president
python propagate/main.py --president all       # Fetch EOs for all presidents
python propagate/main.py --force      # Force reprocess default president's EOs
python propagate/main.py --president all --force  # Force reprocess all presidents' EOs
python propagate/main.py batch        # Batch mode for default president
python propagate/main.py batch --president barack-obama  # Batch mode for specific president
python propagate/main.py batch --force # Batch mode with forced reprocessing
python propagate/summarize_eo.py      # Generate AI summaries for all PDFs
python propagate/summarize_eo.py 14303 # Generate AI summary for specific EO number
python propagate/refine.py            # Refine industry categorization with predefined lists
# Batch processing also supported via Anthropic's batch API
```

### Web Development

```bash
cd web && npm run dev         # Start development server
cd web && npm run preview     # Preview built site
```

### Deployment

```bash
make deploy                   # Build and deploy to Netlify
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
- **Batch Processing**: Supports Anthropic's batch API for cost-effective processing of multiple executive orders with automatic JSONL response handling
- **Search Functionality**: Web frontend includes fuzzy search powered by fuse.js, enabling real-time filtering across titles, summaries, categories, and content fields
- **Interactive UI**: TypeScript-based frontend with responsive design, search capabilities, and structured display of executive order metadata and analysis

## Batch Processing Workflow

When using batch mode, the system creates batch requests to Claude's API for cost-effective processing:

### Creating a Batch

```bash
# Create batch for specific president
python propagate/main.py batch --president joe-biden

# Create batch for all presidents
python propagate/main.py batch --president all

# Force reprocess with batch
python propagate/main.py batch --president donald-trump --force
```

The batch ID will be prominently displayed after creation.

### Managing Batches

Use `batch_manager.py` to manage batch requests:

```bash
# List recent batches from your account
python propagate/batch_manager.py list

# Check specific batch status
python propagate/batch_manager.py status <batch_id>

# Download and process completed batch
python propagate/batch_manager.py process <batch_id>
```

### Complete Workflow Example

1. Create a batch:
   ```bash
   python propagate/main.py batch --president joe-biden
   # Note the Batch ID from output: batch_abc123
   ```

2. Check batch status:
   ```bash
   python propagate/batch_manager.py status batch_abc123
   ```

3. When status shows "ended", process the batch:
   ```bash
   python propagate/batch_manager.py process batch_abc123
   # This downloads the JSONL and automatically runs build_from_claude_batch
   ```

4. Build the final eo.json:
   ```bash
   python propagate/build.py
   ```

Batch IDs are also saved as comments in the `request_ids_[president].txt` files for reference.

## Executive Order Processing Workflow (Critical Functionality)

The application automatically processes executive orders for ALL presidents defined in `models.py` with intelligent deduplication:

1. **Multi-President Processing**: When running `python propagate/main.py`, the system:
   - Iterates through ALL presidents in the `PRESIDENTS` list (currently: Donald Trump, Joe Biden, Barack Obama, George W. Bush)
   - Fetches executive orders for each president from the Federal Register API
   - Maintains president attribution throughout the pipeline

2. **Intelligent Deduplication**: For each president's orders:
   - Checks if a summary already exists using `order.summary_exists()` 
   - Only processes orders that don't have existing summary JSON files
   - Skips entire presidents if all their orders are already processed
   - This ensures incremental updates without reprocessing or API waste

3. **Processing Modes**:
   - **Standard mode**: Processes new orders immediately via `process_pdf()`
   - **Batch mode** (`python propagate/main.py batch`): Queues new orders for batch API processing

4. **Override Functionality** (--force flag):
   - Use `python propagate/main.py --force` to reprocess ALL executive orders
   - Forces re-download of PDFs and regeneration of summaries (overwrites existing files)
   - Works with both standard and batch modes: `python propagate/main.py batch --force`
   - Useful for updating summaries with new prompts or fixing corrupted data

5. **Selective President Processing** (--president flag):
   - Default: Processes only the first president in PRESIDENTS list (Donald Trump)
   - Use `--president [key]` to process a specific president (e.g., `--president joe-biden`)
   - Use `--president all` to process all presidents (original behavior)
   - Combines with --force and batch mode for flexible processing
   - Valid president keys: donald-trump, joe-biden, barack-obama, george-w-bush

This workflow is ESSENTIAL to the application - it ensures complete coverage across all presidents while preventing duplicate processing and unnecessary API costs.