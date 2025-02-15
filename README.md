# simscrape

A flexible and efficient web scraping tool for monitoring and archiving web content. Built with Python using async/await patterns for optimal performance.

## Features

- Asynchronous web crawling for efficient resource usage
- Automatic HTML to Markdown conversion
- Organized file-based storage with timestamps
- Robust error handling and recovery
- Configurable URL lists and output formats

## Installation

```bash
Clone the repository
git clone https://github.com/manu72/simscrape.git
cd simscrape
Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # On Windows use: venv\Scripts\activate
Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Crawling

The base crawler fetches content from configured URLs and saves them as markdown files:

```python
from simscrape.modules.base.base import main
import asyncio
asyncio.run(main())
```

```bash
python main.py --mode crawl --urls urls.txt
```

### Web Difference Detection

The web difference detection module compares two URLs and saves the differences as a markdown file:

```python
from simscrape.modules.webdiff.diff import main
import asyncio
asyncio.run(main())
```

### Output

Files are saved in the `output/` directory with the following structure:

output/
└── {prefix}/
└── {prefix}_{section}_{index}\_{timestamp}.md

## Project Structure

simscrape/
├── common/ # Shared utilities
│ ├── crawler.py # Core crawler implementation
│ ├── filename.py # File naming utilities
│ └── markdown.py # HTML to Markdown conversion
└── modules/
├── base/ # Basic crawling functionality
└── webdiff/ # Change detection features

## Error Handling

The crawler includes comprehensive error handling for:

- Network timeouts
- File operations
- Permission issues
- General exceptions

Each error is logged with appropriate context for debugging.

## Development

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
