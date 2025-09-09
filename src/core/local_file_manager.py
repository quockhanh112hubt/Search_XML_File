"""
Local File Manager Module
Handles local directory traversal and XML file discovery
"""

import os
import logging
from typing import List, Tuple, Generator, Optional
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class LocalFileManager:
    """Manager for local XML file operations"""
    
    def __init__(self):
        self.base_directory = None
        self.total_files_found = 0
        self.processed_files = 0
        
    def set_base_directory(self, directory: str) -> bool:
        """Set and validate the base directory for searching"""
        try:
            if not os.path.exists(directory):
                logger.error(f"Directory does not exist: {directory}")
                return False
                
            if not os.path.isdir(directory):
                logger.error(f"Path is not a directory: {directory}")
                return False
                
            self.base_directory = os.path.abspath(directory)
            logger.info(f"Base directory set to: {self.base_directory}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting base directory: {e}")
            return False
    
    def discover_xml_files(self, file_pattern: str = None) -> List[Tuple[str, int]]:
        """
        Discover all XML files in the base directory and subdirectories
        Returns list of (filepath, size) tuples
        """
        if not self.base_directory:
            logger.error("Base directory not set")
            return []
        
        xml_files = []
        logger.info(f"Discovering XML files in: {self.base_directory}")
        
        try:
            # Debug: Check if directory exists and is accessible
            if not os.path.exists(self.base_directory):
                logger.error(f"Directory does not exist: {self.base_directory}")
                return []
            
            if not os.path.isdir(self.base_directory):
                logger.error(f"Path is not a directory: {self.base_directory}")
                return []
            
            logger.debug(f"Directory exists and is accessible: {self.base_directory}")
            
            for root, dirs, files in os.walk(self.base_directory):
                logger.debug(f"Walking directory: {root}, found {len(files)} files")
                
                # Filter XML files
                for file in files:
                    logger.debug(f"Checking file: {file}")
                    
                    if file.lower().endswith('.xml'):
                        logger.debug(f"Found XML file: {file}")
                        
                        # Apply file pattern filter if provided
                        if file_pattern and file_pattern.strip():
                            import fnmatch
                            if not fnmatch.fnmatch(file, file_pattern):
                                logger.debug(f"File {file} does not match pattern {file_pattern}")
                                continue
                        
                        full_path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(full_path)
                            # Store relative path from base directory
                            rel_path = os.path.relpath(full_path, self.base_directory)
                            xml_files.append((rel_path, size))
                            logger.debug(f"Added XML file: {rel_path} ({size} bytes)")
                            
                        except OSError as e:
                            logger.warning(f"Cannot access file {full_path}: {e}")
                            continue
                    else:
                        logger.debug(f"File {file} is not XML")
            
            logger.info(f"Found {len(xml_files)} XML files")
            self.total_files_found = len(xml_files)
            return xml_files
            
        except Exception as e:
            logger.error(f"Error discovering XML files: {e}")
            return []
    
    def get_file_stream(self, relative_path: str):
        """
        Get file content for reading (simplified approach like SearchXML.py)
        Returns file content as string or None
        """
        if not self.base_directory:
            logger.error("Base directory not set")
            return None
        
        full_path = os.path.join(self.base_directory, relative_path)
        
        try:
            if not os.path.exists(full_path):
                logger.error(f"File not found: {full_path}")
                return None
            
            # Read file content directly with UTF-8 encoding (like SearchXML.py)
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.debug(f"Successfully read file: {relative_path} ({len(content)} characters)")
                return content
                
        except Exception as e:
            logger.error(f"Error reading file {relative_path}: {e}")
            return None
    
    def release_file_stream(self, file_identifier):
        """
        Release file stream (no-op for local files, but maintains interface compatibility)
        """
        # Local files don't need explicit release, but log for consistency
        if file_identifier:
            logger.debug(f"Released local file stream: {os.path.basename(file_identifier)}")
    
    def get_file_info(self, relative_path: str) -> dict:
        """Get file information"""
        if not self.base_directory:
            return {}
        
        full_path = os.path.join(self.base_directory, relative_path)
        
        try:
            if not os.path.exists(full_path):
                return {}
            
            stat = os.stat(full_path)
            return {
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'full_path': full_path,
                'relative_path': relative_path,
                'directory': os.path.dirname(relative_path),
                'filename': os.path.basename(relative_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {relative_path}: {e}")
            return {}
    
    def scan_directory_statistics(self) -> dict:
        """Get directory scanning statistics"""
        if not self.base_directory:
            return {'error': 'No base directory set'}
        
        stats = {
            'base_directory': self.base_directory,
            'total_directories': 0,
            'total_files': 0,
            'xml_files': 0,
            'total_size': 0,
            'largest_file': {'name': '', 'size': 0},
            'scan_time': 0
        }
        
        start_time = time.time()
        
        try:
            for root, dirs, files in os.walk(self.base_directory):
                stats['total_directories'] += 1
                
                for file in files:
                    stats['total_files'] += 1
                    
                    if file.lower().endswith('.xml'):
                        stats['xml_files'] += 1
                    
                    try:
                        full_path = os.path.join(root, file)
                        size = os.path.getsize(full_path)
                        stats['total_size'] += size
                        
                        if size > stats['largest_file']['size']:
                            stats['largest_file'] = {
                                'name': file,
                                'size': size,
                                'path': os.path.relpath(full_path, self.base_directory)
                            }
                    except OSError:
                        continue
            
            stats['scan_time'] = time.time() - start_time
            
            logger.info(f"Directory scan complete: {stats['xml_files']} XML files "
                       f"in {stats['total_directories']} directories "
                       f"(scan took {stats['scan_time']:.2f}s)")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error scanning directory statistics: {e}")
            stats['error'] = str(e)
            return stats
    
    def validate_xml_files(self, xml_files: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        """Validate that XML files are accessible and readable"""
        valid_files = []
        
        for rel_path, size in xml_files:
            full_path = os.path.join(self.base_directory, rel_path)
            
            try:
                # Quick accessibility check
                with open(full_path, 'rb') as f:
                    f.read(1)  # Try to read first byte
                
                valid_files.append((rel_path, size))
                
            except Exception as e:
                logger.warning(f"Skipping inaccessible file {rel_path}: {e}")
                continue
        
        logger.info(f"Validated {len(valid_files)}/{len(xml_files)} XML files")
        return valid_files


class LocalSearchResult:
    """Local search result container"""
    
    def __init__(self, relative_path: str, filename: str, match_type: str, 
                 match_content: str = "", line_number: int = 0):
        self.relative_path = relative_path
        self.filename = filename
        self.match_type = match_type
        self.match_content = match_content
        self.line_number = line_number
        self.date_dir = os.path.dirname(relative_path) or "root"  # Use directory as "date_dir"
        self.file_path = relative_path
