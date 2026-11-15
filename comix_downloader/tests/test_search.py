"""
Test search functionality for comix.to downloader
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from comix_scraper import search_manga


def test_search_basic():
    """Test basic search functionality"""
    print("Testing search for 'smoking'...")
    results = search_manga("smoking", max_results=5)
    
    assert len(results) > 0, "No results found"
    print(f"Found {len(results)} results")
    
    for result in results:
        assert 'title' in result
        assert 'url' in result
        assert 'id' in result
        print(f"  - {result['title']}")
        print(f"    URL: {result['url']}")
        print(f"    ID: {result['id']}")
    
    print("Search test passed!")


if __name__ == "__main__":
    test_search_basic()
