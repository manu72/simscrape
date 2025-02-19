# simscrape

A flexible and efficient web scraping and content analysis toolkit. Built with Python using modern async/await patterns for optimal performance, it provides various modules for web crawling, content comparison, and document analysis.

## Features

- **Base Crawler**: Asynchronous web crawling with configurable parameters
- **Web Difference Detection**: Compare and track changes between web pages over time
- **PDF Vector Analysis**: Process and analyze PDF documents using vector embeddings
- **News Agent**: Intelligent news aggregation and processing
- **Common Utilities**: Shared tools for HTML processing, file management, and error handling
- **Modern Architecture**: Built with async/await patterns for optimal performance
- **Configurable**: Extensive configuration options via environment variables and config files
- **Error Resilient**: Comprehensive error handling and recovery mechanisms

## Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- Git

## Installation

1. Clone the repository:

```bash
git clone https://github.com/manu72/simscrape.git
cd simscrape
```

2. Create and activate virtual environment:

```bash
python -m venv env
source env/bin/activate  # On Windows use: env\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Project Structure

simscrape/
├── api/ # API interfaces
├── common/ # Shared utilities
├── modules/
│ ├── basecrawler/ # Core crawling functionality
│ ├── webdiff/ # Web difference detection
│ ├── pdfvector/ # PDF processing and analysis
│ └── newsagent/ # News processing features
├── config.py # Configuration management
└── main.py # Application entry point

input/ # Input files and configurations
output/ # Generated output files
tests/ # Test suite

## Dependencies

Key dependencies include:

- aiohttp: Async HTTP client/server
- beautifulsoup4: HTML parsing
- pydantic: Data validation
- python-dotenv: Environment management
- openai: AI integration
- sentence-transformers: Text embeddings
- faiss-cpu: Vector similarity search
- langchain: Language model tools
- PyMuPDF: PDF processing

## Usage

### Basic Crawling

```python
from simscrape.modules.basecrawler import crawler
import asyncio

async def main():
    urls = ["https://example.com"]
    results = await crawler.crawl(urls)

asyncio.run(main())
```

### Web Difference Detection

```python
from simscrape.modules.webdiff import diff
import asyncio

async def main():
    url = "https://example.com"
    changes = await diff.compare_versions(url)

asyncio.run(main())
```

### PDF Vector Analysis

```python
from simscrape.modules.pdfvector import analyzer

results = analyzer.process_pdf("document.pdf")
```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and adjust the values:

```env
API_KEY=your_api_key
BASE_URL=https://api.example.com
OUTPUT_DIR=./output
...
```

## Error Handling

The application implements comprehensive error handling for:

- Network timeouts and connection issues
- File system operations
- API rate limits and quotas
- Data processing errors
- Resource management

Errors are logged with context for debugging and monitoring.

## Development

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

For major changes, please open an issue first to discuss the proposed changes.

## Testing [not yet implemented]

Run the test suite:

```bash
python -m pytest tests/
```
