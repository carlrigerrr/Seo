"""
Export Module - Handles exporting results to various formats
"""

import json
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse

# PDF generation imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from .config import APP_VERSION
from .utils import get_domain_from_url

class ExportModule:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom PDF styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12
        )
    
    def export_to_pdf(self, results, outreach_messages, file_path):
        """Generate professional PDF report"""
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        
        # Title page
        story.append(Paragraph("AI-Powered SEO Analysis Report", self.title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", 
                             self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.heading_style))
        
        # Separate main sites and competitors
        main_sites = [r for r in results if not r.get('is_competitor', False)]
        competitor_sites = [r for r in results if r.get('is_competitor', False)]
        
        avg_score = sum(r.get('seo_score', 0) for r in results) / len(results) if results else 0
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Websites Analyzed', str(len(results))],
            ['Your Websites', str(len(main_sites))],
            ['AI-Found Competitors', str(len(competitor_sites))],
            ['Average SEO Score', f"{avg_score:.1f}/100"],
            ['Total Issues Found', str(sum(len(r.get('issues', [])) for r in results))],
            ['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M')]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(PageBreak())
        
        # Competitor Comparison if available
        if competitor_sites:
            story.append(Paragraph("AI Competitor Comparison", self.heading_style))
            
            comp_data = [['Website', 'Type', 'SEO Score', 'Issues']]
            for site in sorted(results, key=lambda x: x.get('seo_score', 0), reverse=True):
                if 'error' not in site:
                    comp_data.append([
                        get_domain_from_url(site['url']),
                        'Competitor' if site.get('is_competitor') else 'Your Site',
                        f"{site.get('seo_score', 0)}/100",
                        str(len(site.get('issues', [])))
                    ])
            
            comp_table = Table(comp_data)
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(comp_table)
            story.append(PageBreak())
        
        # Detailed results for each website
        for result in results:
            # Website header
            site_type = " (AI-Found Competitor)" if result.get('is_competitor') else ""
            story.append(Paragraph(f"Analysis: {result['url']}{site_type}", self.heading_style))
            
            # SEO Score with color
            score = result.get('seo_score', 0)
            score_color = '#E74C3C' if score < 50 else '#F39C12' if score < 80 else '#27AE60'
            story.append(Paragraph(f"<font color='{score_color}'>SEO Score: {score}/100</font>", 
                                 self.styles['Heading3']))
            
            # Screenshot if available
            if result.get('screenshot'):
                try:
                    img = Image(result['screenshot'], width=5*inch, height=3.75*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
                except:
                    pass
            
            # Basic info table
            if 'error' not in result:
                basic_data = [
                    ['Status Code', str(result.get('basic_info', {}).get('status_code', 'N/A'))],
                    ['Load Time', result.get('basic_info', {}).get('load_time', 'N/A')],
                    ['Page Size', result.get('basic_info', {}).get('page_size', 'N/A')],
                    ['Mobile Friendly', 'Yes' if result.get('technical_seo', {}).get('viewport') else 'No'],
                    ['HTTPS', 'Yes' if result.get('technical_seo', {}).get('https') else 'No']
                ]
                
                basic_table = Table(basic_data)
                basic_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(basic_table)
                story.append(Spacer(1, 0.2*inch))
                
                # Issues
                if result.get('issues'):
                    story.append(Paragraph("Issues Found:", self.styles['Heading3']))
                    for issue in result['issues'][:10]:  # Limit to 10 issues
                        story.append(Paragraph(f"• {issue}", self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Recommendations
                if result.get('recommendations'):
                    story.append(Paragraph("Recommendations:", self.styles['Heading3']))
                    for rec in result['recommendations'][:10]:  # Limit to 10 recommendations
                        story.append(Paragraph(f"✓ {rec}", self.styles['Normal']))
                
                # Outreach message if available
                if not result.get('is_competitor') and outreach_messages.get(result['url']):
                    story.append(Spacer(1, 0.2*inch))
                    story.append(Paragraph("AI-Generated Outreach Message:", self.styles['Heading3']))
                    story.append(Paragraph(outreach_messages[result['url']], self.styles['Normal']))
            else:
                story.append(Paragraph(f"Error: {result['error']}", self.styles['Normal']))
            
            story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
    
    def export_to_excel(self, results, outreach_messages, file_path):
        """Export results to Excel with multiple sheets"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Summary sheet
            main_sites = [r for r in results if not r.get('is_competitor', False)]
            competitor_sites = [r for r in results if r.get('is_competitor', False)]
            
            summary_data = {
                'Metric': ['Total Websites', 'Your Websites', 'AI-Found Competitors', 
                          'Average SEO Score (All)', 'Your Average Score', 'Competitors Average',
                          'Total Issues', 'Best Performer', 'Worst Performer'],
                'Value': [
                    len(results),
                    len(main_sites),
                    len(competitor_sites),
                    f"{sum(r.get('seo_score', 0) for r in results) / len(results):.1f}" if results else 'N/A',
                    f"{sum(r.get('seo_score', 0) for r in main_sites) / len(main_sites):.1f}" if main_sites else 'N/A',
                    f"{sum(r.get('seo_score', 0) for r in competitor_sites) / len(competitor_sites):.1f}" if competitor_sites else 'N/A',
                    sum(len(r.get('issues', [])) for r in results),
                    max(results, key=lambda x: x.get('seo_score', 0))['url'] if results else 'N/A',
                    min(results, key=lambda x: x.get('seo_score', 0))['url'] if results else 'N/A'
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed results sheet
            excel_data = []
            
            for result in results:
                row = {
                    'URL': result['url'],
                    'Type': 'AI Competitor' if result.get('is_competitor') else 'Main Site',
                    'Timestamp': result['timestamp'],
                    'SEO Score': result.get('seo_score', 0),
                    'Status Code': result.get('basic_info', {}).get('status_code', 'Error'),
                    'Load Time': result.get('basic_info', {}).get('load_time', 'N/A'),
                    'Page Size': result.get('basic_info', {}).get('page_size', 'N/A'),
                    'Title': result.get('seo_analysis', {}).get('title', ''),
                    'Title Length': result.get('seo_analysis', {}).get('title_length', 0),
                    'Meta Description': result.get('seo_analysis', {}).get('meta_description', ''),
                    'Meta Desc Length': result.get('seo_analysis', {}).get('meta_desc_length', 0),
                    'H1 Count': result.get('seo_analysis', {}).get('headers', {}).get('h1', 0),
                    'Images Total': result.get('seo_analysis', {}).get('images', {}).get('total', 0),
                    'Images No Alt': result.get('seo_analysis', {}).get('images', {}).get('without_alt', 0),
                    'Has Schema': 'Yes' if result.get('seo_analysis', {}).get('has_schema') else 'No',
                    'HTTPS': 'Yes' if result.get('technical_seo', {}).get('https') else 'No',
                    'Mobile Friendly': 'Yes' if result.get('technical_seo', {}).get('viewport') else 'No',
                    'Robots.txt': 'Yes' if result.get('technical_seo', {}).get('robots_txt') else 'No',
                    'Sitemap.xml': 'Yes' if result.get('technical_seo', {}).get('sitemap_xml') else 'No',
                    'Performance Score': result.get('performance', {}).get('performance_score', 'N/A'),
                    'Issues Count': len(result.get('issues', [])),
                    'Issues': '; '.join(result.get('issues', [])),
                    'Recommendations': '; '.join(result.get('recommendations', [])),
                    'Emails': '; '.join(result.get('emails', [])),
                    'Facebook': result.get('social_media', {}).get('facebook', ''),
                    'Twitter': result.get('social_media', {}).get('twitter', ''),
                    'Instagram': result.get('social_media', {}).get('instagram', ''),
                    'LinkedIn': result.get('social_media', {}).get('linkedin', ''),
                    'YouTube': result.get('social_media', {}).get('youtube', ''),
                    'Error': result.get('error', '')
                }
                excel_data.append(row)
            
            # Create DataFrame and save
            df = pd.DataFrame(excel_data)
            df.to_excel(writer, sheet_name='Detailed Results', index=False)
            
            # Competitor Comparison sheet
            if competitor_sites:
                comp_data = []
                for main_site in main_sites:
                    main_url = main_site['url']
                    main_score = main_site.get('seo_score', 0)
                    
                    # Find competitors for this main site
                    site_competitors = [r for r in competitor_sites if r.get('main_site') == main_url]
                    
                    for comp in site_competitors:
                        comp_data.append({
                            'Main Site': main_url,
                            'Main Site Score': main_score,
                            'Competitor': comp['url'],
                            'Competitor Score': comp.get('seo_score', 0),
                            'Score Difference': main_score - comp.get('seo_score', 0),
                            'Main Site Issues': len(main_site.get('issues', [])),
                            'Competitor Issues': len(comp.get('issues', [])),
                            'Advantage': 'Main Site' if main_score > comp.get('seo_score', 0) else 'Competitor'
                        })
                
                if comp_data:
                    comp_df = pd.DataFrame(comp_data)
                    comp_df.to_excel(writer, sheet_name='Competitor Comparison', index=False)
            
            # Issues sheet
            issues_data = []
            for result in results:
                for issue in result.get('issues', []):
                    issues_data.append({
                        'URL': result['url'],
                        'Type': 'AI Competitor' if result.get('is_competitor') else 'Main Site',
                        'Issue': issue,
                        'SEO Score': result.get('seo_score', 0)
                    })
            
            if issues_data:
                issues_df = pd.DataFrame(issues_data)
                issues_df.to_excel(writer, sheet_name='All Issues', index=False)
            
            # Contacts sheet with AI outreach
            contacts_data = []
            for result in results:
                if result.get('emails') or result.get('social_media'):
                    # Create one row per email
                    emails = result.get('emails', [])
                    if emails:
                        for email in emails:
                            contact_row = {
                                'URL': result['url'],
                                'Type': 'AI Competitor' if result.get('is_competitor') else 'Main Site',
                                'Email': email,
                                'AI Outreach Message': outreach_messages.get(result['url'], '') if not result.get('is_competitor') else ''
                            }
                            # Add social media
                            for platform in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'pinterest']:
                                contact_row[platform.capitalize()] = result.get('social_media', {}).get(platform, '')
                            contacts_data.append(contact_row)
                    else:
                        # If no emails, still add row with social media
                        contact_row = {
                            'URL': result['url'],
                            'Type': 'AI Competitor' if result.get('is_competitor') else 'Main Site',
                            'Email': '',
                            'AI Outreach Message': outreach_messages.get(result['url'], '') if not result.get('is_competitor') else ''
                        }
                        for platform in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'pinterest']:
                            contact_row[platform.capitalize()] = result.get('social_media', {}).get(platform, '')
                        contacts_data.append(contact_row)
            
            if contacts_data:
                contacts_df = pd.DataFrame(contacts_data)
                contacts_df.to_excel(writer, sheet_name='Contacts & AI Outreach', index=False)
            
            # AI Outreach Messages sheet
            if outreach_messages:
                outreach_data = []
                for url, message in outreach_messages.items():
                    # Find the result for this URL
                    site_result = next((r for r in results if r['url'] == url), None)
                    if site_result:
                        outreach_data.append({
                            'Website': url,
                            'SEO Score': site_result.get('seo_score', 0),
                            'Issues Count': len(site_result.get('issues', [])),
                            'AI Outreach Message': message,
                            'Primary Email': site_result.get('emails', [''])[0] if site_result.get('emails') else ''
                        })
                
                if outreach_data:
                    outreach_df = pd.DataFrame(outreach_data)
                    outreach_df.to_excel(writer, sheet_name='AI Outreach Messages', index=False)
    
    def export_to_json(self, results, outreach_messages, competitor_map, metadata, file_path):
        """Export results to JSON format"""
        # Separate main sites and competitors
        main_sites = [r for r in results if not r.get('is_competitor', False)]
        competitor_sites = [r for r in results if r.get('is_competitor', False)]
        
        export_data = {
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'tool_version': APP_VERSION,
                'total_websites': len(results),
                'main_sites_count': len(main_sites),
                'ai_competitors_count': len(competitor_sites),
                'average_score': sum(r.get('seo_score', 0) for r in results) / len(results) if results else 0,
                'features_used': metadata.get('features_used', {})
            },
            'results': [],
            'outreach_messages': outreach_messages,
            'competitor_mapping': competitor_map
        }
        
        # Process results without screenshots for JSON
        for result in results:
            # Create a copy without screenshot data
            json_result = result.copy()
            if 'screenshot' in json_result:
                json_result['screenshot'] = 'Screenshot captured but not included in JSON export'
            export_data['results'].append(json_result)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)