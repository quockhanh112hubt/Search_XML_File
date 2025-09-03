#!/usr/bin/env python3
"""
Debug search functionality to identify why only 5 files found
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_ftp_files():
    """Debug FTP file listing"""
    from src.core.ftp_manager import FTPManager
    from datetime import datetime, timedelta
    
    print("=== Debug FTP File Listing ===")
    
    # Test connection (you'll need to provide real FTP details)
    ftp_manager = FTPManager()
    
    # You can set test connection here
    host = "192.168.110.12"  # Replace with your FTP host
    port = 21
    username = "your_username"  # Replace
    password = "your_password"  # Replace
    
    print(f"Connecting to {host}:{port}...")
    
    if ftp_manager.connect(host, port, username, password):
        print("✓ FTP connected successfully")
        
        # Test date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last 7 days
        
        print(f"Searching date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # List date directories
        date_dirs = ftp_manager.list_date_directories(start_date, end_date, "SAMSUNG")
        print(f"Found {len(date_dirs)} date directories: {date_dirs}")
        
        total_files = 0
        for date_dir in date_dirs[:3]:  # Check first 3 directories
            print(f"\n--- Directory: {date_dir} ---")
            files = ftp_manager.list_xml_files(date_dir, "TCO_*_KMC_*.xml", "SAMSUNG", "Send File")
            print(f"Files in {date_dir}: {len(files)}")
            total_files += len(files)
            
            # Show first few files
            for i, (filename, size) in enumerate(files[:5]):
                print(f"  {i+1}. {filename} ({size} bytes)")
            
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")
        
        print(f"\nTotal XML files found: {total_files}")
        ftp_manager.disconnect()
        
    else:
        print("✗ FTP connection failed")

def debug_search_engine():
    """Debug search engine behavior"""
    print("\n=== Debug Search Engine ===")
    
    from src.core.search_engine import SearchEngineFactory
    
    # Test text search engine
    keywords = ["5"]
    engine = SearchEngineFactory.create_text_search(keywords, case_sensitive=False)
    print(f"Created text search engine for keywords: {keywords}")
    
    # Test with sample XML content
    sample_xml = b"""<?xml version="1.0"?>
    <root>
        <data id="5">Sample data 5</data>
        <item value="5">Another 5 here</item>
        <number>12345</number>
    </root>"""
    
    class MockStreamFunc:
        def __init__(self, data):
            self.data = data
            
        def __call__(self, callback):
            callback(self.data)
    
    stream_func = MockStreamFunc(sample_xml)
    result = engine.search_in_stream(stream_func, "20250903", "test.xml", early_termination=True)
    
    if result:
        print(f"✓ Found match: {result.match_content}")
    else:
        print("✗ No match found")

def debug_real_search():
    """Debug real search with your FTP server"""
    print("\n=== Debug Real Search ===")
    
    from src.core.ftp_manager import FTPManager
    from src.core.search_worker import SearchWorker
    from datetime import datetime, timedelta
    import logging
    
    # Enable debug logging
    logging.getLogger('src.core.search_worker').setLevel(logging.DEBUG)
    
    ftp_manager = FTPManager()
    
    # Replace with your actual FTP credentials
    host = "192.168.110.12"
    port = 21
    username = "your_username"  # Replace
    password = "your_password"  # Replace
    
    if ftp_manager.connect(host, port, username, password):
        print("✓ FTP connected")
        
        search_worker = SearchWorker(ftp_manager)
        
        search_params = {
            'start_date': datetime(2024, 8, 1).date(),
            'end_date': datetime.now().date(),
            'keywords': ['5'],
            'search_mode': 'text',
            'case_sensitive': False,
            'file_pattern': 'TCO_*_KMC_*.xml',
            'max_threads': 4,
            'source_directory': 'SAMSUNG',
            'send_file_directory': 'Send File'
        }
        
        print("Starting search...")
        results = search_worker.search(search_params)
        
        print(f"\n=== Search Results ===")
        print(f"Total matches found: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"{i+1}. {result.filename} - {result.match_type}: {result.match_content[:50]}...")
        
        ftp_manager.disconnect()
    else:
        print("✗ FTP connection failed")

if __name__ == "__main__":
    print("🔍 XML Search Tool - Debug Mode\n")
    
    # Uncomment to test specific functions
    debug_search_engine()
    # debug_real_search()  # Requires real FTP credentials
    
    print("\nDebug completed.")
