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
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
