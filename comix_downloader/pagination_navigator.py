"""
Pagination navigation strategies for comix.to website.

Tries multiple navigation methods until one succeeds.
"""

from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
import time


class PaginationNavigator:
    """Handles pagination navigation with multiple fallback strategies."""
    
    def __init__(self, browser: WebDriver, detector):
        """
        Initialize pagination navigator.
        
        Args:
            browser: Selenium WebDriver instance
            detector: PaginationDetector instance
        """
        self.browser = browser
        self.detector = detector
        self.successful_method = None
    
    def navigate_to_next_page(self) -> bool:
        """
        Navigate to next page using best available method.
        
        Tries methods in priority order:
        1. Cached successful method (if available)
        2. Click the page-number button for the next page (deterministic)
        3. Click the Next button
        4. JavaScript event trigger

        The pager is `<nav class="npager">` holding `<button>` elements with no
        href. Strategies that drove a page-number text input, or followed an
        href, were structurally impossible here and have been removed rather
        than left failing quietly - that is how the chapter list came to be
        truncated at one page while reporting success.

        Returns:
            True if navigation successful, False otherwise
        """
        # Try cached method first
        if self.successful_method:
            print(f"Using cached method: {self.successful_method}")
            method = getattr(self, self.successful_method, None)
            if method and method():
                return True
        
        # Try methods in priority order
        methods = [
            ('try_click_page_number', self.try_click_page_number),
            ('try_next_button_click', self.try_next_button_click),
            ('try_javascript_event_trigger', self.try_javascript_event_trigger),
        ]
        
        for method_name, method in methods:
            print(f"Trying navigation method: {method_name}")
            
            if method():
                print(f"Success with method: {method_name}")
                self.successful_method = method_name
                return True
        
        return False
    
    def try_click_page_number(self, page_num: Optional[int] = None) -> bool:
        """
        Click a numbered page button, by default the one after the current page.

        Deterministic, and preferred over the Next control because the pager
        renders a sliding window: page 9 may not be on screen while page 8 is
        active, in which case Next is the only way forward.

        Args:
            page_num: Target page number (None = next page)

        Returns:
            True if a matching button was clicked and took effect
        """
        try:
            if page_num is None:
                page_num = self.detector.get_current_page() + 1

            target = str(page_num)
            for button in self.detector.find_navigation_elements().get(
                    'page_links', []):
                if (button.text or '').strip() == target:
                    self.browser.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    return self.detector.get_current_page() == page_num

            print(f"Page {target} is not in the current pager window")
            return False

        except Exception as e:
            print(f"Page number click failed: {e}")
            return False
    
    def try_next_button_click(self) -> bool:
        """
        Try clicking Next button with JavaScript executor.
        
        Returns:
            True if click executed, False otherwise
        """
        try:
            elements = self.detector.find_navigation_elements()
            next_btn = elements.get('next_button')
            
            if not next_btn:
                return False
            
            # Check if enabled
            if not self.detector.is_next_enabled():
                return False
            
            # Click with JavaScript executor
            self.browser.execute_script("arguments[0].click();", next_btn)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"Next button click failed: {e}")
            return False
    
    def try_javascript_event_trigger(self) -> bool:
        """
        Try triggering click event via JavaScript.
        
        Returns:
            True if event triggered, False otherwise
        """
        try:
            elements = self.detector.find_navigation_elements()
            next_btn = elements.get('next_button')
            
            if not next_btn:
                return False
            
            # Trigger MouseEvent
            self.browser.execute_script("""
                var event = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                arguments[0].dispatchEvent(event);
            """, next_btn)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"JavaScript event trigger failed: {e}")
            return False
    
def navigate_to_page(self, page_num: int) -> bool:
        """
        Navigate to specific page number.
        
        Args:
            page_num: Target page number
            
        Returns:
            True if navigation executed, False otherwise
        """
        return self.try_click_page_number(page_num)
