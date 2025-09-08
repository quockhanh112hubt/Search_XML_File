#!/usr/bin/env python3
"""
XML Search Application - Main Entry Point
Tìm kiếm file XML trên FTP Server với giao diện PyQt
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import MainWindow
from src.utils.logging_config import setup_logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

def set_application_icon(app):
    """Set application icon for taskbar and window"""
    try:
        # Get the directory containing the script
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_dir, "Resource", "icon.ico")
        
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            app.setWindowIcon(icon)
            print(f"Icon loaded from: {icon_path}")
        else:
            print(f"Icon not found at: {icon_path}")
            
    except Exception as e:
        print(f"Error setting application icon: {e}")

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("XML Search Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("XML Search Corp")
    
    # Set application icon
    set_application_icon(app)
    
    # Create and show main window
    window = MainWindow()
    window.app = app  # Pass app reference to window
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
