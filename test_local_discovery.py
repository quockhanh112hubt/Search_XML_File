#!/usr/bin/env python3
"""
Test script for local file discovery
"""
import os
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.local_file_manager import LocalFileManager
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

def test_discovery(directory):
    print(f"\n=== Testing directory: {directory} ===")
    
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"ERROR: Directory does not exist: {directory}")
        return
    
    # Manual check
    print("Manual file check:")
    try:
        for root, dirs, files in os.walk(directory):
            xml_files = [f for f in files if f.lower().endswith('.xml')]
            print(f"  {root}: {len(xml_files)} XML files")
            for xml_file in xml_files[:3]:  # Show first 3
                print(f"    - {xml_file}")
            if len(xml_files) > 3:
                print(f"    ... and {len(xml_files) - 3} more")
    except Exception as e:
        print(f"Manual check failed: {e}")
        return
    
    # Test LocalFileManager
    print("\nLocalFileManager test:")
    manager = LocalFileManager()
    success = manager.set_base_directory(directory)
    print(f"Set base directory: {success}")
    
    if success:
        xml_files = manager.discover_xml_files()
        print(f"Discovered: {len(xml_files)} XML files")
        for i, (rel_path, size) in enumerate(xml_files[:3]):
            print(f"  {i+1}. {rel_path} ({size} bytes)")
        if len(xml_files) > 3:
            print(f"  ... and {len(xml_files) - 3} more")

if __name__ == "__main__":
    # Test directories
    test_dirs = [
        r"E:\XML\20240802\Send File",
        r"E:\XML",
    ]
    
    for test_dir in test_dirs:
        test_discovery(test_dir)
