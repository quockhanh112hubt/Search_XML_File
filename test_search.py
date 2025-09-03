#!/usr/bin/env python3
"""
Quick test script for SearchResult functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_search_result():
    """Test SearchResult creation and attributes"""
    print("Testing SearchResult object...")
    
    try:
        from src.core.search_engine import SearchResult
        
        # Create a test SearchResult
        result = SearchResult(
            date_dir="20250903",
            filename="test_file.xml", 
            match_type="Text Match",
            match_content="This is a test match",
            line_number=42
        )
        
        # Test all attributes
        print(f"date_dir: {result.date_dir}")
        print(f"filename: {result.filename}")
        print(f"file_path: {result.file_path}")
        print(f"match_type: {result.match_type}")
        print(f"match_content: {result.match_content}")
        print(f"line_number: {result.line_number}")
        
        # Verify all attributes exist
        required_attrs = ['date_dir', 'filename', 'file_path', 'match_type', 'match_content', 'line_number']
        for attr in required_attrs:
            if hasattr(result, attr):
                print(f"✓ {attr} exists")
            else:
                print(f"✗ {attr} missing")
                return False
                
        print("✅ SearchResult test passed!")
        return True
        
    except Exception as e:
        print(f"❌ SearchResult test failed: {e}")
        return False

def test_search_engine_factory():
    """Test SearchEngine factory methods"""
    print("\nTesting SearchEngine factory...")
    
    try:
        from src.core.search_engine import SearchEngineFactory
        
        # Test text search
        text_engine = SearchEngineFactory.create_text_search(["test"], case_sensitive=False)
        print(f"✓ Text search engine created: {type(text_engine)}")
        
        # Test regex search  
        regex_engine = SearchEngineFactory.create_text_search([r"\d+"], use_regex=True)
        print(f"✓ Regex search engine created: {type(regex_engine)}")
        
        # Test xpath search
        xpath_engine = SearchEngineFactory.create_xpath_search(["//test"])
        print(f"✓ XPath search engine created: {type(xpath_engine)}")
        
        print("✅ SearchEngine factory test passed!")
        return True
        
    except Exception as e:
        print(f"❌ SearchEngine factory test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Quick Search Component Test\n")
    
    success1 = test_search_result()
    success2 = test_search_engine_factory()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Search components are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
