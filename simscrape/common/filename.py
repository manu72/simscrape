"""
Filename generation utilities
"""
from urllib.parse import urlparse
from typing import Optional

def sanitize_filename(text: str) -> str:
    """Convert text to a valid filename."""
    # Remove or replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    filename = ''.join(c if c not in invalid_chars else '_' for c in text)
    # Limit length and remove trailing spaces/dots
    return filename[:50].strip('. ')

def get_domain_prefix(url: str, default_prefix: str) -> str:
    """Extract domain prefix from URL."""
    try:
        parsed = urlparse(url)
        # Get domain parts and remove common prefixes
        domain_parts = parsed.netloc.split('.')
        if domain_parts[0] in ['www', 'docs', 'api']:
            domain_parts = domain_parts[1:]
        return domain_parts[0] if domain_parts else default_prefix
    except Exception:
        return default_prefix

def get_path_suffix(url: str) -> Optional[str]:
    """Extract meaningful suffix from URL path."""
    try:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        return path_parts[-1] if path_parts else None
    except Exception:
        return None

def generate_filename(url: str, index: int, timestamp: str, default_prefix: str) -> str:
    """Generate a safe filename from URL components."""
    try:
        # Get domain prefix (e.g., 'crawl4ai' from 'docs.crawl4ai.com')
        prefix = get_domain_prefix(url, default_prefix)
        
        # Get path suffix if available
        suffix = get_path_suffix(url)
        
        # Combine prefix with suffix if available
        if suffix:
            file_prefix = f"{prefix}_{sanitize_filename(suffix)}"
        else:
            file_prefix = prefix
            
        # Sanitize the complete prefix
        file_prefix = sanitize_filename(file_prefix)
        if not file_prefix:  # If sanitization results in empty string
            file_prefix = default_prefix
            
    except Exception as e:
        print(f"Warning: Using default prefix due to error: {str(e)}")
        file_prefix = default_prefix
        
    return f"{file_prefix}_{index}_{timestamp}.md" 