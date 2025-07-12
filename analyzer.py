"""
SEO Analysis Engine - Core analysis functionality
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urlparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import textstat

from .config import (
    DEFAULT_HEADERS, BLACKLIST_DOMAINS, BLACKLIST_EMAIL_PATTERNS,
    BUSINESS_EMAIL_KEYWORDS, SOCIAL_PATTERNS, PAGESPEED_API_URL
)
from .utils import (
    clean_text_content, filter_business_emails, safe_get_dict_value,
    format_timestamp, retry_on_failure
)

class SEOAnalyzer:
    def __init__(self):
        self.pagespeed_api_key = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def analyze_website_async(self, url, callback=None):
        """Analyze website asynchronously"""
        def _analyze():
            try:
                result = self.analyze_website(url)
                if callback:
                    callback(result)
            except Exception as e:
                error_result = {
                    'url': url,
                    'error': str(e),
                    'timestamp': format_timestamp(),
                    'seo_score': 0,
                    'issues': [f"Analysis error: {str(e)}"]
                }
                if callback:
                    callback(error_result)
        
        thread = threading.Thread(target=_analyze, daemon=True)
        thread.start()
        return thread
    
    def analyze_website(self, url):
        """Enhanced website analysis with more features"""
        result = {
            'url': url,
            'timestamp': format_timestamp(),
            'basic_info': {},
            'seo_analysis': {},
            'technical_seo': {},
            'content_quality': {},
            'open_graph': {},
            'emails': [],
            'social_media': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Fetch the page
            start_time = time.time()
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30, allow_redirects=True)
            load_time = time.time() - start_time
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Basic info
            result['basic_info'] = self._analyze_basic_info(response, load_time)
            
            # SEO Analysis
            result['seo_analysis'] = self._analyze_seo(soup)
            
            # Check for SEO issues
            self._check_seo_issues(result)
            
            # Technical SEO
            result['technical_seo'] = self._analyze_technical_seo(soup, url, response)
            
            # Content quality analysis
            text_content = clean_text_content(soup)
            result['content_quality'] = self._analyze_content_quality(text_content)
            
            # Open Graph tags
            result['open_graph'] = self._extract_open_graph(soup)
            
            # Find emails
            result['emails'] = self._extract_emails(response.text)
            
            # Find social media links
            result['social_media'] = self._extract_social_media(response.text)
            
            # Check for important files
            self._check_important_files(url, result)
            
            # Calculate SEO score
            result['seo_score'], result['score_breakdown'] = self.calculate_seo_score(result)
            
        except requests.exceptions.Timeout:
            result['error'] = "Website took too long to respond"
            result['issues'].append("Timeout error")
            result['seo_score'] = 0
        except requests.exceptions.ConnectionError:
            result['error'] = "Could not connect to website"
            result['issues'].append("Connection error")
            result['seo_score'] = 0
        except Exception as e:
            result['error'] = str(e)
            result['issues'].append(f"Analysis error: {str(e)}")
            result['seo_score'] = 0
        
        return result
    
    def _analyze_basic_info(self, response, load_time):
        """Analyze basic website information"""
        return {
            'status_code': response.status_code,
            'load_time': f"{load_time:.2f}s",
            'load_time_score': 100 if load_time < 1 else 80 if load_time < 3 else 50 if load_time < 5 else 20,
            'final_url': response.url,
            'redirects': len(response.history),
            'page_size': f"{len(response.content) / 1024:.1f} KB",
            'encoding': response.encoding
        }
    
    def _analyze_seo(self, soup):
        """Analyze SEO elements"""
        title = soup.find('title')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        robots = soup.find('meta', attrs={'name': 'robots'})
        
        # Header analysis
        headers_count = {
            f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)
        }
        
        # Get H1 text
        h1_tags = soup.find_all('h1')
        h1_text = [h1.text.strip() for h1 in h1_tags[:3]]
        
        # Image analysis
        images = soup.find_all('img')
        images_without_alt = [img for img in images if not img.get('alt')]
        large_images = [img for img in images if img.get('src') and not img.get('loading') == 'lazy']
        
        # Schema markup check
        schema_types = self._check_schema_markup(soup)
        
        return {
            'title': title.text.strip() if title else None,
            'title_length': len(title.text.strip()) if title else 0,
            'meta_description': meta_desc.get('content', '').strip() if meta_desc else None,
            'meta_desc_length': len(meta_desc.get('content', '').strip()) if meta_desc else 0,
            'meta_keywords': meta_keywords.get('content', '').strip() if meta_keywords else None,
            'canonical_url': canonical.get('href', '') if canonical else None,
            'robots_meta': robots.get('content', '') if robots else None,
            'headers': headers_count,
            'h1_text': h1_text,
            'images': {
                'total': len(images),
                'without_alt': len(images_without_alt),
                'without_lazy_loading': len(large_images)
            },
            'schema_types': schema_types,
            'has_schema': len(schema_types) > 0
        }
    
    def _check_seo_issues(self, result):
        """Check for SEO issues and add recommendations"""
        seo = result['seo_analysis']
        issues = result['issues']
        recommendations = result['recommendations']
        
        # Title checks
        if not seo.get('title'):
            issues.append("Missing title tag")
            recommendations.append("Add a unique, descriptive title tag (30-60 characters)")
        elif seo['title_length'] < 30:
            issues.append("Title too short (< 30 chars)")
            recommendations.append("Expand title to 30-60 characters with relevant keywords")
        elif seo['title_length'] > 60:
            issues.append("Title too long (> 60 chars)")
            recommendations.append("Shorten title to under 60 characters")
        
        # Meta description checks
        if not seo.get('meta_description'):
            issues.append("Missing meta description")
            recommendations.append("Add a compelling meta description (120-160 characters)")
        elif seo['meta_desc_length'] < 120:
            issues.append("Meta description too short (< 120 chars)")
            recommendations.append("Expand meta description to 120-160 characters")
        elif seo['meta_desc_length'] > 160:
            issues.append("Meta description too long (> 160 chars)")
            recommendations.append("Shorten meta description to under 160 characters")
        
        # Header checks
        h1_count = seo['headers'].get('h1', 0)
        if h1_count == 0:
            issues.append("Missing H1 tag")
            recommendations.append("Add one H1 tag with main keyword")
        elif h1_count > 1:
            issues.append(f"Multiple H1 tags ({h1_count})")
            recommendations.append("Use only one H1 tag per page")
        
        # Image checks
        if seo['images']['without_alt'] > 0:
            issues.append(f"{seo['images']['without_alt']} images missing alt text")
            recommendations.append("Add descriptive alt text to all images")
        
        if seo['images']['without_lazy_loading'] > 5:
            recommendations.append("Implement lazy loading for images")
        
        # Schema markup
        if not seo.get('has_schema'):
            recommendations.append("Add Schema.org structured data")
        
        # Open Graph
        if not result.get('open_graph'):
            recommendations.append("Add Open Graph tags for better social sharing")
    
    def _analyze_technical_seo(self, soup, url, response):
        """Analyze technical SEO aspects"""
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        lang = soup.find('html').get('lang') if soup.find('html') else None
        charset = soup.find('meta', charset=True)
        
        tech_seo = {
            'viewport': viewport.get('content') if viewport else None,
            'lang_attribute': lang,
            'charset': charset.get('charset') if charset else None,
            'https': url.startswith('https://'),
            'www_redirect': 'www.' in response.url
        }
        
        # Add issues for technical SEO
        if not viewport:
            result['issues'].append("Missing viewport meta tag (not mobile-friendly)")
            result['recommendations'].append("Add viewport meta tag for mobile responsiveness")
        
        if not lang:
            result['issues'].append("Missing language attribute")
            result['recommendations'].append("Add lang attribute to html tag")
        
        if not url.startswith('https://'):
            result['issues'].append("Not using HTTPS")
            result['recommendations'].append("Implement SSL certificate for HTTPS")
        
        return tech_seo
    
    def _analyze_content_quality(self, text_content):
        """Analyze content quality and readability"""
        try:
            word_count = len(text_content.split())
            
            if word_count > 50:
                return {
                    'word_count': word_count,
                    'flesch_reading_ease': textstat.flesch_reading_ease(text_content),
                    'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text_content),
                    'smog_index': textstat.smog_index(text_content),
                    'automated_readability_index': textstat.automated_readability_index(text_content),
                    'syllable_count': textstat.syllable_count(text_content)
                }
            else:
                return {'word_count': word_count, 'error': 'Not enough content for analysis'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _check_schema_markup(self, soup):
        """Check for Schema.org structured data"""
        schema_types = []
        
        # Check for JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    schema_types.append(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            schema_types.append(item['@type'])
            except:
                pass
        
        # Check for Microdata
        microdata_items = soup.find_all(attrs={'itemtype': True})
        for item in microdata_items:
            schema_type = item.get('itemtype', '').split('/')[-1]
            if schema_type:
                schema_types.append(schema_type)
        
        return list(set(schema_types))
    
    def _extract_open_graph(self, soup):
        """Extract Open Graph tags"""
        og_tags = {}
        for tag in soup.find_all('meta', property=re.compile(r'^og:')):
            og_tags[tag.get('property')] = tag.get('content')
        return og_tags
    
    def _extract_emails(self, html_content):
        """Extract and filter business emails"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = list(set(re.findall(email_pattern, html_content)))
        
        # Filter emails
        filtered_emails = filter_business_emails(emails, BLACKLIST_DOMAINS, BLACKLIST_EMAIL_PATTERNS)
        
        # Prioritize business emails
        filtered_emails.sort(key=lambda x: any(keyword in x.lower() for keyword in BUSINESS_EMAIL_KEYWORDS), reverse=True)
        
        return filtered_emails[:10]  # Limit to top 10
    
    def _extract_social_media(self, html_content):
        """Extract social media links"""
        social_media = {}
        
        for platform, pattern in SOCIAL_PATTERNS.items():
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                # Clean up the URL
                match = matches[0]
                if not match.startswith(('http://', 'https://')):
                    match = 'https:' + match if match.startswith('//') else 'https://' + match
                social_media[platform] = match
        
        return social_media
    
    def _check_important_files(self, url, result):
        """Check for robots.txt and sitemap.xml"""
        domain = urlparse(url).scheme + '://' + urlparse(url).netloc
        
        try:
            robots_response = requests.get(domain + '/robots.txt', headers=DEFAULT_HEADERS, timeout=10)
            result['technical_seo']['robots_txt'] = robots_response.status_code == 200
        except:
            result['technical_seo']['robots_txt'] = False
        
        try:
            sitemap_response = requests.get(domain + '/sitemap.xml', headers=DEFAULT_HEADERS, timeout=10)
            result['technical_seo']['sitemap_xml'] = sitemap_response.status_code == 200
        except:
            result['technical_seo']['sitemap_xml'] = False
        
        if not result['technical_seo']['robots_txt']:
            result['issues'].append("No robots.txt file found")
            result['recommendations'].append("Create robots.txt file")
        
        if not result['technical_seo']['sitemap_xml']:
            result['issues'].append("No sitemap.xml file found")
            result['recommendations'].append("Create XML sitemap")
    
    def calculate_seo_score(self, result):
        """Calculate overall SEO score based on various factors"""
        score = 100  # Start with perfect score
        penalties = []
        
        # Title penalties
        if not result['seo_analysis'].get('title'):
            score -= 15
            penalties.append(("Missing title tag", -15))
        elif result['seo_analysis']['title_length'] < 30:
            score -= 5
            penalties.append(("Title too short", -5))
        elif result['seo_analysis']['title_length'] > 60:
            score -= 5
            penalties.append(("Title too long", -5))
        
        # Meta description penalties
        if not result['seo_analysis'].get('meta_description'):
            score -= 10
            penalties.append(("Missing meta description", -10))
        elif result['seo_analysis']['meta_desc_length'] < 120:
            score -= 5
            penalties.append(("Meta description too short", -5))
        elif result['seo_analysis']['meta_desc_length'] > 160:
            score -= 5
            penalties.append(("Meta description too long", -5))
        
        # H1 penalties
        h1_count = result['seo_analysis']['headers'].get('h1', 0)
        if h1_count == 0:
            score -= 10
            penalties.append(("Missing H1 tag", -10))
        elif h1_count > 1:
            score -= 5
            penalties.append(("Multiple H1 tags", -5))
        
        # Image alt text penalties
        if result['seo_analysis']['images']['without_alt'] > 0:
            penalty = min(10, result['seo_analysis']['images']['without_alt'] * 2)
            score -= penalty
            penalties.append((f"{result['seo_analysis']['images']['without_alt']} images without alt text", -penalty))
        
        # Technical SEO penalties
        if not result['technical_seo'].get('https'):
            score -= 10
            penalties.append(("Not using HTTPS", -10))
        
        if not result['technical_seo'].get('viewport'):
            score -= 10
            penalties.append(("Not mobile-friendly", -10))
        
        if not result['technical_seo'].get('robots_txt'):
            score -= 5
            penalties.append(("Missing robots.txt", -5))
        
        if not result['technical_seo'].get('sitemap_xml'):
            score -= 5
            penalties.append(("Missing sitemap.xml", -5))
        
        # Performance penalties
        if result.get('basic_info', {}).get('load_time_score', 100) < 50:
            score -= 10
            penalties.append(("Slow load time", -10))
        
        # Schema markup bonus
        if result.get('seo_analysis', {}).get('has_schema'):
            score = min(100, score + 5)  # Bonus points
            penalties.append(("Has Schema markup", +5))
        
        return max(0, score), penalties
    
    def get_performance_insights_async(self, url, callback=None):
        """Get performance insights asynchronously"""
        def _get_insights():
            try:
                insights = self.get_performance_insights(url)
                if callback:
                    callback(url, insights)
            except Exception as e:
                print(f"Performance insights error: {e}")
                if callback:
                    callback(url, {})
        
        thread = threading.Thread(target=_get_insights, daemon=True)
        thread.start()
        return thread
    
    def get_performance_insights(self, url):
        """Get performance insights using Google PageSpeed Insights API"""
        try:
            params = {
                'url': url,
                'category': ['performance', 'seo', 'accessibility'],
                'strategy': 'mobile'  # Mobile-first
            }
            
            if self.pagespeed_api_key:
                params['key'] = self.pagespeed_api_key
            
            response = requests.get(PAGESPEED_API_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract scores
                lighthouse = data.get('lighthouseResult', {})
                categories = lighthouse.get('categories', {})
                
                return {
                    'performance_score': int(categories.get('performance', {}).get('score', 0) * 100),
                    'seo_score': int(categories.get('seo', {}).get('score', 0) * 100),
                    'accessibility_score': int(categories.get('accessibility', {}).get('score', 0) * 100),
                    'metrics': {
                        'first_contentful_paint': lighthouse.get('audits', {}).get('first-contentful-paint', {}).get('displayValue', 'N/A'),
                        'speed_index': lighthouse.get('audits', {}).get('speed-index', {}).get('displayValue', 'N/A'),
                        'time_to_interactive': lighthouse.get('audits', {}).get('interactive', {}).get('displayValue', 'N/A'),
                        'total_blocking_time': lighthouse.get('audits', {}).get('total-blocking-time', {}).get('displayValue', 'N/A')
                    }
                }
            else:
                # Fallback to basic performance calculation
                return self._basic_performance_test(url)
                
        except Exception as e:
            return self._basic_performance_test(url)
    
    def _basic_performance_test(self, url):
        """Basic performance test when PageSpeed API is not available"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=30)
            load_time = time.time() - start_time
            
            # Basic scoring based on load time
            if load_time < 1:
                performance_score = 90
            elif load_time < 3:
                performance_score = 70
            elif load_time < 5:
                performance_score = 50
            else:
                performance_score = 30
            
            return {
                'performance_score': performance_score,
                'seo_score': 0,
                'accessibility_score': 0,
                'metrics': {
                    'load_time': f"{load_time:.2f}s",
                    'page_size': f"{len(response.content) / 1024:.1f} KB"
                }
            }
        except:
            return {}