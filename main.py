"""
SEO Analyzer Pro - Main Application
This is the entry point of the application
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for required libraries
required_libs = {
    'requests': 'requests',
    'bs4': 'beautifulsoup4',
    'pandas': 'pandas',
    'PIL': 'pillow',
    'selenium': 'selenium',
    'google.generativeai': 'google-generativeai'
}

missing_libs = []
for module, pip_name in required_libs.items():
    try:
        __import__(module)
    except ImportError:
        missing_libs.append(pip_name)

if missing_libs:
    root = tk.Tk()
    root.withdraw()
    
    message = f"Missing required libraries:\n{', '.join(missing_libs)}\n\n"
    message += "Install with:\npip install " + ' '.join(missing_libs)
    
    response = messagebox.askyesno("Missing Libraries", 
                                   message + "\n\nContinue anyway?")
    if not response:
        sys.exit(1)
    root.destroy()

# Import the main application
try:
    from modules.app import SEOAnalyzerApp
except ImportError as e:
    print(f"Error importing application: {e}")
    print("Make sure all module files are in the 'modules' folder")
    sys.exit(1)

def main():
    """Main entry point"""
    root = tk.Tk()
    app = SEOAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()