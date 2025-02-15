"""
Summarise website content using the OpenAI ChatGPT API.
"""
from pathlib import Path
from datetime import datetime
import sys
import argparse
import logging
import os
import openai
from dotenv import load_dotenv

# Set up logging for debugging and error tracking.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Add this near the top of the file, before accessing env vars

# Securely load the API key from an environment variable.
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("API key environment variable is not set.")
    sys.exit(1)

# Initialize the OpenAI client
client = openai.OpenAI(api_key=api_key)

def call_chatgpt(
    prompt: str,
    model: str = "gpt-4-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> str:
    """
    Calls the OpenAI API with the given prompt and returns the response.
    """
    if not 0 <= temperature <= 1:
        raise ValueError("Temperature must be between 0 and 1")
    if not 0 <= max_tokens <= 10000:
        raise ValueError("Max tokens must be between 0 and 10000")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=60,
        )
        result = response.choices[0].message.content.strip()
        logger.debug("API call successful.")
        return result
    except Exception as e:
        logger.error("Error calling OpenAI API: %s", e)
        raise

def summarize_text(text: str, prompt_template: str) -> str:
    """
    Inserts the text into the prompt template and returns the summarization.
    """
    prompt = prompt_template.format(text=text)
    return call_chatgpt(prompt)

def summarize_page(page_content: str) -> str:
    """
    Summarizes a single page's markdown content.
    """
    prompt_template = (
        "You are an expert news content summarizer. Summarize the following webpage content "
        "in a few concise paragraphs, highlighting the main points and structure.\n\n{text}\n"
    )
    return summarize_text(page_content, prompt_template)

def summarize_website(pages: dict) -> str:
    """
    Produces an overall website summary by combining the individual page contents.
    """
    combined_summaries = ""
    for file_name, content in pages.items():
        page_summary = summarize_page(content)
        combined_summaries += f"Summary for {file_name}:\n{page_summary}\n\n"

    website_prompt = (
        "You are an expert news website analyst. Based on the following summaries of website pages "
        "produce a well-structured markdown report. Include:\n"
        "1. An executive summary at the top\n"
        "2. Key themes and insights\n"
        "3. Individual story summaries organized by topic\n"
        "4. Notable trends or patterns\n"
        "Use proper markdown formatting with headers, bullet points, and sections.\n\n{text}"
    )
    prompt = website_prompt.format(text=combined_summaries)
    return call_chatgpt(prompt)

def create_markdown_report(page_summaries: dict, overall_summary: str, timestamp: str) -> str:
    """Creates a formatted markdown report combining all summaries."""
    report = f"""# Daily News Summary Report
Generated on: {timestamp}

## Executive Summary
{overall_summary}

## Individual Story Summaries

"""
    # Add individual summaries
    for file_name, summary in page_summaries.items():
        report += f"### {file_name}\n{summary}\n\n"

    return report

def read_markdown_files(folder: str) -> dict:
    """
    Reads all markdown (*.md) files from the provided folder and returns a dictionary
    mapping file names to their content.
    """
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise ValueError(
            f"The path {folder} is not a valid directory or contains no markdown files."
        )

    pages = {}
    for md_file in folder_path.glob("*.md"):
        try:
            with md_file.open(encoding="utf-8") as f:
                pages[md_file.name] = f.read()
            logger.info("Loaded %s", md_file.name)
        except (FileNotFoundError, IOError) as e:
            logger.error("Error reading %s: %s", md_file.name, e)
    return pages

def main():
    """
    Main function to summarise website content.
    """
    parser = argparse.ArgumentParser(
        description="Summarise website content using the OpenAI ChatGPT API."
    )
    parser.add_argument("folder", help="Folder containing markdown files of website pages.")
    args = parser.parse_args()

    try:
        pages = read_markdown_files(args.folder)
    except (ValueError, FileNotFoundError, IOError) as e:
        logger.error("Failed to read markdown files: %s", e)
        sys.exit(1)

    if not pages:
        logger.error("No markdown files found in the specified folder.")
        exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("Summarising individual pages...")
    page_summaries = {}

    for file_name, content in pages.items():
        logger.info("Processing %s...", file_name)
        try:
            summary = summarize_page(content)
            page_summaries[file_name] = summary
            print(f"\nSummary for {file_name}:\n{summary}\n{'-'*60}")
        except (openai.APIError, openai.RateLimitError, ValueError) as e:
            logger.error("Error summarising %s: %s", file_name, e)

    logger.info("Creating overall website summary...")
    try:
        overall_summary = summarize_website(pages)
        print(f"\nOverall Website Summary:\n{overall_summary}\n{'='*60}")

        # Create consolidated report
        report = create_markdown_report(page_summaries, overall_summary, timestamp)

        # Save consolidated report
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        report_filename = f"news_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = output_dir / report_filename
        report_path.write_text(report)
        logger.info("Consolidated report saved to: %s", report_path)

    except (openai.APIError, openai.RateLimitError, IOError) as e:
        logger.error("Error creating summary report: %s", e)

if __name__ == "__main__":
    main()
