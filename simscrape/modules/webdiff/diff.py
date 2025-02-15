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
import difflib
from typing import Dict, List, Tuple
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

async def check_folder_differences(diff_dir: Path) -> Dict[str, List[Tuple[str, str, List[str]]]]:
    """
    Check each subfolder in diff directory for file differences.
    
    Returns:
        Dict mapping folder names to list of (file1, file2, diff_lines) tuples
    """
    changes = {}

    # Scan all subfolders in diff directory
    for folder in diff_dir.iterdir():
        if not folder.is_dir():
            continue

        # Get all markdown files in folder, sorted by timestamp
        md_files = sorted([f for f in folder.glob("*.md")])
        if len(md_files) < 2:
            continue

        folder_changes = []
        # Compare each file with the next one chronologically
        for i in range(len(md_files) - 1):
            file1, file2 = md_files[i], md_files[i + 1]

            # Read file contents
            content1 = file1.read_text().splitlines()
            content2 = file2.read_text().splitlines()

            # Generate diff
            diff = list(difflib.unified_diff(
                content1, content2,
                fromfile=file1.name,
                tofile=file2.name,
                lineterm=''
            ))

            if diff:  # Only store if there are differences
                folder_changes.append((file1.name, file2.name, diff))

        if folder_changes:
            changes[folder.name] = folder_changes

    return changes

async def save_diff_report(changes: Dict[str, List[Tuple[str, str, List[str]]]], base_dir: Path, timestamp: str):
    """
    Save differences report in markdown format.
    """
    report_dir = base_dir / "reports"
    report_dir.mkdir(exist_ok=True)

    report_content = ["# Content Change Report\n"]
    report_content.append(f"Generated: {timestamp}\n")

    for folder, folder_changes in changes.items():
        report_content.append(f"\n## {folder}\n")

        for old_file, new_file, diff in folder_changes:
            report_content.append(f"\n### Changes: {old_file} → {new_file}\n")
            report_content.append("```diff")
            report_content.extend(diff)
            report_content.append("```\n")

    report_file = report_dir / f"diff_report_{timestamp}.md"
    report_file.write_text("\n".join(report_content))
    print(f"✓ Diff report saved to: {report_file}")

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

        # First check for differences in existing files
        if diff_dir.exists():
            print("\nChecking for changes in existing files...")
            changes = await check_folder_differences(diff_dir)
            if changes:
                await save_diff_report(changes, base_output_dir, timestamp)
            else:
                print("No changes detected")

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
