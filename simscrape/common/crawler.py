"""
Common crawler implementation
"""
import re
import aiohttp
# from bs4 import BeautifulSoup
from pydantic import BaseModel
from simscrape.common.markdown import DefaultMarkdownGenerator

class BrowserConfig(BaseModel):
    """Configuration for browser behavior"""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    timeout: int = 30
    verify_ssl: bool = True

class CrawlerRunConfig(BaseModel):
    """Configuration for crawler run"""
    max_retries: int = 3
    delay_between_requests: float = 1.0
    follow_links: bool = False

class CrawlResult(BaseModel):
    """Result from a crawl operation"""
    markdown: str
    html: str = ""

    def clean_markdown(self) -> str:
        """Clean up the markdown content by removing excessive whitespace"""
        cleaned = re.sub(r'\n\s*\n', '\n\n', self.markdown)
        cleaned = '\n'.join(line.strip() for line in cleaned.splitlines())
        cleaned = cleaned.strip()
        return cleaned

class AsyncWebCrawler:
    """Asynchronous web crawler with session management"""

    def __init__(self,
                 browser_config: BrowserConfig = None,
                 run_config: CrawlerRunConfig = None,
                 markdown_generator = None):
        """Initialize the crawler with configuration"""
        self.session = None
        self.browser_config = browser_config or BrowserConfig()
        self.run_config = run_config or CrawlerRunConfig()
        self.markdown_generator = markdown_generator or DefaultMarkdownGenerator()

    async def __aenter__(self):
        """Set up the aiohttp session when entering context"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.browser_config.user_agent},
                timeout=aiohttp.ClientTimeout(total=self.browser_config.timeout)
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the session when exiting context"""
        if self.session:
            await self.session.close()
            self.session = None

    async def arun(self, url: str) -> CrawlResult:
        """Run the crawler on a single URL"""
        if self.session is None:
            raise RuntimeError("Crawler must be used within an async context manager")

        try:
            async with self.session.get(url, ssl=self.browser_config.verify_ssl) as response:
                response.raise_for_status()
                html = await response.text()
                markdown = self.markdown_generator.generate_markdown(html)
                return CrawlResult(markdown=markdown, html=html)
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            return CrawlResult(markdown="", html="")
