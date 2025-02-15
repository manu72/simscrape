"""
Builds on the base crawler and filename generator.
Crawl single URLs and save trimmed content to markdown file(s) suitable for an AI Agent to read.
Compare two md files from same URL to detect changes.
Generate change summary and email report for admin.
"""

import asyncio
from pathlib import Path
from datetime import datetime
import sys
from simscrape.common.crawler import AsyncWebCrawler
from simscrape.common.filename import generate_filename

# variable for configuration
URLS_TO_CRAWL = [
   # "https://immi.homeaffairs.gov.au/what-we-do/whm-program/latest-news",
   # "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing",
    "https://www.abc.net.au/news",
    "https://www.abc.net.au/news/world",
   # "https://www.abc.net.au/news/politics",
   # "https://www.abc.net.au/news/business",
   # "https://www.abc.net.au/news/technology",
   # "https://www.abc.net.au/news/science",
   # "https://www.abc.net.au/news/health",
   # "https://www.abc.net.au/news/entertainment",
   # "https://www.abc.net.au/news/indigenous",
   # "https://www.abc.net.au/news/environment",
   # "https://www.abc.net.au/news/justin",
    # Add more URLs as needed
]
OUTPUT_FILE_PREFIX = "abc"  # variable for prefix for files

async def main():
    """Execute the main crawling process. Returns: int: 0 for success, 1 for failure"""
    try:
        # Create main output directory and its subdirectories
        base_output_dir = Path("output")
        base_output_dir.mkdir(exist_ok=True)

        # Create subdirectory using OUTPUT_FILE_PREFIX
        output_dir = base_output_dir / OUTPUT_FILE_PREFIX
        output_dir.mkdir(exist_ok=True)

        # Create diff directory
        diff_dir = base_output_dir / "diff"
        diff_dir.mkdir(exist_ok=True)

        # Generate timestamp for this batch
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        async with AsyncWebCrawler() as crawler:
            for index, url in enumerate(URLS_TO_CRAWL, start=1):
                try:
                    print(f"\nProcessing {index}/{len(URLS_TO_CRAWL)}: {url}")
                    result = await crawler.arun(url=url)

                    if result.markdown:
                        # Clean up the markdown before saving
                        cleaned_markdown = result.clean_markdown()

                        # Original file saving logic
                        filename = generate_filename(url, index, timestamp, OUTPUT_FILE_PREFIX)
                        output_file = output_dir / filename

                        # Write the cleaned markdown content to file
                        output_file.write_text(cleaned_markdown)
                        print(f"✓ Successfully saved to: {output_file}")

                        # New diff directory logic
                        diff_filename = generate_filename(url, index, "", OUTPUT_FILE_PREFIX).replace("__", "_")
                        diff_subdir = diff_dir / diff_filename
                        diff_subdir.mkdir(exist_ok=True)

                        diff_file = diff_subdir / f"{timestamp}.md"
                        diff_file.write_text(cleaned_markdown)
                        print(f"✓ Diff version saved to: {diff_file}")
                    else:
                        print("✗ Failed: No content retrieved")

                except asyncio.TimeoutError as e:
                    print(f"✗ Timeout error crawling {url}: {str(e)}")
                except IOError as e:
                    print(f"✗ File operation error for {url}: {str(e)}")
                except Exception as e:  # pylint: disable=broad-except
                    # Keep the broad exception as a fallback, but with a pylint disable comment
                    print(f"✗ Error crawling {url}: {str(e)}")

    except PermissionError as e:
        print(f"✗ Permission error creating directories: {str(e)}")
        return 1
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
