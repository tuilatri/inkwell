"""
Pagination detection for comix.to website.

Detects and analyzes pagination elements on manga pages.
"""

from typing import Optional, Dict, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import re


class PaginationDetector:
    """Detects and analyzes pagination structure on manga pages.

    The pager was a Bootstrap-style `<div class="pagination justify-content-center">`
    with an "x of y" text input (`.go-page`). It is now a
    `<nav class="npager" aria-label="Pagination">` of `<button>` elements with no
    href and no total-page text anywhere.

    Two consequences worth remembering:

      * Nothing here may return a value the caller cannot distinguish from
        "genuinely one page". The old implementation returned 1 when `.go-page`
        was absent, which made the collector report success after the first
        page and silently truncate the chapter list.
      * No total is published, so the total has to be discovered by walking.
    """
    
    # The pager, plus a structural fallback so a rename does not disable it
    # the same way the class rename did.
    _CONTAINER_SELECTORS = (
        "nav.npager",
        "[aria-label='Pagination']",
        "nav:has(.npager__nav)",
    )
    
    def __init__(self, browser: WebDriver, manga_id: str):
        """
        Initialize pagination detector.
        
        Args:
            browser: Selenium WebDriver instance
            manga_id: Manga identifier from URL
        """
        self.browser = browser
        self.manga_id = manga_id
    
    def detect_pagination_container(self) -> Optional[WebElement]:
        """
        Find pagination container element.
        
        Returns:
            Pagination container WebElement or None if not found
        """
        for selector in self._CONTAINER_SELECTORS:
            try:
                return self.browser.find_element(By.CSS_SELECTOR, selector)
            except Exception:
                continue
        return None
    
    def get_current_page(self) -> int:
        """
        Get current page number from the pager.
        
        Returns:
            Current page number, defaults to 1 if not found
        """
        try:
            active = self.browser.find_element(
                By.CSS_SELECTOR, ".npager__num.is-active, .npager__num[aria-current='page']"
            )
            text = (active.text or "").strip()
            if text.isdigit():
                return int(text)
        except Exception:
            pass
        return 1
    
    def get_total_pages(self) -> int:
        """
        The pager publishes no total, so this reports the size of the visible
        page-number window and must not be read as the total.

        `detect_pagination_container()` returning a container is the only
        reliable signal that more than one page exists. Callers that need the
        real total must walk and watch `get_current_page()`.
        """
        try:
            container = self.detect_pagination_container()
            if container is None:
                return 1
            return len(container.find_elements(By.CSS_SELECTOR, ".npager__num")) or 1
        except Exception:
            return 1
    
    def has_page_after(self, current_page: int) -> bool:
        """True if any page number greater than `current_page` is on screen.

        This, not `is_next_enabled()`, is the honest end-of-list signal. The
        pager drops the Next control several pages before the real end - pages
        10 through 13 of a 13-page series rendered no Next at all, yet pages
        11-13 were still reachable by their number buttons. Breaking on the
        missing Next control is what truncated this series at Ch.22 and
        reported success.
        """
        try:
            container = self.detect_pagination_container()
            if container is None:
                return False
            for button in container.find_elements(By.CSS_SELECTOR, ".npager__num"):
                text = (button.text or "").strip()
                if text.isdigit() and int(text) > current_page:
                    return True
            return False
        except Exception:
            return False

    def find_navigation_elements(self) -> Dict[str, Optional[WebElement]]:
        """
        Find all navigation elements in pagination.
        
        Returns:
            Dictionary with navigation elements:
            - prev_button: Previous button element
            - next_button: Next button element
            - page_input: Page number input field
            - page_links: List of page number links
        """
        elements = {
            'prev_button': None,
            'next_button': None,
            'last_button': None,
            'page_input': None,
            'page_links': []
        }
        
        try:
            if self.detect_pagination_container() is None:
                return elements
            
            # The pager is buttons, not anchors, and carries no href.
            for button in self.browser.find_elements(
                    By.CSS_SELECTOR, ".npager__num"):
                text = (button.text or "").strip()
                if text.isdigit():
                    elements['page_links'].append(button)
            
            for button in self.browser.find_elements(
                    By.CSS_SELECTOR, ".npager__nav"):
                label = (button.get_attribute('aria-label') or "").lower()
                if 'next' in label:
                    elements['next_button'] = button
                elif 'last' in label:
                    elements['last_button'] = button
                elif 'prev' in label or 'first' in label:
                    elements['prev_button'] = button
            
            return elements
            
        except Exception:
            return elements
    
    def is_next_enabled(self) -> bool:
        """
        Check if Next button is enabled.
        
        Returns:
            True if Next button is enabled, False otherwise
        """
        try:
            elements = self.find_navigation_elements()
            next_btn = elements.get('next_button')
            
            if not next_btn:
                return False
            
            if next_btn.get_attribute('disabled') is not None:
                return False
            
            classes = (next_btn.get_attribute('class') or '').lower()
            if 'disabled' in classes or 'is-disabled' in classes:
                return False
            
            # The pager usually drops the control entirely on the last page
            ancestor_classes = ''
            try:
                parent = next_btn.find_element(By.XPATH, "..")
                ancestor_classes = (parent.get_attribute('class') or '').lower()
            except Exception:
                pass
            return 'disabled' not in ancestor_classes
            
        except Exception:
            return False
    
    def get_pagination_info(self) -> Dict[str, any]:
        """
        Get comprehensive pagination information.
        
        Returns:
            Dictionary with all pagination details
        """
        return {
            'current_page': self.get_current_page(),
            'total_pages': self.get_total_pages(),
            'has_pagination': self.detect_pagination_container() is not None,
            'next_enabled': self.is_next_enabled(),
            'elements': self.find_navigation_elements()
        }
