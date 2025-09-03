"""
Example usage and testing script for XML Search Tool
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.dirname(__file__))

def test_date_utilities():
    """Test date utility functions"""
    print("Testing date utilities...")
    
    from src.utils.date_utils import parse_date_range, format_date_for_ftp
    
    # Test various date ranges
    ranges = ["Today", "Yesterday", "Last 7 Days", "This Month"]
    for range_text in ranges:
        start, end = parse_date_range(range_text)
        print(f"{range_text}: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    
    # Test FTP date formatting
    test_date = datetime(2025, 9, 3)
    ftp_format = format_date_for_ftp(test_date)
    print(f"FTP format for {test_date}: {ftp_format}")
    print()

def test_search_engine():
    """Test search engine creation"""
    print("Testing search engines...")
    
    from src.core.search_engine import SearchEngineFactory
    
    # Test text search
    keywords = ["test", "search", "data"]
    engine = SearchEngineFactory.create_text_search(keywords, case_sensitive=False)
    print(f"Text search engine created with keywords: {engine.keywords}")
    
    # Test regex search
    patterns = [r"\d{4}", r"test.*pattern"]
    regex_engine = SearchEngineFactory.create_text_search(patterns, use_regex=True)
    print(f"Regex search engine created with {len(regex_engine.compiled_patterns)} patterns")
    
    # Test XPath search
    xpath_expressions = ["//data", "//record[@type='test']"]
    xpath_engine = SearchEngineFactory.create_xpath_search(xpath_expressions)
    print(f"XPath search engine created with expressions: {xpath_engine.xpath_expressions}")
    print()

def test_export_functionality():
    """Test export functionality"""
    print("Testing export functionality...")
    
    from src.core.search_engine import SearchResult
    from src.utils.export_utils import ResultExporter
    import tempfile
    
    # Create sample results
    results = [
        SearchResult("20250903", "test1.xml", "Text Match", "sample content 1", 10),
        SearchResult("20250904", "test2.xml", "Regex Match", "sample content 2", 20),
        SearchResult("20250905", "test3.xml", "XPath Match", "sample content 3", 30)
    ]
    
    # Test CSV export
    csv_file = tempfile.mktemp(suffix='.csv')
    try:
        ResultExporter.export_to_csv(results, csv_file)
        with open(csv_file, 'r', encoding='utf-8') as f:
            print(f"CSV export successful. First few lines:")
            for i, line in enumerate(f):
                if i < 3:  # Show first 3 lines
                    print(f"  {line.strip()}")
    except Exception as e:
        print(f"CSV export failed: {e}")
    finally:
        if os.path.exists(csv_file):
            os.unlink(csv_file)
    
    print()

def print_project_structure():
    """Print project structure overview"""
    print("Project Structure:")
    print("""
XML Search Tool
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
├── config/
│   └── settings.py        # Configuration settings
├── src/
│   ├── core/
│   │   ├── ftp_manager.py    # FTP connection management
│   │   ├── search_engine.py  # Search algorithms (Text, Regex, XPath)
│   │   └── search_worker.py  # Multi-threaded search coordinator
│   ├── ui/
│   │   └── main_window.py    # PyQt5 main window and UI components
│   └── utils/
│       ├── export_utils.py   # CSV/Excel export functionality
│       ├── date_utils.py     # Date parsing and formatting
│       └── logging_config.py # Logging configuration
└── tests/
    └── test_basic.py      # Unit tests
    """)

def main():
    """Main demo function"""
    print("XML Search Tool - Demo & Testing")
    print("=" * 50)
    print()
    
    print_project_structure()
    print()
    
    print("Running component tests...")
    print("-" * 30)
    
    try:
        test_date_utilities()
        test_search_engine() 
        test_export_functionality()
        
        print("All tests completed successfully!")
        print()
        print("To run the full application:")
        print("  python main.py")
        print()
        print("To run unit tests:")
        print("  python tests/test_basic.py")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required dependencies:")
        print("  pip install -r requirements.txt")
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    main()
