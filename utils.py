"""
Utility functions for SEO Analyzer
"""

import re
from urllib.parse import urlparse
import time
from datetime import datetime

def ensure_url_protocol(url):
    """Ensure URL has http/https protocol"""
    url = url.strip()
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def get_domain_from_url(url):
    """Extract domain from URL"""
    parsed = urlparse(url)
    return parsed.netloc

def clean_text_content(soup):
    """Clean and extract text content from BeautifulSoup object"""
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text content
    text_content = soup.get_text()
    
    # Clean text
    lines = (line.strip() for line in text_content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text_content = ' '.join(chunk for chunk in chunks if chunk)
    
    return text_content

def calculate_seo_score_color(score):
    """Get color based on SEO score"""
    if score < 20:
        return '#E74C3C'
    elif score < 40:
        return '#E67E22'
    elif score < 60:
        return '#F39C12'
    elif score < 80:
        return '#F1C40F'
    else:
        return '#27AE60'

def format_timestamp():
    """Get formatted timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def filter_business_emails(emails, blacklist_domains, blacklist_patterns):
    """Filter and prioritize business emails"""
    filtered_emails = []
    
    for email in emails:
        # Check if it's a valid business email
        if '@' in email and '.' in email.split('@')[1]:
            domain = email.split('@')[1].lower()
            local_part = email.split('@')[0].lower()
            
            # Skip blacklisted domains
            if any(blacklist in domain for blacklist in blacklist_domains):
                continue
            
            # Skip blacklisted patterns
            if any(re.match(pattern, email.lower()) for pattern in blacklist_patterns):
                continue
            
            # Skip emails that look like IDs
            if len(local_part) > 30 or local_part.replace('.', '').replace('_', '').replace('-', '').isdigit():
                continue
            
            # Skip if local part is mostly numbers
            if sum(c.isdigit() for c in local_part) > len(local_part) * 0.7:
                continue
            
            # Skip if it contains common code/hash patterns
            if re.match(r'^[a-f0-9]+$', local_part) and len(local_part) > 10:
                continue
            
            filtered_emails.append(email)
    
    return filtered_emails

def safe_get_dict_value(dictionary, *keys, default=None):
    """Safely get nested dictionary values"""
    value = dictionary
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default
    return value

def truncate_text(text, max_length=100, suffix='...'):
    """Truncate text to specified length"""
    if text and len(text) > max_length:
        return text[:max_length] + suffix
    return text

def retry_on_failure(func, max_retries=3, delay=1):
    """Retry a function on failure with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay * (2 ** attempt))
    return None

def is_valid_url(url):
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def create_progress_message(current, total, message="Processing"):
    """Create a progress message"""
    percentage = (current / total) * 100 if total > 0 else 0
    return f"{message} {current}/{total} ({percentage:.0f}%)"

def parse_load_time(load_time_str):
    """Parse load time string to float"""
    try:
        # Remove 's' suffix if present
        if isinstance(load_time_str, str) and load_time_str.endswith('s'):
            return float(load_time_str[:-1])
        return float(load_time_str)
    except:
        return 0.0

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"