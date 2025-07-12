"""
Main Application Module - UI and orchestration
Updated with API key management features
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import os
import time
from urllib.parse import urlparse

from .config import *
from .utils import *
from .analyzer import SEOAnalyzer
from .ai_module import AIModule
from .screenshot import ScreenshotModule
from .export_module import ExportModule
from .ui_components import UIComponents

class SEOAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry(WINDOW_SIZE)
        
        # Set modern theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.websites = []
        self.results = []
        self.current_index = 0
        self.is_analyzing = False
        self.include_screenshots = tk.BooleanVar(value=True)
        self.include_competitors = tk.BooleanVar(value=True)
        self.generate_outreach = tk.BooleanVar(value=True)
        
        # API Keys
        self.gemini_api_key = tk.StringVar(value="")
        self.pagespeed_api_key = "YOUR_API_KEY"  # Optional
        
        # Modules
        self.analyzer = SEOAnalyzer()
        self.ai_module = AIModule()
        self.screenshot_module = ScreenshotModule()
        self.export_module = ExportModule()
        self.ui = UIComponents(self)
        
        # Thread management
        self.analysis_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.outreach_messages = {}
        self.competitor_map = {}
        
        # Setup UI
        self.setup_ui()
        
        # Load saved keys
        self.load_saved_keys()
        
        # Start result processor
        self.process_results()
        
    def load_saved_keys(self):
        """Load saved API keys on startup"""
        saved_keys = self.ai_module.load_saved_keys()
        if saved_keys:
            # Set the first key as primary
            self.gemini_api_key.set(saved_keys[0])
            self.update_key_status(f"Loaded {len(saved_keys)} saved key(s)")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header
        self.ui.create_header(main_frame)
        
        # Input section
        input_frame = self.ui.create_input_section(main_frame)
        self.setup_input_section(input_frame)
        
        # Results section
        self.results_notebook = self.ui.create_results_section(main_frame)
        self.setup_results_tabs()
        
        # Export buttons
        self.ui.create_export_section(main_frame, self)
        
    def setup_input_section(self, input_frame):
        """Setup input section with all controls"""
        # API Key Management Frame
        api_frame = ttk.LabelFrame(input_frame, text="API Key Management", padding="10")
        api_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)
        
        # Current key input
        ttk.Label(api_frame, text="Current Key:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.gemini_api_key, show="*", width=50)
        self.api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Key management buttons
        key_buttons_frame = ttk.Frame(api_frame)
        key_buttons_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        tk.Button(key_buttons_frame, text="💾 Save Key", 
                 command=self.save_api_key,
                 bg=COLORS['success'], fg="white", font=("Arial", 9),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(key_buttons_frame, text="🧪 Test Key", 
                 command=self.test_api_key,
                 bg=COLORS['info'], fg="white", font=("Arial", 9),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(key_buttons_frame, text="🔄 Manage Keys", 
                 command=self.open_key_manager,
                 bg=COLORS['warning'], fg="white", font=("Arial", 9),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(key_buttons_frame, text="👁️ Show/Hide", 
                 command=self.toggle_key_visibility,
                 bg=COLORS['secondary'], fg="white", font=("Arial", 9),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.key_status_label = ttk.Label(api_frame, text="", font=("Arial", 9, "italic"))
        self.key_status_label.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Instructions
        instructions = ttk.Label(input_frame, 
                               text="Enter websites to analyze (one per line). AI will find the best competitors!",
                               font=("Arial", 10))
        instructions.grid(row=1, column=0, sticky=tk.W, columnspan=2)
        
        # Website input area
        self.website_text = scrolledtext.ScrolledText(input_frame, height=5, width=50, 
                                                     font=("Consolas", 10))
        self.website_text.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0), columnspan=2)
        self.website_text.insert("1.0", "example.com")
        
        # Options frame
        options_frame = ttk.Frame(input_frame)
        options_frame.grid(row=3, column=0, pady=(10, 0), sticky=tk.W)
        
        # Checkboxes for features
        ttk.Checkbutton(options_frame, text="📸 Capture Screenshots", 
                       variable=self.include_screenshots).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="🤖 AI Competitor Analysis", 
                       variable=self.include_competitors).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="✉️ Generate Outreach Messages", 
                       variable=self.generate_outreach).pack(side=tk.LEFT, padx=10)
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, pady=(10, 0))
        
        self.analyze_button = tk.Button(button_frame, text="🚀 Start AI Analysis", 
                                       command=self.start_analysis,
                                       bg=COLORS['success'], fg="white", font=("Arial", 12, "bold"),
                                       padx=20, pady=10, relief=tk.FLAT)
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="🗑️ Clear", 
                 command=lambda: self.website_text.delete("1.0", tk.END),
                 bg=COLORS['danger'], fg="white", font=("Arial", 10),
                 padx=15, pady=8, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="📁 Load File", 
                 command=self.load_from_file,
                 bg=COLORS['info'], fg="white", font=("Arial", 10),
                 padx=15, pady=8, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready to analyze")
        progress_label = tk.Label(input_frame, textvariable=self.progress_var,
                                 font=("Arial", 11, "italic"), fg="#7F8C8D")
        progress_label.grid(row=5, column=0, pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(input_frame, mode='determinate',
                                           style="green.Horizontal.TProgressbar")
        self.progress_bar.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def save_api_key(self):
        """Save the current API key"""
        key = self.gemini_api_key.get().strip()
        if not key:
            messagebox.showwarning("Warning", "Please enter an API key")
            return
        
        if self.ai_module.add_key(key):
            self.update_key_status("✅ Key saved successfully!")
            messagebox.showinfo("Success", "API key saved successfully!")
        else:
            self.update_key_status("Key already exists")
    
    def test_api_key(self):
        """Test the current API key"""
        key = self.gemini_api_key.get().strip()
        if not key:
            messagebox.showwarning("Warning", "Please enter an API key to test")
            return
        
        self.update_key_status("Testing key...")
        
        # Test in background thread
        def test():
            valid, message = self.ai_module.test_key(key)
            self.root.after(0, lambda: self.show_test_result(valid, message))
        
        thread = threading.Thread(target=test, daemon=True)
        thread.start()
    
    def show_test_result(self, valid, message):
        """Show API key test result"""
        if valid:
            self.update_key_status(f"✅ {message}")
            messagebox.showinfo("Test Result", message)
        else:
            self.update_key_status(f"❌ {message}")
            messagebox.showerror("Test Result", message)
    
    def toggle_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_entry['show'] == '*':
            self.api_key_entry.config(show='')
        else:
            self.api_key_entry.config(show='*')
    
    def update_key_status(self, message):
        """Update key status label"""
        self.key_status_label.config(text=message)
    
    def open_key_manager(self):
        """Open API key manager window"""
        manager_window = tk.Toplevel(self.root)
        manager_window.title("API Key Manager")
        manager_window.geometry("600x400")
        
        # Header
        header = tk.Label(manager_window, text="Manage API Keys", 
                         font=("Arial", 16, "bold"), bg=COLORS['primary'], fg="white")
        header.pack(fill=tk.X, pady=(0, 10))
        
        # Info label
        info = tk.Label(manager_window, 
                       text="Add multiple keys for automatic rotation when rate limits are reached",
                       font=("Arial", 10, "italic"))
        info.pack(pady=5)
        
        # Keys listbox
        list_frame = ttk.Frame(manager_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.keys_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                      font=("Consolas", 10), height=10)
        self.keys_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.keys_listbox.yview)
        
        # Load current keys
        self.refresh_keys_list()
        
        # Buttons
        button_frame = ttk.Frame(manager_window)
        button_frame.pack(pady=10)
        
        # Add key frame
        add_frame = ttk.Frame(button_frame)
        add_frame.pack(pady=5)
        
        self.new_key_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_key_var, width=40, show="*").pack(side=tk.LEFT, padx=5)
        
        tk.Button(add_frame, text="➕ Add Key", 
                 command=lambda: self.add_key_from_manager(),
                 bg=COLORS['success'], fg="white", font=("Arial", 9),
                 padx=10, pady=5, relief=tk.FLAT).pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = ttk.Frame(button_frame)
        action_frame.pack(pady=5)
        
        tk.Button(action_frame, text="🧪 Test Selected", 
                 command=self.test_selected_key,
                 bg=COLORS['info'], fg="white", font=("Arial", 9),
                 padx=10, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(action_frame, text="🗑️ Remove Selected", 
                 command=self.remove_selected_key,
                 bg=COLORS['danger'], fg="white", font=("Arial", 9),
                 padx=10, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(action_frame, text="📋 Use Selected", 
                 command=self.use_selected_key,
                 bg=COLORS['warning'], fg="white", font=("Arial", 9),
                 padx=10, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.manager_status = tk.Label(manager_window, text="", font=("Arial", 9, "italic"))
        self.manager_status.pack(pady=5)
        
        # Close button
        tk.Button(manager_window, text="Close", command=manager_window.destroy,
                 bg=COLORS['secondary'], fg="white", font=("Arial", 10),
                 padx=20, pady=8, relief=tk.FLAT).pack(pady=10)
    
    def refresh_keys_list(self):
        """Refresh the keys listbox"""
        self.keys_listbox.delete(0, tk.END)
        for i, key in enumerate(self.ai_module.api_keys):
            # Show masked key
            masked_key = key[:10] + "..." + key[-10:] if len(key) > 25 else key
            self.keys_listbox.insert(tk.END, f"Key {i+1}: {masked_key}")
    
    def add_key_from_manager(self):
        """Add key from manager window"""
        key = self.new_key_var.get().strip()
        if not key:
            self.manager_status.config(text="Please enter a key", fg=COLORS['danger'])
            return
        
        if self.ai_module.add_key(key):
            self.refresh_keys_list()
            self.new_key_var.set("")
            self.manager_status.config(text="✅ Key added successfully", fg=COLORS['success'])
        else:
            self.manager_status.config(text="Key already exists", fg=COLORS['warning'])
    
    def test_selected_key(self):
        """Test selected key from list"""
        selection = self.keys_listbox.curselection()
        if not selection:
            self.manager_status.config(text="Please select a key", fg=COLORS['warning'])
            return
        
        key_index = selection[0]
        if key_index < len(self.ai_module.api_keys):
            key = self.ai_module.api_keys[key_index]
            self.manager_status.config(text="Testing key...", fg=COLORS['info'])
            
            def test():
                valid, message = self.ai_module.test_key(key)
                self.root.after(0, lambda: self.manager_status.config(
                    text=f"{'✅' if valid else '❌'} {message}", 
                    fg=COLORS['success'] if valid else COLORS['danger']
                ))
            
            thread = threading.Thread(target=test, daemon=True)
            thread.start()
    
    def remove_selected_key(self):
        """Remove selected key"""
        selection = self.keys_listbox.curselection()
        if not selection:
            self.manager_status.config(text="Please select a key", fg=COLORS['warning'])
            return
        
        key_index = selection[0]
        if key_index < len(self.ai_module.api_keys):
            key = self.ai_module.api_keys[key_index]
            if messagebox.askyesno("Confirm", "Remove this API key?"):
                if self.ai_module.remove_key(key):
                    self.refresh_keys_list()
                    self.manager_status.config(text="✅ Key removed", fg=COLORS['success'])
    
    def use_selected_key(self):
        """Use selected key as primary"""
        selection = self.keys_listbox.curselection()
        if not selection:
            self.manager_status.config(text="Please select a key", fg=COLORS['warning'])
            return
        
        key_index = selection[0]
        if key_index < len(self.ai_module.api_keys):
            key = self.ai_module.api_keys[key_index]
            self.gemini_api_key.set(key)
            self.manager_status.config(text="✅ Key set as primary", fg=COLORS['success'])
    
    def setup_results_tabs(self):
        """Setup all result tabs"""
        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.dashboard_frame, text="📊 Dashboard")
        self.dashboard_canvas, self.dashboard_inner = self.ui.create_scrollable_frame(self.dashboard_frame)
        
        # Competitor Comparison tab
        self.competitor_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.competitor_frame, text="🏆 Competitor Analysis")
        self.competitor_canvas, self.competitor_inner = self.ui.create_scrollable_frame(self.competitor_frame)
        
        # AI Outreach tab
        outreach_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(outreach_frame, text="✉️ AI Outreach")
        self.outreach_text = scrolledtext.ScrolledText(outreach_frame, wrap=tk.WORD, font=("Arial", 11))
        self.outreach_text.pack(fill=tk.BOTH, expand=True)
        
        # Screenshots tab
        self.screenshots_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.screenshots_frame, text="📸 Screenshots")
        self.screenshots_canvas, self.screenshots_inner = self.ui.create_scrollable_frame(self.screenshots_frame)
        
        # Detailed results tab
        details_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(details_frame, text="📋 Detailed Analysis")
        self.details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Issues & Recommendations tab
        issues_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(issues_frame, text="⚠️ Issues & Fixes")
        self.issues_text = scrolledtext.ScrolledText(issues_frame, wrap=tk.WORD, font=("Arial", 11))
        self.issues_text.pack(fill=tk.BOTH, expand=True)
        
        # Contacts tab
        contacts_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(contacts_frame, text="📧 Contacts")
        self.contacts_text = scrolledtext.ScrolledText(contacts_frame, wrap=tk.WORD, font=("Arial", 11))
        self.contacts_text.pack(fill=tk.BOTH, expand=True)
    
    def load_from_file(self):
        """Load URLs from file"""
        file_path = filedialog.askopenfilename(
            title="Select file with URLs",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    self.website_text.delete("1.0", tk.END)
                    self.website_text.insert("1.0", content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def start_analysis(self):
        """Start the analysis process"""
        if self.is_analyzing:
            messagebox.showinfo("Info", "Analysis is already running!")
            return
        
        # Validate inputs
        if not self.validate_inputs():
            return
        
        # Parse websites
        self.parse_websites()
        
        if not self.websites:
            messagebox.showwarning("Warning", "No valid websites found!")
            return
        
        # Initialize modules
        if not self.initialize_modules():
            return
        
        # Reset state
        self.reset_analysis_state()
        
        # Start analysis in background
        self.is_analyzing = True
        self.analyze_button.config(state='disabled', bg="#95A5A6")
        
        # Start analysis thread
        analysis_thread = threading.Thread(target=self.run_analysis, daemon=True)
        analysis_thread.start()
    
    def validate_inputs(self):
        """Validate user inputs"""
        # Check for Gemini API key if AI features are enabled
        if (self.include_competitors.get() or self.generate_outreach.get()):
            if not self.ai_module.api_keys and not self.gemini_api_key.get():
                response = messagebox.askyesno("Gemini API Key Required", 
                                             "AI features require a Gemini API key.\n"
                                             "Get a free key at: https://makersuite.google.com/app/apikey\n\n"
                                             "Continue without AI features?")
                if response:
                    self.include_competitors.set(False)
                    self.generate_outreach.set(False)
                else:
                    return False
        
        # Check website input
        text = self.website_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter at least one website!")
            return False
        
        return True
    
    def parse_websites(self):
        """Parse website URLs from input"""
        self.websites = []
        text = self.website_text.get("1.0", tk.END).strip()
        
        for line in text.split('\n'):
            url = line.strip()
            if url:
                url = ensure_url_protocol(url)
                if is_valid_url(url):
                    self.websites.append(url)
    
    def initialize_modules(self):
        """Initialize required modules"""
        try:
            # Initialize AI module if needed
            if self.include_competitors.get() or self.generate_outreach.get():
                primary_key = self.gemini_api_key.get() if self.gemini_api_key.get() else None
                self.ai_module.initialize(primary_key)
                self.update_key_status(f"✅ Initialized with {len(self.ai_module.api_keys)} key(s)")
            
            # Initialize screenshot module if needed
            if self.include_screenshots.get():
                try:
                    self.screenshot_module.initialize()
                except Exception as e:
                    response = messagebox.askyesno("Screenshot Error", 
                                                 f"Failed to initialize screenshots:\n{str(e)}\n\n"
                                                 "Continue without screenshots?")
                    if response:
                        self.include_screenshots.set(False)
                    else:
                        return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("Initialization Error", str(e))
            return False
    
    def reset_analysis_state(self):
        """Reset analysis state and clear results"""
        self.results = []
        self.outreach_messages = {}
        self.competitor_map = {}
        self.current_index = 0
        
        # Clear UI
        self.ui.clear_all_results(self)
        
        # Clear queues
        while not self.analysis_queue.empty():
            self.analysis_queue.get()
        while not self.results_queue.empty():
            self.results_queue.get()
    
    def run_analysis(self):
        """Run the analysis process in background"""
        try:
            all_sites = self.websites.copy()
            
            # Find competitors if enabled
            if self.include_competitors.get():
                self.update_progress("🤖 Finding competitors with AI...")
                competitors = self.find_all_competitors()
                
                # Add unique competitors to analysis list
                for site, comps in competitors.items():
                    self.competitor_map[site] = comps
                    for comp in comps:
                        if comp not in all_sites:
                            all_sites.append(comp)
            
            # Update progress bar
            self.progress_bar['maximum'] = len(all_sites)
            
            # Analyze all sites
            self.analyze_all_sites(all_sites)
            
            # Wait for all analyses to complete
            time.sleep(3)  # Give time for all analyses to finish
            
            # Generate outreach if enabled
            if self.generate_outreach.get() and self.ai_module.is_initialized:
                self.generate_all_outreach()
            
            # Complete
            self.analysis_complete()
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", str(e)))
        finally:
            self.is_analyzing = False
            self.root.after(0, lambda: self.analyze_button.config(state='normal', bg=COLORS['success']))
    
    def find_all_competitors(self):
        """Find competitors for all websites"""
        competitors = {}
        completed_count = [0]  # Use list for mutable counter
        
        def competitor_callback(site, comps):
            competitors[site] = comps
            completed_count[0] += 1
            self.update_progress(f"Found {len(comps)} competitors for {get_domain_from_url(site)} ({completed_count[0]}/{len(self.websites)})")
        
        threads = []
        for website in self.websites:
            thread = self.ai_module.find_competitors_async(website, competitor_callback)
            threads.append(thread)
        
        # Wait for all competitor finding to complete
        for thread in threads:
            thread.join(timeout=45)  # Increased timeout
        
        return competitors
    
    def analyze_all_sites(self, sites):
        """Analyze all websites"""
        completed_analyses = [0]  # Use list for mutable counter
        
        def analysis_callback(result):
            completed_analyses[0] += 1
            # Mark if it's a competitor
            if result['url'] not in self.websites:
                result['is_competitor'] = True
                # Find which main site this competitor belongs to
                for main, comps in self.competitor_map.items():
                    if result['url'] in comps:
                        result['main_site'] = main
                        break
            else:
                result['is_competitor'] = False
                result['main_site'] = result['url']
            
            self.results_queue.put(('analysis', result))
            self.update_progress(f"Analyzed {completed_analyses[0]}/{len(sites)}: {get_domain_from_url(result['url'])}")
        
        threads = []
        for site in sites:
            thread = self.analyzer.analyze_website_async(site, analysis_callback)
            threads.append(thread)
            time.sleep(0.5)  # Small delay between requests
        
        # Wait for all analyses to complete
        for thread in threads:
            thread.join(timeout=90)  # Increased timeout for website analysis
    
    def generate_all_outreach(self):
        """Generate outreach messages for all main sites"""
        self.update_progress("🤖 Generating AI outreach messages...")
        
        # Get main sites (not competitors)
        main_sites = [r for r in self.results if not r.get('is_competitor', False)]
        
        print(f"Generating outreach for {len(main_sites)} main sites")
        
        if not main_sites:
            print("No main sites found for outreach generation")
            return
        
        completed_outreach = [0]  # Use list for mutable counter
        
        def outreach_callback(url, message):
            completed_outreach[0] += 1
            self.outreach_messages[url] = message
            self.results_queue.put(('outreach', (url, message)))
            print(f"Generated outreach for {url}: {message[:50]}...")
            self.update_progress(f"Generated outreach {completed_outreach[0]}/{len(main_sites)}")
        
        threads = []
        for main_site in main_sites:
            # Find competitors for this main site
            main_url = main_site['url']
            competitors = [r for r in self.results 
                          if r.get('is_competitor', False) and r.get('main_site') == main_url]
            
            print(f"Main site: {main_url}, Competitors: {[c['url'] for c in competitors]}")
            
            # Only generate outreach if we have competitor data or the main site has issues
            if competitors or main_site.get('issues'):
                thread = self.ai_module.generate_outreach_message_async(
                    main_site, competitors, outreach_callback
                )
                threads.append(thread)
            else:
                # Generate fallback outreach
                fallback_message = self.ai_module.generate_fallback_outreach(main_site, [])
                outreach_callback(main_url, fallback_message)
        
        # Wait for all outreach generation
        for thread in threads:
            thread.join(timeout=60)  # Increased timeout
        
        print(f"Outreach generation complete. Generated {len(self.outreach_messages)} messages")
    
    def analysis_complete(self):
        """Handle analysis completion"""
        # Cleanup
        if self.screenshot_module.driver:
            self.screenshot_module.cleanup()
        
        # Update UI
        total_sites = len(self.results)
        main_sites = len([r for r in self.results if not r.get('is_competitor', False)])
        competitors = len([r for r in self.results if r.get('is_competitor', False)])
        outreach_count = len(self.outreach_messages)
        
        summary_msg = f"✅ Analysis complete! {total_sites} sites analyzed ({main_sites} main, {competitors} competitors). {outreach_count} outreach messages generated."
        self.update_progress(summary_msg)
        
        # Show summary
        self.root.after(0, self.show_analysis_summary)
    
    def update_progress(self, message):
        """Update progress message safely"""
        self.root.after(0, lambda: self.progress_var.set(message))
    
    def process_results(self):
        """Process results from queue"""
        try:
            while True:
                try:
                    result_type, data = self.results_queue.get_nowait()
                    
                    if result_type == 'analysis':
                        self.handle_analysis_result(data)
                    elif result_type == 'outreach':
                        self.handle_outreach_result(data)
                    elif result_type == 'screenshot':
                        self.handle_screenshot_result(data)
                    elif result_type == 'performance':
                        self.handle_performance_result(data)
                        
                except queue.Empty:
                    break
                    
        except Exception as e:
            print(f"Error processing results: {e}")
        
        # Schedule next check
        self.root.after(100, self.process_results)
    
    def handle_analysis_result(self, result):
        """Handle analysis result"""
        self.results.append(result)
        
        # Update progress
        self.progress_bar['value'] = len(self.results)
        
        # Get performance insights
        if not result.get('error'):
            self.analyzer.get_performance_insights_async(
                result['url'],
                lambda url, perf: self.results_queue.put(('performance', (url, perf)))
            )
        
        # Get screenshot if enabled
        if self.include_screenshots.get() and not result.get('error'):
            self.screenshot_module.capture_screenshot_async(
                result['url'],
                lambda url, screenshot: self.results_queue.put(('screenshot', (url, screenshot)))
            )
        
        # Update UI
        self.ui.update_dashboard(self, result)
        self.ui.update_results_display(self, result)
    
    def handle_outreach_result(self, data):
        """Handle outreach message result"""
        url, message = data
        print(f"Handling outreach result for {url}: {message[:50]}...")
        self.ui.update_outreach_display(self, url, message)
    
    def handle_screenshot_result(self, data):
        """Handle screenshot result"""
        url, screenshot = data
        
        # Find the result for this URL
        for result in self.results:
            if result['url'] == url:
                result['screenshot'] = screenshot
                if screenshot:
                    self.ui.update_screenshot_gallery(self, result)
                break
    
    def handle_performance_result(self, data):
        """Handle performance insights result"""
        url, performance = data
        
        # Find the result for this URL
        for result in self.results:
            if result['url'] == url:
                result['performance'] = performance
                break
    
    def show_analysis_summary(self):
        """Show analysis summary window"""
        self.ui.show_analysis_summary(self)
    
    # Export methods
    def export_to_pdf(self):
        """Export results to PDF"""
        if not self.results:
            messagebox.showwarning("Warning", "No results to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.export_module.export_to_pdf(self.results, self.outreach_messages, file_path)
                messagebox.showinfo("Success", f"PDF report generated: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
    
    def export_to_excel(self):
        """Export results to Excel"""
        if not self.results:
            messagebox.showwarning("Warning", "No results to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.export_module.export_to_excel(self.results, self.outreach_messages, file_path)
                messagebox.showinfo("Success", f"Results exported to {file_path}\n\n"
                                            "Check 'Contacts & AI Outreach' sheet for messages!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def export_to_json(self):
        """Export results to JSON"""
        if not self.results:
            messagebox.showwarning("Warning", "No results to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                metadata = {
                    'features_used': {
                        'screenshots': self.include_screenshots.get(),
                        'ai_competitor_analysis': self.include_competitors.get(),
                        'ai_outreach_generation': self.generate_outreach.get(),
                        'gemini_api_used': bool(self.ai_module.api_keys)
                    }
                }
                self.export_module.export_to_json(self.results, self.outreach_messages, 
                                                self.competitor_map, metadata, file_path)
                messagebox.showinfo("Success", f"Results exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
