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
from simscrape.modules.newsagent.processor import call_chatgpt

# variable for configuration
URLS_TO_CRAWL = [
   # "https://immi.homeaffairs.gov.au/what-we-do/whm-program/latest-news",
   # "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing",
    "https://www.abc.net.au/news",
    "https://www.abc.net.au/news/world",
   # "https://www.abc.net.au/news/politics",
   # "https://www.abc.net.au/news/2025-02-15/elon-musks-doge-agency-explained/104929704",
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

async def check_folder_differences(
    diff_dir: Path
) -> Dict[str, List[Tuple[str, str, List[str], List[str], List[str]]]]:
    """
    Check each subfolder in diff directory for file differences.
    Returns: Dict mapping folder names to list of (file1, file2, 
    diff_lines, content1, content2) tuples
    """
    changes = {}

    # Scan all subfolders in diff directory
    for folder in diff_dir.iterdir():
        if not folder.is_dir():
            continue

        try:
            md_files = sorted([f for f in folder.glob("*.md")]) # sort by timestamp
            if len(md_files) < 2:
                continue

            folder_changes = []
            for i in range(len(md_files) - 1):
                file1, file2 = md_files[i], md_files[i + 1]

                try:
                    content1 = file1.read_text().splitlines()
                    content2 = file2.read_text().splitlines()
                except IOError as e:
                    print(f"Error reading files in {folder.name}: {str(e)}")
                    continue

                diff = list(difflib.unified_diff(
                    content1, content2,
                    fromfile=file1.name,
                    tofile=file2.name,
                    lineterm=''
                ))

                if diff:
                    folder_changes.append((file1.name, file2.name, diff, content1, content2))

            if folder_changes:
                changes[folder.name] = folder_changes

        except Exception as e:  # pylint: disable=broad-except
            print(f"Error processing folder {folder.name}: {str(e)}")
            continue

    return changes

async def save_diff_reports(
    changes: Dict[str, List[Tuple[str, str, List[str], List[str], List[str]]]],
    base_dir: Path,
    timestamp: str
):
    """Save differences reports and get AI analysis"""
    report_dir = base_dir / "reports"
    report_dir.mkdir(exist_ok=True)

    # Generate markdown report content
    report_content = ["# Content Change Report\n"]
    report_content.append(f"Generated: {timestamp}\n")

    for folder, folder_changes in changes.items():
        # Map folder name back to original URL
        original_url = next((url for url in URLS_TO_CRAWL 
                           if folder in generate_filename(url, 1, "", OUTPUT_FILE_PREFIX)), folder)
        
        report_content.append(f"\n## {original_url}\n")
        for old_file, new_file, diff, content1, content2 in folder_changes:
            report_content.append(f"\n### Changes: {old_file} → {new_file}\n")
            report_content.append("```diff")
            report_content.extend(diff)
            report_content.append("```\n")

    # Save markdown report
    report_text = "\n".join(report_content)
    md_file = report_dir / f"diff_report_{timestamp}.md"
    md_file.write_text(report_text)
    print(f"✓ Markdown diff report saved to: {md_file}")

    # Get AI analysis of the changes
    try:
        prompt = (
            "You are an expert at analyzing website content changes. "
            "For each URL below, analyze the differences between the two versions "
            "and provide a clear summary of what changed.\n\n"
            "For each change:\n"
            "1. Start with the URL being monitored\n"
            "2. Show the comparison timestamps (from → to)\n"
            "3. Summarize what content was added, removed, or modified\n"
            "4. Highlight any significant changes in meaning or context\n\n"
            "Format your response in markdown with appropriate headers and bullet points.\n\n"
            f"{report_text}"
        )
        
        ai_summary = call_chatgpt(prompt)
        
        # Save AI summary with metadata header
        summary_content = [
            "# Website Content Change Analysis\n",
            f"Analysis Generated: {timestamp}\n",
            ai_summary
        ]
        
        summary_file = report_dir / f"diff_analysis_{timestamp}.md"
        summary_file.write_text("\n".join(summary_content))
        print(f"✓ AI analysis saved to: {summary_file}")
        
    except Exception as e:
        print(f"Error getting AI analysis: {str(e)}")

    # Save HTML report as before...
    html_content = ["<html><head><title>Content Change Report</title></head>"]
    html_content.append("<body>")
    html_content.append("<h1>Content Change Report</h1>")
    html_content.append(f"<p>Generated: {timestamp}</p>")

    differ = difflib.HtmlDiff()

    for folder, folder_changes in changes.items():
        html_content.append(f"<h2>{folder}</h2>")

        for old_file, new_file, diff, content1, content2 in folder_changes:
            # HTML diff
            html_content.append(f"<h3>Changes: {old_file} → {new_file}</h3>")
            try:
                html_table = differ.make_table(
                    content1, content2,
                    fromdesc=old_file,
                    todesc=new_file,
                    context=True
                )
                html_content.append(html_table)
            except Exception as e:  # pylint: disable=broad-except
                html_content.append(f"<p>Error generating HTML diff: {str(e)}</p>")

    html_content.append("</body></html>")

    try:
        # Save HTML report
        html_file = report_dir / f"diff_report_{timestamp}.html"
        html_file.write_text("\n".join(html_content))
        print(f"✓ HTML diff report saved to: {html_file}")
    except IOError as e:
        print(f"Error saving reports: {str(e)}")

async def main():
    """Execute the main crawling process. Returns: int: 0 for success, 1 for failure"""
    try:
        # Create main output directory and its subdirectories
        base_output_dir = Path("output")
        base_output_dir.mkdir(exist_ok=True)

        output_dir = base_output_dir / OUTPUT_FILE_PREFIX
        output_dir.mkdir(exist_ok=True)

        diff_dir = base_output_dir / "diff"
        diff_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # First crawl all URLs and save content
        async with AsyncWebCrawler() as crawler:
            for index, url in enumerate(URLS_TO_CRAWL, start=1):
                try:
                    print(f"\nProcessing {index}/{len(URLS_TO_CRAWL)}: {url}")
                    result = await crawler.arun(url=url)

                    if result.markdown:
                        cleaned_markdown = result.clean_markdown()

                        # Save to regular output directory
                        filename = generate_filename(url, index, timestamp, OUTPUT_FILE_PREFIX)
                        output_file = output_dir / filename
                        output_file.write_text(cleaned_markdown)
                        print(f"✓ Successfully saved to: {output_file}")

                        # Save to diff directory
                        diff_filename = generate_filename(url, index, "", OUTPUT_FILE_PREFIX)
                        # Remove index number and .md extension
                        diff_foldername = '_'.join(diff_filename.split('_')[:-2])
                        diff_subdir = diff_dir / diff_foldername
                        diff_subdir.mkdir(exist_ok=True)

                        diff_file = diff_subdir / f"{timestamp}.md"
                        diff_file.write_text(cleaned_markdown)
                        print(f"✓ Diff version saved to: {diff_file}")

                        # Now check for differences with previous version
                        print("\nChecking for changes...")
                        changes = await check_folder_differences(diff_dir)
                        if changes:
                            await save_diff_reports(changes, base_output_dir, timestamp)
                        else:
                            print("No changes detected")
                    else:
                        print("✗ Failed: No content retrieved")

                except asyncio.TimeoutError as e:
                    print(f"✗ Timeout error crawling {url}: {str(e)}")
                except IOError as e:
                    print(f"✗ File operation error for {url}: {str(e)}")
                except Exception as e:  # pylint: disable=broad-except
                    print(f"✗ Error crawling {url}: {str(e)}")

        return 0

    except PermissionError as e:
        print(f"✗ Permission error creating directories: {str(e)}")
        return 1
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
