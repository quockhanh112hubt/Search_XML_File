"""
Main Window UI for XML Search Application
"""

import sys
import os
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
from config.settings import (
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, DEFAULT_FILE_PATTERN, 
    MAX_WORKER_THREADS
)

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
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("XML Search Tool - FTP Server File Search")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
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
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
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
        search_layout.addWidget(self.case_sensitive, 2, 2)
        
        search_layout.addWidget(QLabel("Max Threads:"), 3, 0)
        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 20)
        self.max_threads.setValue(MAX_WORKER_THREADS)
        search_layout.addWidget(self.max_threads, 3, 1)
        
        layout.addWidget(search_group)
        
        # Search controls
        controls_layout = QHBoxLayout()
        
        self.search_button = QPushButton("Start Search")
        self.search_button.setStyleSheet("QPushButton { font-weight: bold; }")
        controls_layout.addWidget(self.search_button)
        
        self.stop_button = QPushButton("Stop Search")
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
        
        # Test connection button
        self.test_connection_button = QPushButton("Test Connection")
        ftp_layout.addWidget(self.test_connection_button, 2, 0, 1, 2)
        
        self.connection_status = QLabel("Not connected")
        ftp_layout.addWidget(self.connection_status, 2, 2, 1, 2)
        
        layout.addWidget(ftp_group)
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
        controls_layout.addWidget(self.results_count_label)
        
        controls_layout.addStretch()
        
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setEnabled(False)
        controls_layout.addWidget(self.export_csv_button)
        
        self.export_excel_button = QPushButton("Export Excel")
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
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.results_table)
        
        # Add to tab
        self.tab_widget.addTab(results_widget, "Results")
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Search controls
        self.search_button.clicked.connect(self.start_search)
        self.stop_button.clicked.connect(self.stop_search)
        
        # FTP settings
        self.test_connection_button.clicked.connect(self.test_ftp_connection)
        
        # Date range
        self.date_range_combo.currentTextChanged.connect(self.on_date_range_changed)
        
        # Export buttons
        self.export_csv_button.clicked.connect(self.export_csv)
        self.export_excel_button.clicked.connect(self.export_excel)
        
    def on_date_range_changed(self, range_text: str):
        """Handle date range combo change"""
        if range_text != "Custom Range":
            try:
                start_date, end_date = parse_date_range(range_text)
                self.start_date.setDate(QDate(start_date))
                self.end_date.setDate(QDate(end_date))
            except:
                pass
    
    def test_ftp_connection(self):
        """Test FTP connection"""
        host = self.ftp_host.text().strip()
        port = self.ftp_port.value()
        username = self.ftp_username.text().strip()
        password = self.ftp_password.text()
        
        if not all([host, username, password]):
            QMessageBox.warning(self, "Warning", "Please fill in all FTP connection fields")
            return
        
        self.test_connection_button.setEnabled(False)
        self.connection_status.setText("Testing...")
        
        # Test connection
        try:
            if self.ftp_manager.connect(host, port, username, password):
                self.connection_status.setText("✓ Connected")
                self.connection_status.setStyleSheet("color: green;")
                QMessageBox.information(self, "Success", "FTP connection successful!")
            else:
                self.connection_status.setText("✗ Failed")
                self.connection_status.setStyleSheet("color: red;")
                QMessageBox.warning(self, "Error", "FTP connection failed!")
                
        except Exception as e:
            self.connection_status.setText("✗ Error")
            self.connection_status.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            
        finally:
            self.test_connection_button.setEnabled(True)
    
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
            'max_threads': self.max_threads.value()
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
        self.update_results_count()
        
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
        self.update_results_count()
        
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
    
    def update_results_count(self):
        """Update results count label"""
        count = len(self.search_results)
        self.results_count_label.setText(f"Results: {count}")
    
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
