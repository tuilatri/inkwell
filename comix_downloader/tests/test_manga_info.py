"""
Test manga info extraction for comix.to downloader
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from comix_scraper import get_manga_info, extract_manga_id


def test_extract_id():
    """Test manga ID extraction"""
    url = "https://comix.to/title/y5nn-smoking-behind-the-supermarket-with-you"
    manga_id = extract_manga_id(url)
    
    assert manga_id == "y5nn-smoking-behind-the-supermarket-with-you"
    print(f"Extracted ID: {manga_id}")
    print("ID extraction test passed!")


def test_get_manga_info():
    """Test manga info retrieval"""
    url = "https://comix.to/title/y5nn-smoking-behind-the-supermarket-with-you"
    print(f"Testing manga info for: {url}")
    
    manga_title, chapters = get_manga_info(url)
    
    assert manga_title is not None, "Manga title is None"
    assert len(chapters) > 0, "No chapters found"
    
    print(f"Manga Title: {manga_title}")
    print(f"Found {len(chapters)} chapters")
    
    for i, chapter in enumerate(chapters[:3]):
        print(f"  Chapter {i+1}: {chapter['title']}")
        print(f"    URL: {chapter['url']}")
    
    print("Manga info test passed!")


if __name__ == "__main__":
    test_extract_id()
    print()
    test_get_manga_info()
