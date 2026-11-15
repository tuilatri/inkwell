"""
Content change detection for pagination navigation.

Verifies that navigation successfully loaded new content.
"""

from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


class ContentChangeDetector:
    """Detects when page content changes after navigation."""
    
    def __init__(self, browser: WebDriver, manga_id: str):
        """
        Initialize content change detector.
        
        Args:
            browser: Selenium WebDriver instance
            manga_id: Manga identifier from URL
        """
        self.browser = browser
        self.manga_id = manga_id
    
    def get_current_chapter_count(self) -> int:
        """
        Count chapter links on current page.
        
        Returns:
            Number of chapter links found
        """
        try:
            links = self.browser.find_elements(
                By.CSS_SELECTOR,
                f"a[href*='/title/{self.manga_id}/']"
            )
            return len(links)
        except Exception:
            return 0
    
    def get_first_chapter_title(self) -> str:
        """
        Get title of first chapter link.
        
        Returns:
            First chapter title or empty string
        """
        try:
            links = self.browser.find_elements(
                By.CSS_SELECTOR,
                f"a[href*='/title/{self.manga_id}/']"
            )
            
            if links:
                return links[0].text.strip()
            
            return ""
        except Exception:
            return ""
    
    def wait_for_staleness(self, element: WebElement, timeout: int = 10) -> bool:
        """
        Wait for element to become stale (indicates page update).
        
        Args:
            element: WebElement to watch
            timeout: Maximum wait time in seconds
        
        Returns:
            True if element became stale, False if timeout
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                EC.staleness_of(element)
            )
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            return True
    
    def wait_for_content_change(self,
                                old_chapter_count: int,
                                old_first_chapter: str,
                                timeout: int = 10) -> bool:
        """
        Wait for content to change after navigation.
        
        Checks for:
        1. Chapter count change
        2. First chapter title change
        3. New elements appearing
        
        Args:
            old_chapter_count: Chapter count before navigation
            old_first_chapter: First chapter title before navigation
            timeout: Maximum wait time in seconds
        
        Returns:
            True if content changed, False if timeout
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check chapter count
                new_count = self.get_current_chapter_count()
                if new_count > 0 and new_count != old_chapter_count:
                    return True
                
                # Check first chapter title
                new_first = self.get_first_chapter_title()
                if new_first and new_first != old_first_chapter:
                    return True
                
                # Wait a bit before checking again
                time.sleep(0.5)
                
            except Exception:
                # Element might be stale during transition
                time.sleep(0.5)
                continue
        
        return False
    
    def wait_for_new_elements(self, timeout: int = 10) -> bool:
        """
        Wait for new chapter elements to appear.
        
        Args:
            timeout: Maximum wait time in seconds
        
        Returns:
            True if elements appeared, False if timeout
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda d: len(d.find_elements(
                    By.CSS_SELECTOR,
                    f"a[href*='/title/{self.manga_id}/']"
                )) > 0
            )
            return True
        except TimeoutException:
            return False
