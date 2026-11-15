"""
Comix.to Scraper Module
Core logic for scraping manga from comix.to using browser automation
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
from concurrent.futures import ThreadPoolExecutor
import threading
from urllib.parse import quote, urljoin
from queue import Queue

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import undetected_chromedriver as uc
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

BASE_URL = "https://comix.to"

# Backstop for the chapter-list walk. The pager never publishes a total, so the
# loop stops when the Next control runs out; this only bounds a pager that
# never disables.
MAX_PAGER_PAGES = 200

_browser_pool = None
_browser_pool_lock = threading.Lock()


def cleanup_chrome_profile():
    """
    Delete .chrome_profile directory to clean up session data.
    
    Returns:
        bool: True if cleanup successful, False otherwise
    """
    import shutil
    
    profile_dir = os.path.join(os.path.dirname(__file__), ".chrome_profile")
    
    if not os.path.exists(profile_dir):
        print("Chrome profile directory does not exist, nothing to clean up")
        return True
    
    try:
        # Close any open browsers first
        global _browser_pool
        if _browser_pool:
            print("Closing browser pool...")
            _browser_pool.cleanup()
            _browser_pool = None
        
        # Wait for processes to close
        time.sleep(2)
        
        # Remove directory
        print(f"Removing Chrome profile: {profile_dir}")
        shutil.rmtree(profile_dir, ignore_errors=True)
        print("✓ Chrome profile cleaned up successfully")
        return True
    except Exception as e:
        print(f"Error cleaning up Chrome profile: {e}")
        return False


class BrowserPool:
    """Pool of Chrome browser instances for concurrent chapter downloads."""
    
    def __init__(self, max_browsers=3):
        self.max_browsers = max_browsers
        self.available = Queue()
        self.all_browsers = []
        self.lock = threading.Lock()
    
    def _create_browser(self):
        """Create a new Chrome browser instance with anti-detection."""
        if not SELENIUM_AVAILABLE:
            raise ImportError("undetected_chromedriver not available")
        
        profile_dir = os.path.join(os.path.dirname(__file__), ".chrome_profile")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        
        options = uc.ChromeOptions()
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # No version_main: an explicit value pins undetected-chromedriver to that
        # Chrome for Testing build, and it refuses to drive the installed Chrome
        # once that is newer. Passing nothing auto-detects what is installed.
        # Verified against Chrome 155.0.8059.39 - see docs/ai-context/ARCHITECTURE.md
        browser = uc.Chrome(options=options, use_subprocess=True)
        
        try:
            from selenium_stealth import stealth
            stealth(browser,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            print("Selenium-stealth applied")
        except ImportError:
            browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    window.chrome = {
                        runtime: {}
                    };
                """
            })
        
        return browser
    
    def _is_alive(self, browser):
        """Is this driver session still usable?

        A driver round trip, not a navigation. Measured 2026-10-13 against a
        real Chrome force-killed with taskkill /F: window_handles raised
        InvalidSessionIdException in 0.00 s, so this does not trade a fast
        failure for a stall.

        One failure mode is unreachable by construction rather than untested:
        undetected-chromedriver runs with use_subprocess=True, so there is no
        separate chromedriver process to lose while Chrome carries on. The only
        way a session dies here is the browser going with it.

        Anything it raises counts as dead - a session that cannot answer a
        trivial question is not worth handing to a download that would otherwise
        fail somewhere that looks like the site refusing to load.
        """
        if browser is None:
            return False
        try:
            browser.window_handles
            return True
        except Exception:
            return False

    def _discard(self, browser):
        """Take a browser out of the pool for good and try to shut it down."""
        with self.lock:
            if browser in self.all_browsers:
                self.all_browsers.remove(browser)
        try:
            browser.quit()
        except Exception:
            pass            # already gone; nothing left to close

    def get_browser(self):
        """Get a browser from the pool, blocking if every one is on loan.

        A browser can die while it sits idle in the queue. Handing out one of
        those turns a local failure into something that reads like a scraping
        problem, so anything taken from the queue is probed first and dropped
        if it is gone - which frees the slot for a replacement.
        """
        while True:
            candidate = None
            with self.lock:
                if not self.available.empty():
                    candidate = self.available.get()
                elif len(self.all_browsers) < self.max_browsers:
                    # Created under the lock so concurrent callers cannot
                    # overshoot max_browsers. Slow, but a browser launch is
                    # slow, and racing two of them to save a lock is the wrong
                    # trade. Probed below only if it came from the queue - this
                    # one was launched a moment ago.
                    candidate = self._create_browser()
                    self.all_browsers.append(candidate)
                    return candidate
            if candidate is None:
                # Every browser is on loan. Wait for one to come back. This
                # block is unbounded by design and is what applies
                # back-pressure; see docs/ai-context/ARCHITECTURE.md section 5
                # for why a timeout here would be worse than waiting.
                return self.available.get()
            if self._is_alive(candidate):
                return candidate
            self._discard(candidate)

    def return_browser(self, browser):
        """Return browser to the pool for reuse, if it is still alive.

        Probed outside the lock: a driver call can stall, and holding the lock
        across it would block every other worker. Only the bookkeeping runs
        under the lock.
        """
        if browser is None:
            return
        alive = self._is_alive(browser)
        with self.lock:
            if browser not in self.all_browsers:
                return
            if alive:
                self.available.put(browser)
                return
        self._discard(browser)
    
    def close_all(self):
        """Close all browsers in pool."""
        with self.lock:
            for browser in self.all_browsers:
                try:
                    browser.quit()
                except Exception as e:
                    if "WinError" not in str(e):
                        print(f"Warning closing browser: {e}")
            self.all_browsers.clear()
            while not self.available.empty():
                try:
                    self.available.get_nowait()
                except:
                    break
    
    def cleanup(self):
        """Alias for close_all for consistency with cleanup_chrome_profile."""
        self.close_all()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically cleanup browsers."""
        self.cleanup()
        return False
    
    def __del__(self):
        """Destructor - automatically cleanup when object is destroyed."""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during cleanup in destructor


def get_browser_pool(max_browsers=3):
    """Get or create the global browser pool."""
    global _browser_pool
    with _browser_pool_lock:
        if _browser_pool is None:
            _browser_pool = BrowserPool(max_browsers)
        elif _browser_pool.max_browsers != max_browsers:
            _browser_pool.max_browsers = max_browsers
    return _browser_pool


def extract_manga_id(url_or_id):
    """
    Extract manga ID from comix.to URL or return ID if already provided.
    Supports URLs like: https://comix.to/title/y5nn-smoking-behind-the-supermarket-with-you
    Returns the full manga code (e.g., 'y5nn-smoking-behind-the-supermarket-with-you')
    """
    if not url_or_id:
        return None
    
    if url_or_id.startswith('http'):
        # Strip the query and fragment first. '/title/([^/]+)' stops at a
        # slash, and a query string contains none, so the suffix used to be
        # swallowed whole: '?group_id=4217' became part of the id and no
        # chapter href could match f'/title/{manga_id}/'.
        path = url_or_id.split('?', 1)[0].split('#', 1)[0]
        match = re.search(r'/title/([^/]+)', path)
        if match:
            return match.group(1)
    
    return url_or_id


def search_manga(query, max_results=50):
    """
    Search for manga on comix.to by keyword.
    Uses browser automation to handle JavaScript-loaded content.
    """
    if not SELENIUM_AVAILABLE:
        print("Warning: Browser automation not available. Comix.to requires Selenium.")
        return []
    
    browser = None
    try:
        pool = get_browser_pool(max_browsers=1)
        browser = pool.get_browser()
        
        search_url = f"{BASE_URL}/search?q={quote(query)}"
        browser.get(search_url)
        time.sleep(3)
        
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        results = []
        seen_urls = set()
        
        for item in soup.find_all('a', href=True):
            href = item.get('href', '')
            if '/title/' in href and '/read/' not in href:
                url = href if href.startswith('http') else urljoin(BASE_URL, href)
                
                if url not in seen_urls:
                    title_elem = item.find(class_='title') or item
                    title = title_elem.get_text(strip=True)
                    
                    if title and len(title) > 2:
                        title = re.sub(r'[^\x00-\x7F]+', '', title).strip()
                        if title:
                            results.append({
                                'title': title,
                                'url': url,
                                'id': extract_manga_id(url)
                            })
                            seen_urls.add(url)
                            
                            if len(results) >= max_results:
                                break
        
        pool.return_browser(browser)
        return results
        
    except Exception as e:
        print(f"Error searching manga: {e}")
        if browser:
            pool.return_browser(browser)
        return []


def group_options(chapters):
    """Distinct scanlation groups present in a chapter list.

    Returns [(label, group_id), ...] sorted by label, empty when no chapter
    carries a group. A single-group series still yields one entry; it is the
    caller's job to decide whether a filter with one option is worth showing.

    Matched and reported by href, never by display text: the site writes
    "OmegaScans" in the chapter row and lowercase "omegascans" elsewhere.
    """
    seen = {}
    for chapter in chapters:
        group_id = chapter.get('group_id')
        if group_id and group_id not in seen:
            seen[group_id] = chapter.get('group') or group_id
    return sorted(((label, gid) for gid, label in seen.items()),
                  key=lambda pair: pair[0].lower())


def filter_by_group(chapters, group_id):
    """Keep only chapters from one scanlation group. None keeps everything."""
    if not group_id:
        return list(chapters)
    return [c for c in chapters if c.get('group_id') == group_id]


def chapter_display(chapter):
    """`Ch.110 [OmegaScans]`, or just `Ch.110` when the group is unknown.

    Two groups publish the same chapter number, so a bare title gives the user
    two identical rows and no way to tell them apart.
    """
    title = chapter.get('title') or ''
    group = chapter.get('group')
    return f"{title} [{group}]" if group else title


def chapter_dir_name(chapter_title, group=None):
    """Directory segment for a chapter, nested under its group when given.

    Two groups publishing Ch.110 both sanitise to "Ch110" and would overwrite
    each other's pages. Nesting keeps them apart.

    With no group the result is exactly the plain sanitised title, so a
    single-group series produces byte-identical directories to before.
    """
    if not group:
        return sanitize_filename(chapter_title)
    return os.path.join(sanitize_filename(group),
                        sanitize_filename(chapter_title))


def _chapter_sort_key(chapter):
    """Sort key for the collected chapter list: number ascending, unnumbered last.

    The pager serves each page newest-first and the collector walks page 1
    first, while `get_chapters_from_soup` reverses each page. The result is
    ascending *within* a page and descending *between* pages:

        97, 98, 98.5, 99 ... 112,  87 ... 111,  77 ... 86,  67 ... 76

    Nothing in the pipeline sees the whole set at once, so the order has to be
    fixed at the end. Fractional chapters sort numerically, and a chapter whose
    number did not parse goes last rather than raising.
    """
    try:
        return (0, float(chapter['number']))
    except (KeyError, TypeError, ValueError):
        return (1, 0.0)


def _sort_chapters(chapters):
    """Order chapters by number, oldest first. Stable within equal keys."""
    return sorted(chapters, key=_chapter_sort_key)


def _chapter_status(chapter, seen_ids, group_id=None):
    """Classify one parsed chapter as 'new', 'duplicate' or 'other_group'.

    Dedupe on chapter **id**, never on title. comix hosts several scanlation
    groups publishing the same series, and two groups can both publish the same
    chapter number - on this series both OmegaScans and The Blank publish
    Ch.110. Keying on title silently dropped one of them, which is why earlier
    runs of the collector returned 20 chapters and then 19.

    Returns one of:
        'new'         - collected, and now recorded in seen_ids
        'duplicate'   - this id was already collected on an earlier page
        'other_group' - filtered out because group_id was requested
    """
    key = chapter.get('id')
    if key in seen_ids:
        return 'duplicate'
    if group_id and chapter.get('group_id') != group_id:
        return 'other_group'
    seen_ids.add(key)
    return 'new'


def get_manga_info(url_or_id, use_browser=True, group_id=None):
    """
    Get manga information including title and chapter list.
    Uses browser to handle JavaScript-loaded content.
    
    Args:
        url_or_id: Comix.to URL or manga ID
        use_browser: Use browser for complete chapter list (default: True)
        group_id: Only keep chapters from this scanlation group, given as its
            href e.g. '/groups/5121'. Matched on href, never on display text,
            because the site is inconsistent about capitalisation.
            None keeps every group.
    
    Returns:
        tuple: (manga_title, chapters_list)
    """
    manga_id = extract_manga_id(url_or_id)
    if not manga_id:
        print(f"Could not extract manga ID from: {url_or_id}")
        return None, []
    
    manga_url = f"{BASE_URL}/title/{manga_id}"
    
    if not use_browser or not SELENIUM_AVAILABLE:
        print("Warning: Browser automation not available. May not get complete chapter list.")
        return None, []
    
    browser = None
    try:
        pool = get_browser_pool(max_browsers=1)
        browser = pool.get_browser()
        
        print(f"Loading manga page: {manga_url}")
        browser.get(manga_url)
        time.sleep(10)  # Increased from 5s to 10s for pagination to fully load
        
        # Initialize pagination detection system
        try:
            from .pagination_detector import PaginationDetector
            from .pagination_navigator import PaginationNavigator
            from .content_change_detector import ContentChangeDetector
        except ImportError:
            from pagination_detector import PaginationDetector
            from pagination_navigator import PaginationNavigator
            from content_change_detector import ContentChangeDetector
        
        detector = PaginationDetector(browser, manga_id)
        navigator = PaginationNavigator(browser, detector)
        change_detector = ContentChangeDetector(browser, manga_id)
        
        all_chapters = []
        seen_chapter_ids = set()
        skipped = 0
        page_num = 1
        if group_id:
            print(f"Filtering to scanlation group {group_id}")
        
        # Get pagination info
        pagination_info = detector.get_pagination_info()
        total_pages = pagination_info['total_pages']
        
        print("Collecting chapters from all pages...")
        print(f"Page buttons visible: {total_pages} (the pager publishes no total)")
        
        # The pager shows a sliding window of page numbers and never states a
        # total, so `total_pages` is not the number of pages - it is how many
        # buttons happen to be on screen. Stopping there silently truncated the
        # chapter list before. Walk until the Next control runs out instead,
        # with a generous ceiling as a backstop against a pager that never
        # disables.
        max_pages = max(total_pages, 1) + MAX_PAGER_PAGES
        
        while page_num <= max_pages:
            print(f"\n--- Page {page_num} ---")
            
            soup = BeautifulSoup(browser.page_source, 'html.parser')
            
            if page_num == 1:
                title_elem = soup.find('h1')
                if not title_elem:
                    title_elem = soup.find('h2')
                if not title_elem:
                    title_elem = soup.find(class_='title')
                
                manga_title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                manga_title = re.sub(r'[^\x00-\x7F]+', '', manga_title).strip()
                print(f"Manga title: {manga_title}")
            
            chapters = get_chapters_from_soup(soup, manga_id)
            
            new_chapters = 0
            for chapter in chapters:
                status = _chapter_status(chapter, seen_chapter_ids, group_id)
                if status == 'new':
                    all_chapters.append(chapter)
                    new_chapters += 1
                elif status == 'other_group':
                    skipped += 1
            
            print(f"New chapters: {new_chapters} | Total: {len(all_chapters)}")
            if skipped:
                print(f"Skipped {skipped} chapters from other scanlation groups")
            
            if new_chapters == 0 and page_num > 1:
                print("No new chapters, stopping")
                break
            
            if not detector.is_next_enabled() and not detector.has_page_after(page_num):
                print(f"No further pages after {page_num} - last page")
                break
            
            # Capture current state before navigation
            old_count = change_detector.get_current_chapter_count()
            old_first = change_detector.get_first_chapter_title()
            
            # Try to navigate to next page
            print(f"Navigating to page {page_num + 1}...")
            success = navigator.navigate_to_next_page()
            
            if not success:
                print("Navigation failed, stopping")
                break
            
            # Verify content changed
            print("Waiting for content to load...")
            changed = change_detector.wait_for_content_change(old_count, old_first, timeout=10)
            
            if not changed:
                print("Content didn't change, stopping")
                break
            
            print("Content loaded successfully")
            page_num += 1

        # Each page came back ascending and pages were appended newest first, so
        # the raw order is 97..112, then 87..111, then 77..86. This is the only
        # point that has seen every page, so it is the only place the order can
        # be fixed. It also makes --range 1-10 mean the ten lowest chapters
        # rather than the first ten the pager happened to show.
        all_chapters = _sort_chapters(all_chapters)

        print(f"\n=== Pagination Complete ===")
        print(f"Total chapters collected: {len(all_chapters)}")
        print(f"Pages processed: {page_num}")
        if navigator.successful_method:
            print(f"Successful navigation method: {navigator.successful_method}")
        
        pool.return_browser(browser)
        return manga_title, all_chapters
        
    except Exception as e:
        print(f"Error fetching manga info: {e}")
        if browser:
            pool.return_browser(browser)
        return None, []


def get_chapters_from_soup(soup, manga_id):
    """Extract chapters from BeautifulSoup object."""
    chapters = []
    seen_urls = set()
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        
        if not href or '/title/' not in href:
            continue
        
        if f'/title/{manga_id}/' not in href:
            continue
        
        chapter_url = href if href.startswith('http') else urljoin(BASE_URL, href)
        
        if chapter_url in seen_urls:
            continue
        
        match = re.search(rf'/title/{re.escape(manga_id)}/(\d+)-', chapter_url)
        if not match:
            continue
        
        chapter_id = match.group(1)
        seen_urls.add(chapter_url)
        
        chapter_title = link.get_text(strip=True)
        if not chapter_title or len(chapter_title) < 2:
            continue
        
        chapter_title = re.sub(r'[^\x00-\x7F]+', '', chapter_title).strip()
        
        number_match = (
            re.search(r'[Cc]hapter\s*(\d+(?:\.\d+)?)', chapter_title) or
            re.search(r'Ch\.?\s*(\d+(?:\.\d+)?)', chapter_title, re.IGNORECASE) or
            re.search(r'^(\d+(?:\.\d+)?)', chapter_title)
        )
        chapter_number = number_match.group(1) if number_match else None
        
        # comix hosts several scanlation groups publishing the same series, and
        # two groups can both publish the same chapter number. The group lives
        # on the enclosing row, not on the link. `mchap-row__group` is the
        # scanlation group; `mchap-row__uploader` is the person who uploaded.
        # They are separate fields - do not read one for the other.
        #
        # Filter on group_id (the /groups/NNNN href), never on the display text:
        # the same page writes "OmegaScans" in the row and lowercase
        # "omegascans" elsewhere.
        group = group_id = uploader = None
        row = link.find_parent('li', class_='mchap-item')
        if row is not None:
            group_link = row.find('a', class_='mchap-row__group')
            if group_link:
                group = group_link.get_text(strip=True)
                group_id = group_link.get('href')
            uploader_link = row.find('a', class_='mchap-row__uploader')
            if uploader_link:
                uploader = uploader_link.get_text(strip=True)
        
        if chapter_id and chapter_url and chapter_title:
            chapters.append({
                'id': chapter_id,
                'number': chapter_number,
                'title': chapter_title,
                'url': chapter_url,
                'group': group,
                'group_id': group_id,
                'uploader': uploader
            })
    
    chapters.reverse()
    return chapters


# The reader is a virtualised long strip: it only renders the pages near the
# viewport, so the page list has to be harvested while scrolling. Two details
# were measured on the live site rather than guessed:
#
#   * `body` is `overflow: hidden` and the document itself does not scroll, so
#     `window.scrollBy()` is a no-op. The scrolling element is found by asking
#     which ancestor of a page element is actually scrollable.
#   * every page element carries `data-page`, which supplies both the ordering
#     and a trustworthy total, so a short harvest is detectable rather than
#     silently returned as a complete chapter.

_FIND_SCROLLER_JS = """
var page = document.querySelector('[data-page]');
while (page && page !== document.body) {
    if (page.scrollHeight > page.clientHeight + 4) { return page; }
    page = page.parentElement;
}
return null;
"""

_HARVEST_PAGES_JS = """
var found = {};
var holders = document.querySelectorAll('[data-page]');
for (var i = 0; i < holders.length; i++) {
    var img = holders[i].querySelector('img');
    if (!img) { continue; }
    var src = img.getAttribute('src') || '';
    if (src.indexOf('http') !== 0) { continue; }
    found[holders[i].getAttribute('data-page')] = src;
}
return found;
"""


_READ_SCROLLER_JS = """
var e = arguments[0];
return [e.scrollHeight, e.clientHeight, e.scrollTop];
"""

# The reader scrolls smoothly. Assigning scrollTop therefore reads back as 0
# for roughly a second while the position animates, which is indistinguishable
# from "the container will not scroll" if you sample too early. Measured on
# Ch.10: 0 at +0.0s, 1540 at +0.3s, 4130 at +0.6s, 4989 at +1.2s.
# Forcing instant behaviour removes the whole problem.
_DISABLE_SMOOTH_SCROLL_JS = """
arguments[0].style.setProperty('scroll-behavior', 'auto', 'important');
return getComputedStyle(arguments[0]).scrollBehavior;
"""

# The reader renders a progress rail with one jump button per page:
#   <button class="rpage-progress__seg" title="Page 1" aria-label="Go to page 1">
#
# This is a far better way in than scrolling. The reader resets its scroll
# position to the top every ~90 passes and unmounts whatever scrolled past, so
# a sweep collects at most a few dozen pages out of ~110 no matter how long it
# waits. Clicking each segment lands directly on one page, gives it exactly one
# image-load of time, and needs no recovery. Ch.6: 107/107 in 130s by jumping,
# 12/107 after 473s of scrolling.
#
# The segment count is also the authoritative page count, which the scroll maths
# could only approximate.
_PAGE_SEGMENT_COUNT_JS = "return document.querySelectorAll('.rpage-progress__seg').length;"
_GOTO_PAGE_JS = """
var segs = document.querySelectorAll('.rpage-progress__seg');
var i = arguments[0];
if (i < 0 || i >= segs.length) { return false; }
segs[i].click();
return true;
"""

# Deliberately no Referer. The image CDN serves a Cloudflare block page to any
# request that carries one, which is why the reader tags every <img> with
# referrerpolicy="no-referrer". Measured on the 1xx.* mirrors: Referer present
# -> 403, absent -> 200. Note the failure is host-dependent - the
# c150.kkplayer.wtf mirrors ignore Referer, so testing there hides the bug.
_IMAGE_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/155.0.0.0 Safari/537.36')
}


# Image formats recognised by their leading bytes. Checked before anything the
# server claims, because the bytes are already in memory and cannot lie.
_IMAGE_MAGIC = (
    (b'\xff\xd8\xff', 'jpg'),
    (b'\x89PNG\r\n\x1a\n', 'png'),
    (b'GIF87a', 'gif'),
    (b'GIF89a', 'gif'),
    (b'RIFF', 'webp'),
)

_CONTENT_TYPE_EXT = {
    'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/pjpeg': 'jpg',
    'image/png': 'png', 'image/apng': 'png',
    'image/gif': 'gif', 'image/webp': 'webp', 'image/bmp': 'bmp',
}

_URL_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}


def _url_extension(img_url):
    """Suffix of the path only - never a query value or fragment."""
    if not img_url:
        return None
    path = img_url.split('?', 1)[0].split('#', 1)[0]
    last = path.rsplit('/', 1)[-1]
    if '.' not in last:
        return None
    ext = last.rsplit('.', 1)[-1].lower()
    return ext if ext in _URL_EXTENSIONS else None


def _image_extension(img_url, content_type=None, content=b''):
    """Decide the saved extension from what was actually downloaded.

    comix serves images from /hi/<token>, a path with no extension at all, so
    the old code - which took the extension from the URL string - always fell
    through to 'jpg' and saved WebP bytes as page_001.jpg.

    Order is deliberate: the bytes first, because they are the file and are
    already in memory; Content-Type next, because it is only the server's
    claim; the URL last, because a suffix is a hint and can contradict either.
    Measured 2026-10-12 against the live CDN: Content-Type read image/webp and
    agreed with the magic number on 6/6 responses, while the URL guess named
    all 6 .jpg.
    """
    head = content[:16] if content else b''
    for signature, ext in _IMAGE_MAGIC:
        if head.startswith(signature):
            return ext

    if content_type:
        mime = content_type.split(';', 1)[0].strip().lower()
        if mime in _CONTENT_TYPE_EXT:
            return _CONTENT_TYPE_EXT[mime]

    ext = _url_extension(img_url)
    if ext:
        return 'jpg' if ext == 'jpeg' else ext
    return 'jpg'


def _normalise_pages(raw):
    """Turn a raw harvest into {page number: image url}, dropping junk.

    Page numbers are what order the chapter, so a key that is not a number is
    discarded rather than sorted lexically into the wrong position.
    """
    pages = {}
    for key, src in (raw or {}).items():
        try:
            pages[int(key)] = src
        except (TypeError, ValueError):
            continue
    return pages


def _page_urls(pages):
    """Page URLs in page order. data-page is the only ordering signal there is."""
    return [pages[number] for number in sorted(pages)]


def _completeness_warning(pages):
    """Warn when the harvest is short, so a partial chapter is never silent."""
    if not pages:
        return "No image URLs found."
    declared = max(pages)
    if len(pages) < declared:
        return (f"Warning: expected {declared} pages but collected "
                f"{len(pages)}.")
    return None


def _scroll_collect(browser, chapter_url, pages, harvest, scroll_pause,
                    max_passes):
    """Fallback: walk the reader by scrolling, harvesting as pages mount.

    Only used when the progress rail is absent. The reader resets its scroll
    position to the top every ~90 passes and unmounts whatever scrolled past,
    so this reliably collects only a fraction of a long chapter no matter how
    patient the walk is. It is kept because it is all that is left if the rail
    changes, not because it works well.
    """
    scroller = browser.execute_script(_FIND_SCROLLER_JS)
    if not scroller:
        print("Warning: no scrollable reader element found, "
              "returning only the pages already mounted.")
        return pages

    found = dict(pages)

    def metrics():
        return browser.execute_script(_READ_SCROLLER_JS, scroller)

    height, client, top = metrics()
    step = max(200, int(client * 0.8))
    # The reader scrolls smoothly, so scrollTop reads back as 0 for about a
    # second while the position animates. Measured on Ch.10: 0 at +0.0s, 1540
    # at +0.3s, 4130 at +0.6s, 4989 at +1.2s. Sample too early and a working
    # scroll is indistinguishable from a stuck one.
    browser.execute_script(_DISABLE_SMOOTH_SCROLL_JS, scroller)
    print(f"Scrolling reader: {height}px tall, {step}px per pass...")

    passes = 0
    stalled = 0
    while passes < max_passes:
        bottom = height - client
        if top >= bottom - 4:
            break

        prev_top = top
        browser.execute_script(
            "arguments[0].scrollTop = arguments[1];",
            scroller, min(top + step, bottom))
        time.sleep(scroll_pause)
        passes += 1

        found.update(harvest())
        height, client, top = metrics()

        if top <= prev_top:
            fresh = browser.execute_script(_FIND_SCROLLER_JS)
            if fresh is not None and fresh != scroller:
                scroller = fresh
                browser.execute_script(_DISABLE_SMOOTH_SCROLL_JS, scroller)
                height, client, top = metrics()
                continue
            stalled += 1
            if stalled >= 3:
                print("Warning: reader stopped scrolling before the end.")
                break
        else:
            stalled = 0

    found.update(harvest())
    print(f"Scrolled {passes} passes, collected {len(found)} pages.")
    return found


def get_chapter_images(chapter_url, use_browser=True, scroll_pause=1.2,
                       max_passes=400, return_meta=False):
    """
    Get image URLs for a chapter.
    Comix.to loads images via JavaScript, so browser automation is required.

    Args:
        chapter_url: Full chapter URL
        use_browser: Use Selenium browser (required for comix.to)
        scroll_pause: Seconds to give each page to mount its image. 1.2s is
            measured, not guessed: the reader needs a moment to attach the
            image and unmounts it again once it leaves the viewport.
        max_passes: Safety bound on scroll passes, fallback path only
        return_meta: return `(urls, declared_pages)` instead of just urls

    Returns:
        list: Image URLs in page order.
              With `return_meta=True`, a pair instead:

                urls            what the harvest actually collected
                declared_pages  how many pages the reader says there are

              These are different numbers and the gap is the whole point of a
              resume check. The collected list is what can be downloaded *this
              time*; the declared count is what the chapter *is*. They diverge
              whenever the walk comes up short, which the function already
              reports as "Collected N of M declared pages".

              `declared_pages` comes from the progress rail and is 0 when the
              rail is absent, because the scrolling fallback cannot know. **0
              means unknown, not empty.** A caller asking whether a chapter is
              already finished must refuse to decide on 0 rather than read it
              as "nothing to fetch".
    """
    if not use_browser or not SELENIUM_AVAILABLE:
        print("Warning: Browser automation not available. Comix.to requires Selenium.")
        return ([], 0) if return_meta else []

    pool = None
    browser = None
    try:
        pool = get_browser_pool(max_browsers=1)
        browser = pool.get_browser()

        print(f"Loading chapter page: {chapter_url}")
        browser.get(chapter_url)
        time.sleep(5)

        def harvest():
            return _normalise_pages(browser.execute_script(_HARVEST_PAGES_JS))

        pages = harvest()

        # Preferred path: one jump per page via the progress rail.
        total = 0
        try:
            total = browser.execute_script(_PAGE_SEGMENT_COUNT_JS) or 0
        except Exception:
            total = 0

        if total:
            print(f"Reader exposes {total} page buttons, visiting each...")
            for index in range(total):
                if not browser.execute_script(_GOTO_PAGE_JS, index):
                    break
                time.sleep(scroll_pause)
                pages.update(harvest())
            pages.update(harvest())
            print(f"Collected {len(pages)} of {total} declared pages.")
        else:
            pages = _scroll_collect(browser, chapter_url, pages, harvest,
                                    scroll_pause, max_passes)

        image_urls = _page_urls(pages)

        warning = _completeness_warning(pages)
        if warning:
            print(warning)

        pool.return_browser(browser)
        if return_meta:
            return image_urls, total
        return image_urls

    except Exception as e:
        print(f"Error fetching chapter images: {e}")
        if browser:
            pool.return_browser(browser)
        return ([], 0) if return_meta else []


def sanitize_filename(name):
    """Sanitize filename to remove invalid Windows characters."""
    if not name:
        return "untitled"
    
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name.rstrip('.')


def _chapter_is_complete(chapter_dir, expected_pages):
    """Is every page of a chapter already on disk?

    `expected_pages` is the count from data-page, i.e. what the reader itself
    declares. Anything less is treated as incomplete.

    The hole check matters more than it looks: download_image_with_retry runs
    `max_workers` image threads, so a crash tends to drop the tail of a chapter.
    A naive "does page_001 exist" would call that complete. Extra pages beyond
    the expected count are fine - never redownload for having too many.
    """
    if not expected_pages:
        return False
    if not chapter_dir or not os.path.isdir(chapter_dir):
        return False

    found = set()
    try:
        entries = os.listdir(chapter_dir)
    except OSError:
        return False
    for name in entries:
        m = re.match(r"^page_(\d+)\.(?:jpe?g|png|gif|webp|bmp)$", name, re.I)
        if m:
            found.add(int(m.group(1)))

    if not found:
        return False
    # a gap anywhere, at any depth, means incomplete
    if len(found) != max(found):
        return False
    return len(found) >= expected_pages


def _resume_blockers(chapter_dir, output_format, convert_to_pdf, convert_to_cbz):
    """Reasons a chapter whose pages are all on disk still must not be skipped.

    Page count answers "did the images arrive", not "did the caller get what it
    asked for". comix serves WebP, so a default download leaves .webp files;
    _chapter_is_complete counts any of jpe?g|png|gif|webp|bmp as a page, and
    `--format jpeg --resume` over that directory would skip it and produce no
    JPEG at all, without a word. `--pdf` and `--cbz` skip the same way and skip
    the conversion too.

    Returns a list of readable reasons - empty when skipping is safe. A list
    rather than a bool because the CLI prints them: re-downloading a complete
    chapter is wasteful, so the user is told exactly what forced it.
    """
    reasons = []

    wanted_format = str(output_format or "original").lower()
    if wanted_format in ("jpeg", "jpg", "png"):
        suffix = "jpg" if wanted_format in ("jpeg", "jpg") else "png"
        page_re = re.compile(r"^page_(\d+)\.(jpe?g|png|gif|webp|bmp)$", re.I)
        try:
            entries = os.listdir(chapter_dir)
        except OSError:
            entries = []
        # Count rather than look for any match. Conversion writes pages one at a
        # time, so an interrupted run leaves some pages converted and the rest
        # not - "is there one .jpg" would call that done and skip the chapter
        # with half of it still WebP. Same strictness as _chapter_is_complete.
        converted = 0
        unconverted = 0
        for name in entries:
            m = page_re.match(name)
            if not m:
                continue
            ext = m.group(2).lower()
            if ("jpg" if ext in ("jpg", "jpeg") else ext) == suffix:
                converted += 1
            else:
                unconverted += 1
        if converted == 0:
            reasons.append(f"no .{suffix} pages on disk")
        elif unconverted:
            reasons.append(f"{unconverted} page(s) on disk are in another format")

    if convert_to_pdf and not os.path.exists(chapter_dir + ".pdf"):
        reasons.append("no PDF yet")
    if convert_to_cbz and not os.path.exists(chapter_dir + ".cbz"):
        reasons.append("no CBZ yet")

    return reasons


def _drop_sibling_page_formats(chapter_dir, base_name, keep_path):
    """Remove page files of this same page in other formats, keeping keep_path.

    download_image_with_retry writes page_003.jpg next to the page_003.webp that
    is already in the directory and removes nothing, so a chapter re-downloaded
    to change format accumulates rather than converges. Measured over three runs
    on a six-page WebP chapter: the directory held twelve files for six pages,
    download_chapter counted 12 against 6 and printed 'Chapter incomplete', and
    _resume_blockers reported '6 page(s) on disk are in another format' again
    every time - so the chapter was re-downloaded forever and reported as failed
    while actually being complete.

    Only siblings of the same page number are touched, and only after the new
    file is known to have content, so an interrupted run cannot lose data it
    did not replace.
    """
    pattern = re.compile(
        rf"^{re.escape(base_name)}\.(?:jpe?g|png|gif|webp|bmp)$", re.I)
    try:
        entries = os.listdir(chapter_dir)
    except OSError:
        return
    keep = os.path.normcase(os.path.abspath(keep_path))
    for name in entries:
        if not pattern.match(name):
            continue
        path = os.path.join(chapter_dir, name)
        if os.path.normcase(os.path.abspath(path)) == keep:
            continue
        try:
            os.remove(path)
        except OSError:
            pass


def download_chapter(chapter_url, manga_title, chapter_title, output_dir=".",
                      stop_event=None, convert_to_pdf=False, convert_to_cbz=False,
                      keep_images=True, max_workers=15, output_format="original",
                      jpeg_quality=92, max_retries=3, group=None, resume=False):
    """
    Download all images for a chapter with verification and retry.
    
    Args:
        chapter_url: Full chapter URL
        manga_title: Manga title for folder naming
           chapter_title: Chapter title for folder naming
           group: Scanlation group name. When given, the chapter folder is
               nested under it, because two groups publishing the same
               chapter number would otherwise overwrite each other.
           output_dir: Output directory
        stop_event: Threading event to signal stop
        convert_to_pdf: Convert to PDF after download
        convert_to_cbz: Convert to CBZ after download
        keep_images: Keep images after conversion
        max_workers: Concurrent image downloads
        output_format: Image format (original, png, jpeg)
        jpeg_quality: JPEG quality (1-100)
        max_retries: Maximum retry attempts for failed downloads
        
    Returns:
        dict: {
            'success': bool,
            'total_images': int,
            'downloaded': int,
            'failed': int,
            'chapter_dir': str or None,
            'bytes': int,
            'stopped': bool
        }
        Every return path carries the same keys. 'skipped' appears only when
        resume=True and the chapter was already complete. 'stopped' is True on
        exactly one path - the one where stop_event was already set - and it is
        the only way a caller can tell "you asked me to stop" from "this chapter
        failed", since both otherwise look like success False and no images.
    """
    if stop_event and stop_event.is_set():
        # 'stopped' distinguishes this from a chapter that genuinely failed.
        # A caller cannot tell them apart from the rest of the dict - both have
        # success False and zero images - and guessing from a stop_event the
        # caller happens to observe would swallow failures that happened before
        # the stop landed.
        return {'success': False, 'total_images': 0, 'downloaded': 0, 'failed': 0, 'chapter_dir': None, 'bytes': 0, 'stopped': True}
    
    gathered = get_chapter_images(chapter_url, return_meta=True)
    # A bare list would unpack as a valid pair - two URLs read as
    # (urls="a", declared=2) - and silently corrupt the completeness check
    # below. Fail loudly instead.
    if not (isinstance(gathered, tuple) and len(gathered) == 2
            and isinstance(gathered[1], int) and not isinstance(gathered[1], bool)):
        raise TypeError(
            f"get_chapter_images(return_meta=True) must return "
            f"(urls, declared_pages); got {type(gathered).__name__}"
        )
    image_urls, declared_pages = gathered
    if not image_urls:
        print(f"No images found for chapter: {chapter_title}")
        return {'success': False, 'total_images': 0, 'downloaded': 0, 'failed': 0, 'chapter_dir': None, 'bytes': 0, 'stopped': False}
    
    sanitized_manga = sanitize_filename(manga_title)
    chapter_dir = os.path.join(output_dir, sanitized_manga,
                               chapter_dir_name(chapter_title, group))
    os.makedirs(chapter_dir, exist_ok=True)
    
    # The target is the reader's declared count, NOT len(image_urls). Those are
    # different numbers whenever the harvest came up short, and using the
    # collected one would let a 100-page chapter that yielded 87 URLs match 87
    # files on disk and be skipped with 13 pages never fetched.
    #
    # declared_pages is 0 when the progress rail is absent - the scrolling
    # fallback cannot know the count, and _chapter_is_complete treats 0 as
    # "never skip". It fails closed.
    if resume and _chapter_is_complete(chapter_dir, declared_pages):
        # Having every page is not the same as having what was asked for.
        # Without this, `--format jpeg --resume` over a WebP download skips and
        # silently produces nothing.
        blockers = _resume_blockers(chapter_dir, output_format,
                                    convert_to_pdf, convert_to_cbz)
        if blockers:
            print(f"Re-downloading {chapter_title} - "
                  f"{'; '.join(blockers)}")
        else:
            print(f"Skipping {chapter_title} - all {declared_pages} declared pages "
                  f"already on disk")
            return {'success': True, 'total_images': declared_pages,
                    'downloaded': 0, 'failed': 0, 'skipped': True,
                    'chapter_dir': chapter_dir, 'bytes': 0,
                    'stopped': False}
    
    print(f"Downloading {len(image_urls)} images for {chapter_title}")
    
    # Track download results
    download_results = {
        'success': False,
        'total_images': len(image_urls),
        'downloaded': 0,
        'failed': 0,
        'chapter_dir': chapter_dir,
        'bytes': 0,
        'stopped': False
    }
    
    print_lock = threading.Lock()
    
    def download_image_with_retry(img_url, index, retry_count=0):
        """Download single image with retry logic and verification."""
        if stop_event and stop_event.is_set():
            return False
        
        try:
            response = requests.get(img_url, headers=_IMAGE_HEADERS, timeout=30)
            response.raise_for_status()
            
            base_name = f"page_{index+1:03d}"

            if output_format.lower() in ('png', 'jpeg', 'jpg') and PIL_AVAILABLE:
                from io import BytesIO
                img = Image.open(BytesIO(response.content))
                
                if output_format.lower() == 'png':
                    img_path = os.path.join(chapter_dir, f"{base_name}.png")
                    img = img.convert('RGBA') if img.mode == 'RGBA' else img.convert('RGB')
                    img.save(img_path, 'PNG', optimize=True)
                else:
                    img_path = os.path.join(chapter_dir, f"{base_name}.jpg")
                    if img.mode in ('RGBA', 'P', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if len(img.split()) == 4 else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(img_path, 'JPEG', quality=jpeg_quality, optimize=True)
            else:
                ext = _image_extension(img_url,
                                       response.headers.get('Content-Type'),
                                       response.content)
                img_path = os.path.join(chapter_dir, f"{base_name}.{ext}")
                with open(img_path, 'wb') as f:
                    f.write(response.content)
            
            # Verify file was created and has content
            written = os.path.getsize(img_path) if os.path.exists(img_path) else 0
            if written > 0:
                _drop_sibling_page_formats(chapter_dir, base_name, img_path)
                with print_lock:
                    download_results['downloaded'] += 1
                    download_results['bytes'] += written
                    print(f"✓ Downloaded page {index+1}/{len(image_urls)}")
                return True
            else:
                raise Exception("File not created or empty")
                
        except Exception as e:
            if retry_count < max_retries:
                # Exponential backoff: 2^retry_count seconds
                wait_time = 2 ** retry_count
                with print_lock:
                    print(f"⟳ Retry {retry_count + 1}/{max_retries} for page {index+1} (waiting {wait_time}s)")
                time.sleep(wait_time)
                return download_image_with_retry(img_url, index, retry_count + 1)
            else:
                with print_lock:
                    download_results['failed'] += 1
                    print(f"✗ Failed page {index+1} after {max_retries} retries: {e}")
                return False
    
    # A requested format that cannot be honoured must say so. Without this,
    # --format jpeg on an install without Pillow quietly writes WebP and
    # still reports the chapter complete. Once per chapter, not once per
    # page: 172 pages would otherwise print this 172 times.
    if str(output_format).lower() in ('png', 'jpeg', 'jpg') \
            and not PIL_AVAILABLE:
        print(f"! Pillow is not installed, so --format {output_format} "
              f"cannot be applied. Saving the original format instead. "
              f"Install it with: pip install Pillow")

    # Download with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_image_with_retry, url, i): i 
                   for i, url in enumerate(image_urls)}
        
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Unexpected error: {e}")
    
    # Final verification - count actual downloaded files
    try:
        downloaded_files = [f for f in os.listdir(chapter_dir) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        actual_count = len(downloaded_files)
    except Exception:
        actual_count = 0
    
    expected_count = len(image_urls)
    download_results['success'] = (actual_count == expected_count and download_results['failed'] == 0)
    
    if download_results['success']:
        print(f"✓ Chapter complete: {actual_count}/{expected_count} images")
    else:
        print(f"⚠ Chapter incomplete: {actual_count}/{expected_count} images ({download_results['failed']} failed)")
    
    # PDF/CBZ conversion
    if convert_to_pdf:
        print(f"Converting {chapter_title} to PDF...")
        pdf_file = convert_chapter_to_pdf(chapter_dir, delete_images=not keep_images)
        if pdf_file:
            print(f"PDF created: {pdf_file}")
    
    if convert_to_cbz:
        print(f"Converting {chapter_title} to CBZ...")
        cbz_file = convert_chapter_to_cbz(chapter_dir, manga_title, chapter_title, delete_images=not keep_images)
        if cbz_file:
            print(f"CBZ created: {cbz_file}")
    
    return download_results


def convert_chapter_to_pdf(chapter_dir, delete_images=False):
    """Convert chapter images to PDF."""
    if not PIL_AVAILABLE:
        print("PIL not available, cannot convert to PDF")
        return None
    
    from PIL import Image
    
    image_files = [os.path.join(chapter_dir, f) for f in os.listdir(chapter_dir)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    image_files.sort(key=lambda f: int(m.group(1)) if (m := re.search(r'page_(\d+)', os.path.basename(f))) else 0)
    
    if not image_files:
        print(f"No images found in {chapter_dir}")
        return None
    
    pdf_path = chapter_dir + ".pdf"
    
    try:
        images = []
        for img_file in image_files:
            try:
                img = Image.open(img_file).convert("RGB")
                images.append(img)
            except Exception as e:
                print(f"Error opening {img_file}: {e}")
        
        if images:
            images[0].save(pdf_path, save_all=True, append_images=images[1:])
            
            if delete_images:
                for img_file in image_files:
                    try:
                        os.remove(img_file)
                    except Exception:
                        pass
                try:
                    os.rmdir(chapter_dir)
                except OSError:
                    pass
            
            return pdf_path
    except Exception as e:
        print(f"Error creating PDF: {e}")
    
    return None


def _create_comic_info_xml(manga_title, chapter_title):
    """Create ComicInfo.xml content for CBZ."""
    root = ET.Element("ComicInfo")
    
    series = ET.SubElement(root, "Series")
    series.text = manga_title
    
    title = ET.SubElement(root, "Title")
    title.text = chapter_title
    
    match = re.search(r'[Cc]hapter\s*(\d+(?:\.\d+)?)', chapter_title)
    if match:
        number = ET.SubElement(root, "Number")
        number.text = match.group(1)
    
    notes = ET.SubElement(root, "Notes")
    notes.text = "Generated by Comix-Downloader"
    
    xml_str = ET.tostring(root, 'utf-8')
    return minidom.parseString(xml_str).toprettyxml(indent="  ")


def convert_chapter_to_cbz(chapter_dir, manga_title, chapter_title, delete_images=False):
    """Convert chapter images to CBZ."""
    image_files = [os.path.join(chapter_dir, f) for f in os.listdir(chapter_dir)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    image_files.sort(key=lambda f: int(m.group(1)) if (m := re.search(r'page_(\d+)', os.path.basename(f))) else 0)
    
    if not image_files:
        return None
    
    cbz_path = chapter_dir + ".cbz"
    
    try:
        comic_info = _create_comic_info_xml(manga_title, chapter_title)
        
        with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
            cbz.writestr("ComicInfo.xml", comic_info)
            for img_file in image_files:
                cbz.write(img_file, os.path.basename(img_file))
        
        if delete_images:
            for img_file in image_files:
                try:
                    os.remove(img_file)
                except Exception:
                    pass
            try:
                os.rmdir(chapter_dir)
            except OSError:
                pass
        
        return cbz_path
    except Exception as e:
        print(f"Error creating CBZ: {e}")
    
    return None
