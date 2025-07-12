"""
Screenshot Module - Handles website screenshot capture
"""

import time
import threading
from io import BytesIO

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .config import CHROME_OPTIONS

class ScreenshotModule:
    def __init__(self):
        self.driver = None
        self.is_initialized = False
        
    def initialize(self):
        """Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not installed. Install with: pip install selenium")
        
        if not PIL_AVAILABLE:
            raise ImportError("Pillow not installed. Install with: pip install pillow")
        
        try:
            chrome_options = Options()
            for option in CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # Additional options to suppress logs
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.is_initialized = True
            return True
            
        except Exception as e:
            raise Exception(f"Failed to initialize Chrome driver: {str(e)}\n"
                          f"Please ensure Chrome and ChromeDriver are installed.")
    
    def capture_screenshot_async(self, url, callback=None):
        """Capture screenshot asynchronously"""
        def _capture():
            try:
                screenshot = self.capture_screenshot(url)
                if callback:
                    callback(url, screenshot)
            except Exception as e:
                print(f"Screenshot error for {url}: {e}")
                if callback:
                    callback(url, None)
        
        thread = threading.Thread(target=_capture, daemon=True)
        thread.start()
        return thread
    
    def capture_screenshot(self, url):
        """Capture screenshot of a website"""
        if not self.is_initialized:
            return None
        
        try:
            # Load the page
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give extra time for dynamic content
            time.sleep(2)
            
            # Take screenshot
            screenshot = self.driver.get_screenshot_as_png()
            
            # Convert to PIL Image for manipulation
            img = PILImage.open(BytesIO(screenshot))
            
            # Resize if too large (maintain aspect ratio)
            max_width = 800
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), PILImage.Resampling.LANCZOS)
            
            # Save to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            print(f"Screenshot error for {url}: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.is_initialized = False