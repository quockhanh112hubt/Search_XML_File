"""
Basic unit tests for XML Search Application
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta

# Test imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.date_utils import parse_date_range, format_date_for_display, format_date_for_ftp
from src.core.search_engine import TextSearchEngine, SearchEngineFactory

class TestDateUtils(unittest.TestCase):
    """Test date utility functions"""
    
    def test_parse_date_range_today(self):
        """Test parsing 'Today' range"""
        start, end = parse_date_range("Today")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(start, today)
        self.assertEqual(end, today)
    
    def test_parse_date_range_last_7_days(self):
        """Test parsing 'Last 7 Days' range"""
        start, end = parse_date_range("Last 7 Days")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        expected_start = today - timedelta(days=6)
        self.assertEqual(start, expected_start)
        self.assertEqual(end, today)
    
    def test_format_date_for_ftp(self):
        """Test FTP date formatting"""
        test_date = datetime(2025, 9, 3)
        formatted = format_date_for_ftp(test_date)
        self.assertEqual(formatted, "20250903")

class TestSearchEngine(unittest.TestCase):
    """Test search engine functionality"""
    
    def test_text_search_engine_creation(self):
        """Test creating text search engine"""
        keywords = ["test", "search"]
        engine = SearchEngineFactory.create_text_search(keywords, case_sensitive=False)
        self.assertIsInstance(engine, TextSearchEngine)
        self.assertEqual(engine.keywords, keywords)
        self.assertFalse(engine.case_sensitive)
    
    def test_text_search_engine_regex(self):
        """Test creating regex search engine"""
        patterns = [r"\d+", r"test.*pattern"]
        engine = SearchEngineFactory.create_text_search(patterns, use_regex=True)
        self.assertTrue(engine.use_regex)
        self.assertEqual(len(engine.compiled_patterns), 2)

class TestExportUtils(unittest.TestCase):
    """Test export functionality"""
    
    def setUp(self):
        """Setup test data"""
        from src.core.search_engine import SearchResult
        self.test_results = [
            SearchResult("20250903", "test1.xml", "Text Match", "test content", 10),
            SearchResult("20250904", "test2.xml", "Regex Match", "regex match", 20)
        ]
    
    def test_csv_export(self):
        """Test CSV export functionality"""
        from src.utils.export_utils import ResultExporter
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            ResultExporter.export_to_csv(self.test_results, temp_file)
            
            # Check if file was created and has content
            self.assertTrue(os.path.exists(temp_file))
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("test1.xml", content)
                self.assertIn("test2.xml", content)
                self.assertIn("Text Match", content)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

if __name__ == '__main__':
    unittest.main()
