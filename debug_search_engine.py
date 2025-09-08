#!/usr/bin/env python3
"""
Debug script to test search engine with a simple string
"""

import logging
import io
from src.core.search_engine import SearchEngineFactory

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_search_engine():
    """Test search engine with simple data"""
    
    # Sample XML content similar to real files
    sample_xml = """<?xml version="1.0" standalone="yes"?>
<TCO_SEND_Data>
    <Header>
        <MessageID>12345</MessageID>
        <Timestamp>2024-08-02T08:28:18</Timestamp>
    </Header>
    <Body>
        <Data>
            <Field1>Some text with keyword 1.0 here</Field1>
            <Field2>Another field</Field2>
        </Data>
    </Body>
</TCO_SEND_Data>""".encode('utf-8')
    
    print(f"Sample XML size: {len(sample_xml)} bytes")
    print("Sample XML content preview:")
    print(sample_xml[:200].decode('utf-8'))
    
    # Create search engine
    search_engine = SearchEngineFactory.create_text_search(
        keywords=["1.0"], 
        case_sensitive=False, 
        use_regex=False
    )
    
    print("\n=== Testing with early_termination=True ===")
    
    # Create a simple stream function
    def create_stream_func(data):
        def stream_func(callback):
            print(f"Stream function called, data size: {len(data)}")
            # Send data in chunks
            chunk_size = 1024
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                print(f"Sending chunk {i//chunk_size + 1}, size: {len(chunk)}")
                callback(chunk)
            print("Stream function completed")
        return stream_func
    
    stream_func = create_stream_func(sample_xml)
    
    try:
        print("Starting search with early_termination=True...")
        result = search_engine.search_in_stream(
            stream_func, 
            "20240802", 
            "test.xml", 
            early_termination=True
        )
        print(f"Search result (early_termination=True): {result}")
        if result:
            print(f"  Match type: {result.match_type}")
            print(f"  Match content: {result.match_content}")
            print(f"  Line: {result.line_number}")
    except Exception as e:
        print(f"Error in search (early_termination=True): {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing with early_termination=False ===")
    
    try:
        print("Starting search with early_termination=False...")
        result = search_engine.search_in_stream(
            stream_func, 
            "20240802", 
            "test.xml", 
            early_termination=False
        )
        print(f"Search result (early_termination=False): {result}")
        if result:
            print(f"  Match type: {result.match_type}")
            print(f"  Match content: {result.match_content}")
            print(f"  Line: {result.line_number}")
    except Exception as e:
        print(f"Error in search (early_termination=False): {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_engine()
