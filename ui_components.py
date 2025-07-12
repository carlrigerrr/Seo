"""
UI Components Module - Handles UI creation and updates
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from urllib.parse import urlparse
from datetime import datetime

try:
    from PIL import Image as PILImage, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .config import COLORS, APP_NAME
from .utils import calculate_seo_score_color, get_domain_from_url

class UIComponents:
    def __init__(self, app):
        self.app = app
        
    def create_header(self, parent):
        """Create application header"""
        header_frame = tk.Frame(parent, bg=COLORS['primary'], height=80)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.grid_propagate(False)
        
        title_label = tk.Label(header_frame, text="Professional SEO Analyzer Pro - AI Edition", 
                              font=("Arial", 24, "bold"), fg="white", bg=COLORS['primary'])
        title_label.pack(expand=True)
        
        subtitle = tk.Label(header_frame, text="AI-Powered Competitor Analysis & Personalized Outreach Generation", 
                           font=("Arial", 12), fg="#BDC3C7", bg=COLORS['primary'])
        subtitle.pack()
        
        return header_frame
    
    def create_input_section(self, parent):
        """Create input section frame"""
        input_frame = ttk.LabelFrame(parent, text="Analysis Configuration", padding="15")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        return input_frame
    
    def create_results_section(self, parent):
        """Create results notebook"""
        results_notebook = ttk.Notebook(parent)
        results_notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        return results_notebook
    
    def create_export_section(self, parent, app):
        """Create export buttons section"""
        export_frame = ttk.Frame(parent)
        export_frame.grid(row=3, column=0, pady=(10, 0))
        
        tk.Button(export_frame, text="📄 Generate PDF Report", 
                 command=app.export_to_pdf,
                 bg=COLORS['purple'], fg="white", font=("Arial", 11, "bold"),
                 padx=20, pady=10, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(export_frame, text="📊 Export Excel + Outreach", 
                 command=app.export_to_excel,
                 bg=COLORS['turquoise'], fg="white", font=("Arial", 11, "bold"),
                 padx=15, pady=10, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(export_frame, text="💾 Export JSON", 
                 command=app.export_to_json,
                 bg=COLORS['secondary'], fg="white", font=("Arial", 11),
                 padx=15, pady=10, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        return export_frame
    
    def create_scrollable_frame(self, parent):
        """Create a scrollable frame"""
        canvas = tk.Canvas(parent, bg="white")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Update scroll region when frame changes
        def configure_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", configure_scroll)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return canvas, scrollable_frame
    
    def clear_all_results(self, app):
        """Clear all result displays"""
        # Clear dashboard
        for widget in app.dashboard_inner.winfo_children():
            widget.destroy()
        
        # Clear competitor analysis
        for widget in app.competitor_inner.winfo_children():
            widget.destroy()
        
        # Clear screenshots
        for widget in app.screenshots_inner.winfo_children():
            widget.destroy()
        
        # Clear text areas
        app.details_text.delete("1.0", tk.END)
        app.issues_text.delete("1.0", tk.END)
        app.contacts_text.delete("1.0", tk.END)
        app.outreach_text.delete("1.0", tk.END)
    
    def update_dashboard(self, app, result):
        """Update dashboard with website result"""
        # Create frame for this website
        site_frame = tk.Frame(app.dashboard_inner, bg='white', relief=tk.RAISED, bd=2)
        site_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Add competitor badge if applicable
        if result.get('is_competitor'):
            badge = tk.Label(site_frame, text="COMPETITOR", 
                           font=("Arial", 8, "bold"), bg='#E67E22', fg='white')
            badge.pack(anchor='ne', padx=5, pady=5)
        
        # Header with URL
        header_frame = tk.Frame(site_frame, bg=COLORS['secondary'], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        url_label = tk.Label(header_frame, text=result['url'], 
                            font=("Arial", 12, "bold"), fg='white', bg=COLORS['secondary'])
        url_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Score on the right
        score = result.get('seo_score', 0)
        score_color = calculate_seo_score_color(score)
        score_label = tk.Label(header_frame, text=f"Score: {score}/100", 
                              font=("Arial", 14, "bold"), fg=score_color, bg=COLORS['secondary'])
        score_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Content frame
        content_frame = tk.Frame(site_frame, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Key metrics
        left_frame = tk.Frame(content_frame, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Metrics
        metrics = [
            ("Status Code", result.get('basic_info', {}).get('status_code', 'N/A'), 
             COLORS['success'] if result.get('basic_info', {}).get('status_code') == 200 else COLORS['danger']),
            ("Load Time", result.get('basic_info', {}).get('load_time', 'N/A'), COLORS['secondary']),
            ("Issues Found", len(result.get('issues', [])), 
             COLORS['success'] if len(result.get('issues', [])) == 0 else COLORS['danger']),
            ("Performance Score", f"{result.get('performance', {}).get('performance_score', 'N/A')}%", COLORS['info']),
            ("Mobile Friendly", "Yes" if result.get('technical_seo', {}).get('viewport') else "No",
             COLORS['success'] if result.get('technical_seo', {}).get('viewport') else COLORS['danger'])
        ]
        
        for metric, value, color in metrics:
            metric_frame = tk.Frame(left_frame, bg='white')
            metric_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(metric_frame, text=metric + ":", font=("Arial", 10), 
                    bg='white', width=15, anchor='w').pack(side=tk.LEFT)
            tk.Label(metric_frame, text=str(value), font=("Arial", 10, "bold"), 
                    fg=color, bg='white').pack(side=tk.LEFT)
        
        # Right side - Top issues
        right_frame = tk.Frame(content_frame, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="Top Issues:", font=("Arial", 11, "bold"), 
                bg='white').pack(anchor='w')
        
        issues = result.get('issues', [])[:5]  # Top 5 issues
        for issue in issues:
            issue_label = tk.Label(right_frame, text=f"• {issue}", 
                                  font=("Arial", 9), fg=COLORS['danger'], bg='white',
                                  wraplength=200, justify='left')
            issue_label.pack(anchor='w', pady=2)
    
    def update_results_display(self, app, result):
        """Update detailed results display"""
        url = result['url']
        
        # Update detailed results
        app.details_text.insert(tk.END, f"{'='*80}\n")
        app.details_text.insert(tk.END, f"DETAILED ANALYSIS: {url}\n")
        app.details_text.insert(tk.END, f"Timestamp: {result['timestamp']}\n")
        app.details_text.insert(tk.END, f"SEO Score: {result.get('seo_score', 0)}/100\n")
        if result.get('is_competitor'):
            app.details_text.insert(tk.END, "Type: COMPETITOR\n")
        app.details_text.insert(tk.END, f"{'='*80}\n\n")
        
        if 'error' not in result:
            # Add all analysis details
            self._add_analysis_details(app.details_text, result)
        else:
            app.details_text.insert(tk.END, f"Error: {result['error']}\n")
        
        app.details_text.insert(tk.END, "\n")
        app.details_text.see(tk.END)
        
        # Update issues & recommendations
        self._update_issues_display(app, result)
        
        # Update contacts
        self._update_contacts_display(app, result)
    
    def _add_analysis_details(self, text_widget, result):
        """Add detailed analysis to text widget"""
        # Basic Info
        text_widget.insert(tk.END, "BASIC INFORMATION:\n")
        for key, value in result.get('basic_info', {}).items():
            text_widget.insert(tk.END, f"  • {key.replace('_', ' ').title()}: {value}\n")
        
        # SEO Analysis
        text_widget.insert(tk.END, "\nSEO ANALYSIS:\n")
        seo = result.get('seo_analysis', {})
        if seo.get('title'):
            text_widget.insert(tk.END, f"  • Title: {seo['title'][:100]}{'...' if len(seo.get('title', '')) > 100 else ''}\n")
            text_widget.insert(tk.END, f"  • Title Length: {seo.get('title_length', 0)} chars\n")
        
        if seo.get('meta_description'):
            text_widget.insert(tk.END, f"  • Meta Description: {seo['meta_description'][:150]}{'...' if len(seo.get('meta_description', '')) > 150 else ''}\n")
            text_widget.insert(tk.END, f"  • Meta Desc Length: {seo.get('meta_desc_length', 0)} chars\n")
        
        # Add more details as needed...
    
    def _update_issues_display(self, app, result):
        """Update issues and recommendations display"""
        if result.get('issues') or result.get('recommendations'):
            app.issues_text.insert(tk.END, f"{'='*80}\n")
            app.issues_text.insert(tk.END, f"ISSUES & RECOMMENDATIONS: {result['url']}\n")
            if result.get('is_competitor'):
                app.issues_text.insert(tk.END, "(COMPETITOR SITE)\n")
            app.issues_text.insert(tk.END, f"{'='*80}\n\n")
            
            if result.get('issues'):
                app.issues_text.insert(tk.END, "❌ ISSUES FOUND:\n")
                for i, issue in enumerate(result['issues'], 1):
                    app.issues_text.insert(tk.END, f"  {i}. {issue}\n")
                app.issues_text.insert(tk.END, "\n")
            
            if result.get('recommendations'):
                app.issues_text.insert(tk.END, "✅ RECOMMENDATIONS:\n")
                for i, rec in enumerate(result['recommendations'], 1):
                    app.issues_text.insert(tk.END, f"  {i}. {rec}\n")
            
            app.issues_text.insert(tk.END, "\n")
    
    def _update_contacts_display(self, app, result):
        """Update contacts display"""
        if result.get('emails') or result.get('social_media'):
            app.contacts_text.insert(tk.END, f"{'='*80}\n")
            app.contacts_text.insert(tk.END, f"CONTACTS: {result['url']}\n")
            if result.get('is_competitor'):
                app.contacts_text.insert(tk.END, "(COMPETITOR SITE)\n")
            app.contacts_text.insert(tk.END, f"{'='*80}\n\n")
            
            if result.get('emails'):
                app.contacts_text.insert(tk.END, "📧 EMAIL ADDRESSES:\n")
                for email in result['emails']:
                    app.contacts_text.insert(tk.END, f"  • {email}\n")
                app.contacts_text.insert(tk.END, "\n")
            
            if result.get('social_media'):
                app.contacts_text.insert(tk.END, "🌐 SOCIAL MEDIA:\n")
                for platform, link in result['social_media'].items():
                    app.contacts_text.insert(tk.END, f"  • {platform.capitalize()}: {link}\n")
            
            app.contacts_text.insert(tk.END, "\n")
    
    def update_outreach_display(self, app, url, message):
        """Update outreach message display"""
        app.outreach_text.insert(tk.END, f"{'='*80}\n")
        app.outreach_text.insert(tk.END, f"AI OUTREACH MESSAGE FOR: {url}\n")
        app.outreach_text.insert(tk.END, f"{'='*80}\n\n")
        app.outreach_text.insert(tk.END, message)
        app.outreach_text.insert(tk.END, "\n\n")
        app.outreach_text.see(tk.END)
    
    def update_screenshot_gallery(self, app, result):
        """Update screenshot gallery"""
        if not result.get('screenshot') or not PIL_AVAILABLE:
            return
        
        # Create frame for this screenshot
        screenshot_frame = tk.Frame(app.screenshots_inner, bg='white', relief=tk.RAISED, bd=1)
        screenshot_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # URL label
        url_label = tk.Label(screenshot_frame, text=result['url'], 
                            font=("Arial", 10, "bold"), bg='white')
        url_label.pack(pady=5)
        
        # Load and display image
        try:
            img = PILImage.open(result['screenshot'])
            # Resize for display
            display_width = 600
            if img.width > display_width:
                ratio = display_width / img.width
                display_height = int(img.height * ratio)
                img = img.resize((display_width, display_height), PILImage.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Display image
            img_label = tk.Label(screenshot_frame, image=photo, bg='white')
            img_label.image = photo  # Keep a reference
            img_label.pack(padx=10, pady=5)
            
            # Score label
            score_label = tk.Label(screenshot_frame, 
                                 text=f"SEO Score: {result.get('seo_score', 0)}/100",
                                 font=("Arial", 10), bg='white')
            score_label.pack(pady=5)
            
        except Exception as e:
            error_label = tk.Label(screenshot_frame, text="Screenshot failed to load",
                                 font=("Arial", 10), fg='red', bg='white')
            error_label.pack(pady=5)
    
    def show_analysis_summary(self, app):
        """Show analysis summary window"""
        if not app.results:
            return
        
        # Separate main sites and competitors
        main_sites = [r for r in app.results if not r.get('is_competitor', False)]
        competitor_sites = [r for r in app.results if r.get('is_competitor', False)]
        
        # Calculate averages
        all_avg_score = sum(r.get('seo_score', 0) for r in app.results) / len(app.results) if app.results else 0
        main_avg_score = sum(r.get('seo_score', 0) for r in main_sites) / len(main_sites) if main_sites else 0
        comp_avg_score = sum(r.get('seo_score', 0) for r in competitor_sites) / len(competitor_sites) if competitor_sites else 0
        
        # Create summary window
        summary_window = tk.Toplevel(app.root)
        summary_window.title("AI Analysis Summary")
        summary_window.geometry("700x600")
        
        # Header
        header_frame = tk.Frame(summary_window, bg=COLORS['primary'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🤖 AI-Powered Analysis Complete!", 
                font=("Arial", 20, "bold"), fg="white", bg=COLORS['primary']).pack(expand=True)
        
        # Summary stats
        stats_frame = tk.Frame(summary_window, bg="white", padx=20, pady=20)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        stats = [
            ("Total Websites Analyzed", len(app.results)),
            ("Your Websites", len(main_sites)),
            ("AI-Found Competitors", len(competitor_sites)),
            ("Average SEO Score (All)", f"{all_avg_score:.1f}/100"),
            ("Your Average Score", f"{main_avg_score:.1f}/100"),
            ("Competitors Average", f"{comp_avg_score:.1f}/100"),
            ("Total Issues Found", sum(len(r.get('issues', [])) for r in app.results)),
            ("Websites with Errors", sum(1 for r in app.results if 'error' in r))
        ]
        
        for label, value in stats:
            stat_frame = tk.Frame(stats_frame, bg="white")
            stat_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(stat_frame, text=label + ":", font=("Arial", 12), 
                    bg="white", width=25, anchor='w').pack(side=tk.LEFT)
            
            # Color code certain values
            if "Your Average Score" in label:
                color = COLORS['success'] if main_avg_score >= 80 else COLORS['warning'] if main_avg_score >= 50 else COLORS['danger']
            elif "Competitors Average" in label:
                color = COLORS['info']
            else:
                color = COLORS['secondary']
            
            tk.Label(stat_frame, text=str(value), font=("Arial", 12, "bold"), 
                    fg=color, bg="white").pack(side=tk.LEFT)
        
        # Close button
        tk.Button(summary_window, text="Close", command=summary_window.destroy,
                 bg=COLORS['secondary'], fg="white", font=("Arial", 12),
                 padx=20, pady=10, relief=tk.FLAT).pack(pady=20)