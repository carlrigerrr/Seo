"""
AI Module - Handles Gemini AI integration and competitor finding
Updated for Gemini 2.0 Flash with API key rotation
"""

import json
import re
import time
from urllib.parse import urlparse
import threading
import os

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

try:
    from googlesearch import search
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
    search = None

import tldextract
from .utils import get_domain_from_url

class AIModule:
    def __init__(self):
        self.gemini_models = []
        self.current_key_index = 0
        self.is_initialized = False
        self.keys_file = "gemini_keys.json"
        self.api_keys = []
        self.load_saved_keys()
        
    def load_saved_keys(self):
        """Load saved API keys from file"""
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r') as f:
                    data = json.load(f)
                    self.api_keys = data.get('keys', [])
                    return self.api_keys
        except Exception as e:
            print(f"Error loading saved keys: {e}")
        return []
    
    def save_keys(self, keys):
        """Save API keys to file"""
        try:
            with open(self.keys_file, 'w') as f:
                json.dump({'keys': keys}, f)
            return True
        except Exception as e:
            print(f"Error saving keys: {e}")
            return False
    
    def add_key(self, api_key):
        """Add a new API key"""
        if api_key and api_key not in self.api_keys:
            self.api_keys.append(api_key)
            self.save_keys(self.api_keys)
            return True
        return False
    
    def remove_key(self, api_key):
        """Remove an API key"""
        if api_key in self.api_keys:
            self.api_keys.remove(api_key)
            self.save_keys(self.api_keys)
            return True
        return False
    
    def test_key(self, api_key):
        """Test if an API key is valid"""
        if not GEMINI_AVAILABLE:
            return False, "google-generativeai library not installed"
        
        try:
            # Configure with test key
            genai.configure(api_key=api_key)
            
            # Try to create model and generate simple content
            model = genai.GenerativeModel('gemini-2.0-flash-latest')
            response = model.generate_content("Say 'Hello'")
            
            # If we get here, key is valid
            return True, "API key is valid!"
            
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg:
                return False, "Invalid API key"
            elif "RATE_LIMIT_EXCEEDED" in error_msg:
                return False, "Rate limit exceeded for this key"
            else:
                return False, f"Error: {error_msg}"
    
    def initialize(self, primary_key=None):
        """Initialize Gemini with API key(s)"""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai library not installed")
        
        # Add primary key if provided
        if primary_key and primary_key not in self.api_keys:
            self.api_keys.insert(0, primary_key)
            self.save_keys(self.api_keys)
        
        if not self.api_keys:
            raise ValueError("No API keys available")
        
        # Initialize models for all keys
        self.gemini_models = []
        valid_keys = []
        
        for key in self.api_keys:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-2.0-flash-latest')
                # Test the model
                test_response = model.generate_content("Test")
                self.gemini_models.append(model)
                valid_keys.append(key)
            except Exception as e:
                print(f"Failed to initialize key: {str(e)}")
        
        if not self.gemini_models:
            raise Exception("No valid API keys could be initialized")
        
        # Update keys list with only valid ones
        self.api_keys = valid_keys
        self.save_keys(self.api_keys)
        self.current_key_index = 0
        self.is_initialized = True
        return True
    
    def get_current_model(self):
        """Get current model, rotate if needed"""
        if not self.is_initialized or not self.gemini_models:
            return None
        
        return self.gemini_models[self.current_key_index]
    
    def rotate_key(self):
        """Rotate to next API key"""
        if len(self.gemini_models) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.gemini_models)
            print(f"Rotated to API key index: {self.current_key_index}")
            return True
        return False
    
    def generate_with_retry(self, prompt, max_retries=3):
        """Generate content with automatic key rotation on rate limit"""
        if not self.is_initialized:
            return None
        
        retries = 0
        keys_tried = 0
        
        while retries < max_retries and keys_tried < len(self.gemini_models):
            try:
                model = self.get_current_model()
                if not model:
                    return None
                
                response = model.generate_content(prompt)
                return response
                
            except Exception as e:
                error_msg = str(e)
                print(f"Generation error: {error_msg}")
                
                if "RATE_LIMIT_EXCEEDED" in error_msg or "429" in error_msg:
                    # Try rotating to next key
                    if self.rotate_key():
                        keys_tried += 1
                        continue
                    else:
                        # No more keys to try
                        raise Exception("All API keys have hit rate limits")
                else:
                    # Other error, retry with same key
                    retries += 1
                    if retries < max_retries:
                        time.sleep(2 ** retries)  # Exponential backoff
                    else:
                        raise e
        
        return None
    
    def find_competitors_async(self, website_url, callback=None):
        """Find competitors asynchronously to avoid UI freezing"""
        def _find():
            try:
                competitors = self.find_competitors_with_gemini(website_url)
                if callback:
                    callback(website_url, competitors)
            except Exception as e:
                print(f"Error finding competitors: {e}")
                if callback:
                    callback(website_url, self.find_competitors_fallback(website_url))
        
        thread = threading.Thread(target=_find, daemon=True)
        thread.start()
        return thread
    
    def find_competitors_with_gemini(self, website_url):
        """Use Gemini AI to find the best competitors"""
        if not self.is_initialized:
            return self.find_competitors_fallback(website_url)
        
        try:
            domain = urlparse(website_url).netloc
            
            prompt = f"""Analyze the website {website_url} and identify its top 3 direct competitors.

IMPORTANT: Return ONLY a JSON object with no markdown formatting, no backticks, no explanations.
The response must be EXACTLY in this format:

{{"competitors": [
  {{"url": "https://competitor1.com", "reason": "Brief reason why they compete"}},
  {{"url": "https://competitor2.com", "reason": "Brief reason why they compete"}},
  {{"url": "https://competitor3.com", "reason": "Brief reason why they compete"}}
]}}

Focus on:
1. Companies in the same industry/niche
2. Similar target audience
3. Competing for same keywords/services
4. Similar business model

Return ONLY the JSON object, nothing else."""

            response = self.generate_with_retry(prompt)
            if not response:
                return self.find_competitors_fallback(website_url)
            
            # Clean response text
            response_text = response.text.strip()
            # Remove any markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            
            # Parse JSON
            try:
                data = json.loads(response_text)
                competitors = []
                
                for comp in data.get('competitors', []):
                    url = comp.get('url', '')
                    if url:
                        # Ensure URL has protocol
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        competitors.append(url)
                
                return competitors[:3]  # Return top 3
                
            except json.JSONDecodeError:
                print(f"Failed to parse Gemini response as JSON: {response_text}")
                return self.find_competitors_fallback(website_url)
                
        except Exception as e:
            print(f"Gemini competitor finding error: {str(e)}")
            return self.find_competitors_fallback(website_url)
    
    def find_competitors_fallback(self, domain):
        """Fallback method using Google search if Gemini fails"""
        if not GOOGLE_SEARCH_AVAILABLE:
            return []
            
        competitors = []
        
        try:
            # Extract domain info
            ext = tldextract.extract(domain)
            domain_name = ext.domain
            
            # Search queries
            search_queries = [
                f"{domain_name} competitors",
                f"sites like {domain_name}",
                f"{domain_name} alternatives"
            ]
            
            found_domains = set()
            
            for query in search_queries[:2]:
                try:
                    search_results = search(query, num=10, stop=10, pause=2)
                    
                    for result in search_results:
                        result_ext = tldextract.extract(result)
                        result_domain = f"{result_ext.domain}.{result_ext.suffix}"
                        
                        if (result_domain != f"{ext.domain}.{ext.suffix}" and 
                            result_domain not in found_domains and
                            result_ext.domain and result_ext.suffix):
                            
                            found_domains.add(result_domain)
                            competitors.append(f"https://{result_domain}")
                            
                            if len(competitors) >= 3:
                                break
                    
                    if len(competitors) >= 3:
                        break
                        
                except Exception as e:
                    print(f"Search error: {str(e)}")
                    
                time.sleep(2)
            
        except Exception as e:
            print(f"Competitor finding error: {str(e)}")
        
        return competitors[:3]
    
    def generate_outreach_message_async(self, main_site_data, competitor_data, callback=None):
        """Generate outreach message asynchronously"""
        def _generate():
            try:
                message = self.generate_outreach_message(main_site_data, competitor_data)
                if callback:
                    callback(main_site_data['url'], message)
            except Exception as e:
                print(f"Error generating outreach: {e}")
                if callback:
                    fallback = self.generate_fallback_outreach(main_site_data, competitor_data)
                    callback(main_site_data['url'], fallback)
        
        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()
        return thread
    
    def generate_outreach_message(self, main_site_data, competitor_data):
        """Generate personalized outreach message using Gemini"""
        if not self.is_initialized:
            return self.generate_fallback_outreach(main_site_data, competitor_data)
        
        try:
            # Prepare data summary
            main_score = main_site_data.get('seo_score', 0)
            main_issues = main_site_data.get('issues', [])
            main_url = main_site_data.get('url', '')
            
            # Competitor summary
            comp_scores = [c.get('seo_score', 0) for c in competitor_data if not c.get('error')]
            avg_comp_score = sum(comp_scores) / len(comp_scores) if comp_scores else 0
            
            # Find competitive advantages/disadvantages
            advantages = []
            disadvantages = []
            
            for comp in competitor_data:
                if comp.get('seo_score', 0) > main_score:
                    disadvantages.append({
                        'competitor': urlparse(comp['url']).netloc,
                        'score_diff': comp.get('seo_score', 0) - main_score,
                        'their_advantages': [
                            issue for issue in main_issues 
                            if issue not in comp.get('issues', [])
                        ][:3]
                    })
            
            prompt = f"""Create a brief, personalized outreach message for {main_url} based on this SEO analysis data.

Website Analysis:
- SEO Score: {main_score}/100
- Average Competitor Score: {avg_comp_score:.0f}/100
- Main Issues: {', '.join(main_issues[:5])}
- Total Issues Found: {len(main_issues)}

Competitor Advantages:
{json.dumps(disadvantages, indent=2)}

Create a SHORT (max 150 words), direct outreach message that:
1. Opens with their specific competitive disadvantage (if any)
2. Mentions 1-2 specific issues hurting their ranking
3. Quantifies potential impact (traffic/revenue increase)
4. Ends with a clear call to action

Be specific, data-driven, and avoid generic marketing fluff. Write as if you're a helpful expert, not a salesperson.

IMPORTANT: Return ONLY the message text, no explanations or formatting."""

            response = self.generate_with_retry(prompt)
            if not response:
                return self.generate_fallback_outreach(main_site_data, competitor_data)
                
            return response.text.strip()
            
        except Exception as e:
            print(f"Outreach generation error: {str(e)}")
            return self.generate_fallback_outreach(main_site_data, competitor_data)
    
    def generate_fallback_outreach(self, main_site_data, competitor_data):
        """Generate template-based outreach if Gemini fails"""
        main_score = main_site_data.get('seo_score', 0)
        main_issues = main_site_data.get('issues', [])
        domain = urlparse(main_site_data.get('url', '')).netloc
        
        comp_scores = [c.get('seo_score', 0) for c in competitor_data if not c.get('error')]
        avg_comp_score = sum(comp_scores) / len(comp_scores) if comp_scores else 0
        
        if main_score < avg_comp_score:
            opening = f"Your competitors are outranking {domain} with {avg_comp_score - main_score:.0f} points higher SEO scores."
        else:
            opening = f"While {domain} performs well, there are opportunities to extend your lead."
        
        issues_text = f"Key issues: {', '.join(main_issues[:2])}" if main_issues else "Several technical improvements needed"
        
        message = f"""{opening} {issues_text}. 
Our analysis shows fixing these could increase organic traffic by 25-40% within 3 months. 
Interested in seeing the full competitive analysis report?"""
        
        return message