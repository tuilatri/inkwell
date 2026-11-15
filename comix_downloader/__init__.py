"""
Comix.to Downloader
Download manga chapters from comix.to
"""

from .comix_scraper import (
    search_manga,
    get_manga_info,
    download_chapter,
    extract_manga_id,
    sanitize_filename,
    convert_chapter_to_pdf,
    convert_chapter_to_cbz,
    get_browser_pool,
)

__version__ = "1.0.0"
__all__ = [
    "search_manga",
    "get_manga_info",
    "download_chapter",
    "extract_manga_id",
    "sanitize_filename",
    "convert_chapter_to_pdf",
    "convert_chapter_to_cbz",
    "get_browser_pool",
]
