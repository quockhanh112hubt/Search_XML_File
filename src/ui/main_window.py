"""
Main Window UI for XML Search Application
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QComboBox, QCheckBox, QDateEdit, QProgressBar, QStatusBar, QTabWidget,
    QGroupBox, QSplitter, QHeaderView, QMessageBox, QFileDialog,
    QSpinBox, QFrame
)
from PyQt5.QtCore import QDate, QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFont, QIcon

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.ftp_manager import FTPManager
from src.core.search_worker import SearchWorker, SearchResult
from src.utils.export_utils import ResultExporter
from src.utils.date_utils import parse_date_range, format_date_for_display
from src.utils.settings_manager import SettingsManager
from config.settings import (
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, DEFAULT_FILE_PATTERN, 
    MAX_WORKER_THREADS
)
from src.ui.styles import COMPLETE_STYLESHEET, BUTTON_STYLES, COLORS

class SearchThread(QThread):
    """Background search thread"""
    
    progress_updated = pyqtSignal(dict)
    search_completed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, search_worker: SearchWorker, search_params: dict):
        super().__init__()
        self.search_worker = search_worker
        self.search_params = search_params
    
    def run(self):
        try:
            def progress_callback(status):
                self.progress_updated.emit(status)
            
            results = self.search_worker.search(self.search_params, progress_callback)
            self.search_completed.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        if self.search_worker:
            self.search_worker.stop()

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.ftp_manager = FTPManager()
        self.search_worker = None
        self.search_thread = None
        self.search_results = []
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        
        self.init_ui()
        self.setup_connections()
        self.setup_custom_logging()
        self.load_saved_settings()
        self.auto_connect_if_possible()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("🔍 XML Search Tool - Professional Dark Edition")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Set window icon
        self.set_window_icon()
        
        # Apply modern dark stylesheet
        self.setStyleSheet(COMPLETE_STYLESHEET)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_search_tab()
        self.create_settings_tab()
        self.create_results_tab()
        self.create_log_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text_primary']};
                border-top: 1px solid {COLORS['border']};
                font-weight: 500;
            }}
        """)
        self.setStatusBar(self.status_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                text-align: center;
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                font-weight: bold;
                min-height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 6px;
                margin: 1px;
            }}
        """)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; padding: 5px;")
        self.status_bar.addWidget(self.status_label)
        
    def create_search_tab(self):
        """Create search parameters tab"""
        search_widget = QWidget()
        layout = QVBoxLayout(search_widget)
        
        # Date range group
        date_group = QGroupBox("Date Range")
        date_layout = QGridLayout(date_group)
        
        # Quick date range
        date_layout.addWidget(QLabel("Quick Range:"), 0, 0)
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems([
            "Custom Range", "Today", "Yesterday", "This Week", "Last Week",
            "This Month", "Last Month", "Last 7 Days", "Last 30 Days"
        ])
        date_layout.addWidget(self.date_range_combo, 0, 1, 1, 2)
        
        # Custom date range
        date_layout.addWidget(QLabel("From Date:"), 1, 0)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date, 1, 1)
        
        date_layout.addWidget(QLabel("To Date:"), 1, 2)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date, 1, 3)
        
        layout.addWidget(date_group)
        
        # File filter group
        filter_group = QGroupBox("File Filter")
        filter_layout = QGridLayout(filter_group)
        
        filter_layout.addWidget(QLabel("File Pattern:"), 0, 0)
        self.file_pattern = QLineEdit(DEFAULT_FILE_PATTERN)
        self.file_pattern.setPlaceholderText("e.g., TCO_*_KMC_*.xml")
        filter_layout.addWidget(self.file_pattern, 0, 1, 1, 2)
        
        layout.addWidget(filter_group)
        
        # Search parameters group
        search_group = QGroupBox("Search Parameters")
        search_layout = QGridLayout(search_group)
        
        search_layout.addWidget(QLabel("Keywords:"), 0, 0)
        self.keywords_input = QTextEdit()
        self.keywords_input.setMaximumHeight(80)
        self.keywords_input.setPlaceholderText("Enter keywords (one per line)")
        search_layout.addWidget(self.keywords_input, 0, 1, 2, 2)
        
        search_layout.addWidget(QLabel("Search Mode:"), 2, 0)
        self.search_mode = QComboBox()
        self.search_mode.addItems(["Text Contains", "Regex Pattern", "XPath Query"])
        search_layout.addWidget(self.search_mode, 2, 1)
        
        self.case_sensitive = QCheckBox("Case Sensitive")
        self.setup_custom_checkbox(self.case_sensitive)
        search_layout.addWidget(self.case_sensitive, 2, 2)
        
        search_layout.addWidget(QLabel("Max Threads:"), 3, 0)
        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 20)
        self.max_threads.setValue(MAX_WORKER_THREADS)
        search_layout.addWidget(self.max_threads, 3, 1)
        
        # Search options
        self.find_all_matches = QCheckBox("Find all matches per file")
        self.setup_custom_checkbox(self.find_all_matches)
        self.find_all_matches.setToolTip("If unchecked, stops at first match per file (faster)")
        search_layout.addWidget(self.find_all_matches, 3, 2)
        
        layout.addWidget(search_group)
        
        # Search controls
        controls_layout = QHBoxLayout()
        
        self.search_button = QPushButton("Start Search")
        self.search_button.setStyleSheet(BUTTON_STYLES['primary'])
        self.search_button.setMinimumHeight(35)
        controls_layout.addWidget(self.search_button)
        
        self.stop_button = QPushButton("Stop Search")
        self.stop_button.setStyleSheet(BUTTON_STYLES['error'])
        self.stop_button.setMinimumHeight(35)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Add to tab
        self.tab_widget.addTab(search_widget, "Search")
        
    def create_settings_tab(self):
        """Create FTP settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # FTP connection group
        ftp_group = QGroupBox("FTP Connection")
        ftp_layout = QGridLayout(ftp_group)
        
        ftp_layout.addWidget(QLabel("FTP Host:"), 0, 0)
        self.ftp_host = QLineEdit()
        self.ftp_host.setPlaceholderText("ftp.example.com")
        ftp_layout.addWidget(self.ftp_host, 0, 1)
        
        ftp_layout.addWidget(QLabel("Port:"), 0, 2)
        self.ftp_port = QSpinBox()
        self.ftp_port.setRange(1, 65535)
        self.ftp_port.setValue(21)
        ftp_layout.addWidget(self.ftp_port, 0, 3)
        
        ftp_layout.addWidget(QLabel("Username:"), 1, 0)
        self.ftp_username = QLineEdit()
        ftp_layout.addWidget(self.ftp_username, 1, 1)
        
        ftp_layout.addWidget(QLabel("Password:"), 1, 2)
        self.ftp_password = QLineEdit()
        self.ftp_password.setEchoMode(QLineEdit.Password)
        ftp_layout.addWidget(self.ftp_password, 1, 3)
        
        # Remember password checkbox
        self.remember_password = QCheckBox("Remember Password")
        self.setup_custom_checkbox(self.remember_password)
        ftp_layout.addWidget(self.remember_password, 2, 0, 1, 2)
        
        # Connection button (Connect/Disconnect)  
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet(BUTTON_STYLES['success'])
        self.connect_button.setMinimumHeight(35)
        ftp_layout.addWidget(self.connect_button, 3, 0, 1, 2)
        
        self.connection_status = QLabel("Not connected")
        self.connection_status.setStyleSheet(f"color: {COLORS['error']}; font-weight: bold;")
        ftp_layout.addWidget(self.connection_status, 3, 2, 1, 2)
        
        layout.addWidget(ftp_group)
        
        # Directory structure group
        dir_group = QGroupBox("FTP Directory Structure")
        dir_layout = QGridLayout(dir_group)
        
        dir_layout.addWidget(QLabel("Source Directory:"), 0, 0)
        self.source_directory = QLineEdit()
        self.source_directory.setPlaceholderText("SAMSUNG")
        dir_layout.addWidget(self.source_directory, 0, 1, 1, 2)
        
        dir_layout.addWidget(QLabel("Send File Directory:"), 1, 0)
        self.send_file_directory = QLineEdit()
        self.send_file_directory.setPlaceholderText("Send File")
        dir_layout.addWidget(self.send_file_directory, 1, 1, 1, 2)
        
        dir_layout.addWidget(QLabel("Receive File Directory:"), 2, 0)
        self.receive_file_directory = QLineEdit()
        self.receive_file_directory.setPlaceholderText("Receive File")
        dir_layout.addWidget(self.receive_file_directory, 2, 1, 1, 2)
        
        # Directory structure help text
        help_label = QLabel("Directory structure: /{Source}/{YYYYMMDD}/{Send File}/files.xml")
        help_label.setStyleSheet("color: #666; font-style: italic;")
        dir_layout.addWidget(help_label, 3, 0, 1, 3)
        
        layout.addWidget(dir_group)
        
        # Settings controls
        settings_controls = QHBoxLayout()
        
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.setStyleSheet(BUTTON_STYLES['primary'])
        self.save_settings_button.setMinimumHeight(32)
        settings_controls.addWidget(self.save_settings_button)
        
        self.reset_settings_button = QPushButton("Reset to Defaults")
        self.reset_settings_button.setStyleSheet(BUTTON_STYLES['secondary'])
        self.reset_settings_button.setMinimumHeight(32)
        settings_controls.addWidget(self.reset_settings_button)
        
        settings_controls.addStretch()
        layout.addLayout(settings_controls)
        layout.addStretch()
        
        # Add to tab
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def create_results_tab(self):
        """Create results display tab"""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)
        
        # Results controls
        controls_layout = QHBoxLayout()
        
        self.results_count_label = QLabel("Results: 0")
        self.results_count_label.setStyleSheet(f"font-weight: bold; color: {COLORS['text_primary']}; font-size: 12px;")
        controls_layout.addWidget(self.results_count_label)
        
        controls_layout.addStretch()
        
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setStyleSheet(BUTTON_STYLES['secondary'])
        self.export_csv_button.setMinimumHeight(32)
        self.export_csv_button.setEnabled(False)
        controls_layout.addWidget(self.export_csv_button)
        
        self.export_excel_button = QPushButton("Export Excel")
        self.export_excel_button.setStyleSheet(BUTTON_STYLES['secondary'])
        self.export_excel_button.setMinimumHeight(32)
        self.export_excel_button.setEnabled(False)
        controls_layout.addWidget(self.export_excel_button)
        
        layout.addLayout(controls_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Date", "Filename", "File Path", "Match Type", "Match Content", "Line"
        ])
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Filename
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # File Path
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Match Type
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Match Content
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Line
        
        # Configure vertical header (row numbers)
        v_header = self.results_table.verticalHeader()
        v_header.setVisible(True)
        v_header.setDefaultSectionSize(40)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.results_table)
        
        # Add to tab
        self.tab_widget.addTab(results_widget, "Results")
        
    def create_log_tab(self):
        """Create log display tab with statistics"""
        log_widget = QWidget()
        layout = QVBoxLayout(log_widget)
        
        # Statistics panel
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
                margin: 4px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        # Statistics labels
        self.stats_directories = QLabel("📁 Directories: 0")
        self.stats_xml_files = QLabel("📄 XML Files: 0")
        self.stats_processed = QLabel("✅ Processed: 0")
        self.stats_failed = QLabel("❌ Failed: 0")
        self.stats_connections = QLabel("🔌 Connection Issues: 0")
        
        # Style statistics labels
        stats_style = f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-weight: 600;
                font-size: 11px;
                padding: 4px 8px;
                background-color: {COLORS['bg_dark']};
                border-radius: 4px;
                margin: 2px;
            }}
        """
        
        for label in [self.stats_directories, self.stats_xml_files, self.stats_processed, 
                     self.stats_failed, self.stats_connections]:
            label.setStyleSheet(stats_style)
            stats_layout.addWidget(label)
        
        stats_layout.addStretch()
        
        # Clear logs button
        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.setStyleSheet(BUTTON_STYLES['secondary'])
        self.clear_logs_button.setMinimumHeight(28)
        self.clear_logs_button.clicked.connect(self.clear_logs)
        stats_layout.addWidget(self.clear_logs_button)
        
        layout.addWidget(stats_frame)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
                line-height: 1.4;
            }}
        """)
        
        layout.addWidget(self.log_display)
        
        # Initialize statistics
        self.log_stats = {
            'directories': 0,
            'xml_files': 0,
            'processed': 0,
            'failed': 0,
            'connection_issues': 0
        }
        
        # Add to tab
        self.tab_widget.addTab(log_widget, "Logs")
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Search controls
        self.search_button.clicked.connect(self.start_search)
        self.stop_button.clicked.connect(self.stop_search)
        
        # FTP settings
        self.connect_button.clicked.connect(self.toggle_connection)
        
        # Settings controls
        self.save_settings_button.clicked.connect(self.save_settings)
        self.reset_settings_button.clicked.connect(self.reset_settings)
        
        # Date range
        self.date_range_combo.currentTextChanged.connect(self.on_date_range_changed)
        
        # Export buttons
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_excel_button.clicked.connect(self.export_excel)
        
    def update_connection_status(self, text: str, status_type: str = 'error'):
        """Update connection status with proper styling"""
        color_map = {
            'success': COLORS['success'],
            'error': COLORS['error'],
            'warning': COLORS['warning'],
            'info': COLORS['text_secondary']
        }
        color = color_map.get(status_type, COLORS['error'])
        self.connection_status.setText(text)
        self.connection_status.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def setup_custom_checkbox(self, checkbox):
        """Setup custom checkbox with checkmark display"""
        def update_checkbox_style():
            if checkbox.isChecked():
                checkbox.setText(f"✓ {checkbox.text().replace('✓ ', '')}")
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        color: {COLORS['primary']};
                        font-weight: 600;
                    }}
                    QCheckBox::indicator {{
                        width: 22px;
                        height: 22px;
                        border: 2px solid {COLORS['primary']};
                        border-radius: 6px;
                        background-color: {COLORS['primary']};
                    }}
                """)
            else:
                checkbox.setText(checkbox.text().replace('✓ ', ''))
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        color: {COLORS['text_primary']};
                        font-weight: 500;
                    }}
                    QCheckBox::indicator {{
                        width: 22px;
                        height: 22px;
                        border: 2px solid {COLORS['border']};
                        border-radius: 6px;
                        background-color: {COLORS['bg_primary']};
                    }}
                """)
        
        checkbox.stateChanged.connect(lambda: update_checkbox_style())
        update_checkbox_style()  # Initial setup
    
    def update_results_count_style(self, count: int):
        """Update results count with proper styling"""
        if count == 0:
            color = COLORS['text_secondary']
        elif count < 50:
            color = COLORS['success']
        elif count < 200:
            color = COLORS['warning'] 
        else:
            color = COLORS['error']
        
        self.results_count_label.setText(f"Results: {count}")
        self.results_count_label.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 12px;")
    
    def on_date_range_changed(self, range_text: str):
        """Handle date range combo change"""
        if range_text != "Custom Range":
            try:
                start_date, end_date = parse_date_range(range_text)
                self.start_date.setDate(QDate(start_date))
                self.end_date.setDate(QDate(end_date))
            except:
                pass
    
    def toggle_connection(self):
        """Toggle FTP connection (Connect/Disconnect)"""
        if self.ftp_manager.is_connected:
            # Disconnect
            try:
                self.ftp_manager.disconnect()
                self.update_connection_status("Disconnected", 'error')
                self.connect_button.setText("Connect")
                self.connect_button.setStyleSheet(BUTTON_STYLES['success'])
                QMessageBox.information(self, "Success", "Disconnected from FTP server")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Disconnect error: {str(e)}")
        else:
            # Connect
            self.connect_to_ftp()
    
    def connect_to_ftp(self):
        """Connect to FTP server"""
        host = self.ftp_host.text().strip()
        port = self.ftp_port.value()
        username = self.ftp_username.text().strip()
        password = self.ftp_password.text()
        
        if not all([host, username, password]):
            QMessageBox.warning(self, "Warning", "Please fill in all FTP connection fields")
            return
        
        self.connect_button.setEnabled(False)
        self.update_connection_status("Connecting...", 'info')
        
        try:
            if self.ftp_manager.connect(host, port, username, password):
                self.update_connection_status("✓ Connected", 'success')
                self.connect_button.setText("Disconnect")
                self.connect_button.setStyleSheet(BUTTON_STYLES['error'])
                QMessageBox.information(self, "Success", "FTP connection successful!")
            else:
                self.update_connection_status("✗ Failed", 'error')
                QMessageBox.warning(self, "Error", "FTP connection failed!")
                
        except Exception as e:
            self.update_connection_status("✗ Error", 'error')
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            
        finally:
            self.connect_button.setEnabled(True)
    
    def start_search(self):
        """Start search operation"""
        # Validate inputs
        if not self.ftp_manager.is_connected:
            QMessageBox.warning(self, "Warning", "Please connect to FTP server first")
            self.tab_widget.setCurrentIndex(1)  # Switch to settings tab
            return
        
        keywords_text = self.keywords_input.toPlainText().strip()
        if not keywords_text:
            QMessageBox.warning(self, "Warning", "Please enter keywords to search")
            return
        
        # Prepare search parameters
        keywords = [line.strip() for line in keywords_text.split('\n') if line.strip()]
        
        search_params = {
            'start_date': self.start_date.date().toPyDate(),
            'end_date': self.end_date.date().toPyDate(),
            'keywords': keywords,
            'search_mode': self.search_mode.currentText().lower().replace(' ', '_'),
            'case_sensitive': self.case_sensitive.isChecked(),
            'file_pattern': self.file_pattern.text().strip() or None,
            'max_threads': self.max_threads.value(),
            'find_all_matches': self.find_all_matches.isChecked(),
            # Add directory settings
            'source_directory': self.source_directory.text().strip() or 'SAMSUNG',
            'send_file_directory': self.send_file_directory.text().strip() or 'Send File'
        }
        
        # Convert search mode
        if 'regex' in search_params['search_mode']:
            search_params['search_mode'] = 'regex'
        elif 'xpath' in search_params['search_mode']:
            search_params['search_mode'] = 'xpath'
        else:
            search_params['search_mode'] = 'text'
        
        # Create search worker and thread
        self.search_worker = SearchWorker(self.ftp_manager)
        self.search_thread = SearchThread(self.search_worker, search_params)
        
        # Connect signals
        self.search_thread.progress_updated.connect(self.on_search_progress)
        self.search_thread.search_completed.connect(self.on_search_completed)
        self.search_thread.error_occurred.connect(self.on_search_error)
        
        # Update UI
        self.search_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting search...")
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.search_results = []
        self.update_results_display()
        
        # Start search
        self.search_thread.start()
        
        # Switch to results tab
        self.tab_widget.setCurrentIndex(2)
    
    def stop_search(self):
        """Stop search operation"""
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.status_label.setText("Stopping search...")
    
    def on_search_progress(self, status: dict):
        """Handle search progress update"""
        dirs_processed = status['directories_processed']
        dirs_total = status['directories_total']
        files_processed = status['files_processed']
        files_total = status['files_total']
        matches_found = status['matches_found']
        current_file = status['current_file']
        
        # Update progress bar
        if files_total > 0:
            progress = int((files_processed / files_total) * 100)
            self.progress_bar.setValue(progress)
        
        # Update status
        status_text = f"Processing: {dirs_processed}/{dirs_total} directories · {files_processed}/{files_total} files · {matches_found} matches"
        if current_file:
            status_text += f" · {current_file}"
        
        self.status_label.setText(status_text)
    
    def on_search_completed(self, results: List[SearchResult]):
        """Handle search completion"""
        self.search_results = results
        self.update_results_table()
        self.update_results_display()
        
        # Update UI
        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Search completed. Found {len(results)} matches.")
        
        # Enable export buttons
        self.export_csv_button.setEnabled(len(results) > 0)
        self.export_excel_button.setEnabled(len(results) > 0)
    
    def on_search_error(self, error_message: str):
        """Handle search error"""
        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Search failed")
        
        QMessageBox.critical(self, "Search Error", f"Search failed: {error_message}")
    
    def update_results_table(self):
        """Update results table with search results"""
        self.results_table.setRowCount(len(self.search_results))
        
        for row, result in enumerate(self.search_results):
            try:
                # Check if result is a SearchResult object
                if hasattr(result, 'date_dir'):
                    self.results_table.setItem(row, 0, QTableWidgetItem(result.date_dir))
                    self.results_table.setItem(row, 1, QTableWidgetItem(result.filename))
                    self.results_table.setItem(row, 2, QTableWidgetItem(result.file_path))
                    self.results_table.setItem(row, 3, QTableWidgetItem(result.match_type))
                    self.results_table.setItem(row, 4, QTableWidgetItem(result.match_content))
                    self.results_table.setItem(row, 5, QTableWidgetItem(str(result.line_number)))
                else:
                    # Handle unexpected result type
                    print(f"Warning: Unexpected result type: {type(result)} = {result}")
                    self.results_table.setItem(row, 0, QTableWidgetItem("Unknown"))
                    self.results_table.setItem(row, 1, QTableWidgetItem(str(result)))
                    self.results_table.setItem(row, 2, QTableWidgetItem(""))
                    self.results_table.setItem(row, 3, QTableWidgetItem("Error"))
                    self.results_table.setItem(row, 4, QTableWidgetItem(""))
                    self.results_table.setItem(row, 5, QTableWidgetItem("0"))
            except Exception as e:
                print(f"Error updating row {row}: {e}")
                # Fill with empty values to prevent crashes
                for col in range(6):
                    self.results_table.setItem(row, col, QTableWidgetItem(""))
    
    def update_results_display(self):
        """Update results count label"""
        count = len(self.search_results)
        self.update_results_count_style(count)
    
    def export_csv(self):
        """Export results to CSV"""
        if not self.search_results:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "search_results.csv", "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                ResultExporter.export_to_csv(self.search_results, filename)
                QMessageBox.information(self, "Success", f"Results exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def export_excel(self):
        """Export results to Excel"""
        if not self.search_results:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Excel", "search_results.xlsx", "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                ResultExporter.export_to_excel(self.search_results, filename)
                QMessageBox.information(self, "Success", f"Results exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.search_thread and self.search_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit", 
                "Search is still running. Do you want to stop and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.search_thread.stop()
                self.search_thread.wait(3000)  # Wait up to 3 seconds
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
        # Clean up FTP connection
        if self.ftp_manager:
            self.ftp_manager.disconnect()
    
    def load_saved_settings(self):
        """Load saved settings into UI"""
        try:
            # Load FTP settings
            ftp_settings = self.settings.get('ftp', {})
            self.ftp_host.setText(ftp_settings.get('host', ''))
            self.ftp_port.setValue(ftp_settings.get('port', 21))
            self.ftp_username.setText(ftp_settings.get('username', ''))
            
            # Load password only if remember_password is enabled
            if ftp_settings.get('remember_password', False):
                self.ftp_password.setText(ftp_settings.get('password', ''))
                self.remember_password.setChecked(True)
            
            # Load directory settings
            dir_settings = self.settings.get('directories', {})
            self.source_directory.setText(dir_settings.get('source_directory', 'SAMSUNG'))
            self.send_file_directory.setText(dir_settings.get('send_file_directory', 'Send File'))
            self.receive_file_directory.setText(dir_settings.get('receive_file_directory', 'Receive File'))
            
            # Load search settings
            search_settings = self.settings.get('search', {})
            self.file_pattern.setText(search_settings.get('default_file_pattern', 'TCO_*_KMC_*.xml'))
            self.case_sensitive.setChecked(search_settings.get('case_sensitive', False))
            self.find_all_matches.setChecked(search_settings.get('find_all_matches', False))
            self.max_threads.setValue(search_settings.get('max_threads', 8))
            
            # Load UI settings
            ui_settings = self.settings.get('ui', {})
            last_date_range = ui_settings.get('last_date_range', 'Last 7 Days')
            index = self.date_range_combo.findText(last_date_range)
            if index >= 0:
                self.date_range_combo.setCurrentIndex(index)
            
            last_search_mode = ui_settings.get('last_search_mode', 'Text Contains')
            index = self.search_mode.findText(last_search_mode)
            if index >= 0:
                self.search_mode.setCurrentIndex(index)
                
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings"""
        try:
            # Update settings from UI
            self.settings['ftp'] = {
                'host': self.ftp_host.text().strip(),
                'port': self.ftp_port.value(),
                'username': self.ftp_username.text().strip(),
                'password': self.ftp_password.text() if self.remember_password.isChecked() else '',
                'remember_password': self.remember_password.isChecked()
            }
            
            self.settings['directories'] = {
                'source_directory': self.source_directory.text().strip() or 'SAMSUNG',
                'send_file_directory': self.send_file_directory.text().strip() or 'Send File',
                'receive_file_directory': self.receive_file_directory.text().strip() or 'Receive File'
            }
            
            self.settings['search'] = {
                'default_file_pattern': self.file_pattern.text().strip() or 'TCO_*_KMC_*.xml',
                'case_sensitive': self.case_sensitive.isChecked(),
                'find_all_matches': self.find_all_matches.isChecked(),
                'max_threads': self.max_threads.value()
            }
            
            self.settings['ui'] = {
                'last_date_range': self.date_range_combo.currentText(),
                'last_search_mode': self.search_mode.currentText()
            }
            
            # Save to file
            if self.settings_manager.save_settings(self.settings):
                QMessageBox.information(self, "Success", "Settings saved successfully!")
            else:
                QMessageBox.warning(self, "Warning", "Failed to save settings.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving settings: {str(e)}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "Confirm Reset", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to defaults
            self.settings = self.settings_manager.default_settings.copy()
            self.load_saved_settings()
            QMessageBox.information(self, "Success", "Settings reset to defaults!")
    
    def auto_connect_if_possible(self):
        """Auto-connect to FTP if credentials are available"""
        try:
            ftp_settings = self.settings.get('ftp', {})
            
            # Check if we have complete FTP settings
            if (ftp_settings.get('host') and 
                ftp_settings.get('username') and 
                ftp_settings.get('password') and 
                ftp_settings.get('remember_password', False)):
                
                host = ftp_settings['host']
                port = ftp_settings.get('port', 21)
                username = ftp_settings['username']
                password = ftp_settings['password']
                
                # Try to connect automatically
                self.update_connection_status("Auto-connecting...", 'info')
                
                success = self.ftp_manager.connect(host, port, username, password)
                
                if success:
                    self.update_connection_status("✓ Connected", 'success')
                    self.connect_button.setText("Disconnect")
                    self.connect_button.setStyleSheet(BUTTON_STYLES['error'])
                    # Don't show popup for auto-connect
                else:
                    self.update_connection_status("Auto-connect failed", 'error')
                    self.connect_button.setText("Connect")
                    self.connect_button.setStyleSheet(BUTTON_STYLES['success'])
                    
            else:
                self.update_connection_status("No saved credentials", 'warning')
                
        except Exception as e:
            self.update_connection_status("Auto-connect error", 'error')

    def set_window_icon(self):
        """Set window icon from Resource folder"""
        try:
            # Get the directory containing the script
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            icon_path = os.path.join(base_dir, "Resource", "icon.ico")
            
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                # Also set for the application (taskbar)
                if hasattr(self, 'app'):
                    self.app.setWindowIcon(icon)
            else:
                print(f"Icon not found at: {icon_path}")
                
        except Exception as e:
            print(f"Error setting icon: {e}")
    
    def setup_custom_logging(self):
        """Setup custom logging to capture and display logs in UI"""
        class UILogHandler(logging.Handler):
            def __init__(self, main_window):
                super().__init__()
                self.main_window = main_window
                
            def emit(self, record):
                try:
                    # Format the log message
                    msg = self.format(record)
                    level = record.levelname
                    
                    # Send to main window for display
                    self.main_window.add_log_message(msg, level)
                    
                    # Update statistics based on log content
                    self.main_window.update_log_statistics(msg, level)
                    
                except Exception:
                    pass  # Prevent logging errors from breaking the app
        
        # Create and configure handler
        self.ui_log_handler = UILogHandler(self)
        self.ui_log_handler.setLevel(logging.INFO)
        
        # Format: timestamp - level - message
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                    datefmt='%H:%M:%S')
        self.ui_log_handler.setFormatter(formatter)
        
        # Add handler to root logger to catch all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(self.ui_log_handler)
        
        # Also add to specific loggers we care about
        for logger_name in ['src.core.ftp_manager', 'src.core.search_worker', 
                           'src.core.search_engine']:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
    
    def add_log_message(self, message: str, level: str):
        """Add a log message to the log display with color coding"""
        if not hasattr(self, 'log_display'):
            return
            
        # Color coding based on log level
        color_map = {
            'INFO': COLORS['text_primary'],
            'WARNING': COLORS['warning'],
            'ERROR': COLORS['error'],
            'DEBUG': COLORS['text_secondary'],
            'CRITICAL': COLORS['error']
        }
        
        color = color_map.get(level, COLORS['text_primary'])
        
        # Format message with HTML for coloring
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_msg = f'<span style="color: {color};">[{level}] {message}</span>'
        
        # Add to log display (use QTextEdit's HTML capabilities)
        self.log_display.append(formatted_msg)
        
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.End)
        self.log_display.setTextCursor(cursor)
    
    def update_log_statistics(self, message: str, level: str):
        """Update log statistics based on message content"""
        msg_lower = message.lower()
        
        # Track different types of events
        if 'found' in msg_lower and 'directories' in msg_lower:
            try:
                # Extract number from messages like "Found 5 directories"
                import re
                match = re.search(r'found (\d+)', msg_lower)
                if match:
                    self.log_stats['directories'] = int(match.group(1))
            except:
                pass
                
        elif 'found' in msg_lower and 'xml files' in msg_lower:
            try:
                # Extract number from messages like "Found 150 XML files"
                import re
                match = re.search(r'found (\d+)', msg_lower)
                if match:
                    self.log_stats['xml_files'] += int(match.group(1))
            except:
                pass
                
        elif 'search completed' in msg_lower and 'result: found' in msg_lower:
            self.log_stats['processed'] += 1
            
        elif level == 'ERROR' and any(keyword in msg_lower for keyword in 
                                     ['connection', '10060', 'timeout', 'host']):
            self.log_stats['connection_issues'] += 1
            self.log_stats['failed'] += 1
            
        elif level == 'ERROR':
            self.log_stats['failed'] += 1
        
        # Update statistics display
        self.update_statistics_display()
    
    def update_statistics_display(self):
        """Update the statistics labels"""
        if hasattr(self, 'stats_directories'):
            self.stats_directories.setText(f"📁 Directories: {self.log_stats['directories']}")
            self.stats_xml_files.setText(f"📄 XML Files: {self.log_stats['xml_files']}")
            self.stats_processed.setText(f"✅ Processed: {self.log_stats['processed']}")
            self.stats_failed.setText(f"❌ Failed: {self.log_stats['failed']}")
            self.stats_connections.setText(f"🔌 Connection Issues: {self.log_stats['connection_issues']}")
    
    def clear_logs(self):
        """Clear log display and reset statistics"""
        if hasattr(self, 'log_display'):
            self.log_display.clear()
        
        # Reset statistics
        self.log_stats = {
            'directories': 0,
            'xml_files': 0,
            'processed': 0,
            'failed': 0,
            'connection_issues': 0
        }
        
        self.update_statistics_display()
        
        # Add initial log message
        self.add_log_message("Logs cleared", "INFO")
