"""
Configuration and constants for SEO Analyzer
"""

import os
import warnings
import logging

# Suppress warnings
warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').disabled = True
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Application Info
APP_NAME = "Professional SEO Analyzer Pro - AI Edition"
APP_VERSION = "4.0"
WINDOW_SIZE = "1300x850"

# Colors
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#34495E',
    'success': '#27AE60',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'info': '#3498DB',
    'light': '#ECF0F1',
    'white': '#FFFFFF',
    'purple': '#9B59B6',
    'turquoise': '#1ABC9C'
}

# Email Filtering
BLACKLIST_DOMAINS = [
    'sentry', 'wixpress', 'example', 'test', 'schema.org', 
    'w3.org', 'googleapis', 'gstatic', 'google-analytics',
    'facebook.com', 'twitter.com', 'schema.org', 'json-ld',
    'wordpress.com', 'wp.com', 'cloudflare', 'jquery',
    'bootstrap', 'fontawesome', 'googleapis.com', 'github.com',
    'gravatar.com', 'wp.org', 'wordpress.org'
]

BLACKLIST_EMAIL_PATTERNS = [
    r'^[0-9a-f]{20,}@',  # Long hex strings
    r'noreply@', r'no-reply@', r'donotreply@',
    r'^id[0-9]+@', r'^[0-9]+@',  # Numeric IDs
    r'^[a-f0-9]{32}@',  # MD5 hashes
    r'^[a-f0-9]{40}@',  # SHA1 hashes
    r'^[a-f0-9]{64}@',  # SHA256 hashes
]

BUSINESS_EMAIL_KEYWORDS = [
    'contact', 'info', 'sales', 'support', 'hello', 'admin', 
    'office', 'help', 'inquiry', 'service', 'team', 'business',
    'enquiry', 'customer', 'marketing'
]

# Social Media Patterns
SOCIAL_PATTERNS = {
    'facebook': r'(?:https?:)?\/\/(?:www\.)?facebook\.com\/[a-zA-Z0-9._-]+',
    'twitter': r'(?:https?:)?\/\/(?:www\.)?twitter\.com\/[a-zA-Z0-9_]+',
    'instagram': r'(?:https?:)?\/\/(?:www\.)?instagram\.com\/[a-zA-Z0-9._-]+',
    'linkedin': r'(?:https?:)?\/\/(?:www\.)?linkedin\.com\/(?:company|in)\/[a-zA-Z0-9._-]+',
    'youtube': r'(?:https?:)?\/\/(?:www\.)?youtube\.com\/(?:c|channel|user)\/[a-zA-Z0-9._-]+',
    'tiktok': r'(?:https?:)?\/\/(?:www\.)?tiktok\.com\/@[a-zA-Z0-9._-]+',
    'pinterest': r'(?:https?:)?\/\/(?:www\.)?pinterest\.com\/[a-zA-Z0-9._-]+'
}

# Chrome Options
CHROME_OPTIONS = [
    '--headless',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--window-size=1920,1080',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    '--log-level=3'
]

# API URLs
PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
GEMINI_API_URL = "https://makersuite.google.com/app/apikey"

# Headers for requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}