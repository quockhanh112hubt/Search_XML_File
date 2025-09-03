"""
Search Worker Module
Handles multi-threaded search operations
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from threading import Event, Lock
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .ftp_manager import FTPManager
from .search_engine import SearchEngineFactory, SearchResult
from config.settings import MAX_WORKER_THREADS, MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

class SearchProgress:
    """Thread-safe search progress tracker"""
    
    def __init__(self):
        self.lock = Lock()
        self.directories_total = 0
        self.directories_processed = 0
        self.files_total = 0
        self.files_processed = 0
        self.matches_found = 0
        self.current_directory = ""
        self.current_file = ""
        self.start_time = None
        self.errors = []
    
    def set_totals(self, directories: int, files: int):
        with self.lock:
            self.directories_total = directories
            self.files_total = files
            self.start_time = time.time()
    
    def update_directory(self, directory: str):
        with self.lock:
            self.current_directory = directory
            self.directories_processed += 1
    
    def update_file(self, filename: str):
        with self.lock:
            self.current_file = filename
            self.files_processed += 1
    
    def add_match(self):
        with self.lock:
            self.matches_found += 1
    
    def add_error(self, error: str):
        with self.lock:
            self.errors.append(error)
    
    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            return {
                'directories_processed': self.directories_processed,
                'directories_total': self.directories_total,
                'files_processed': self.files_processed,
                'files_total': self.files_total,
                'matches_found': self.matches_found,
                'current_directory': self.current_directory,
                'current_file': self.current_file,
                'elapsed_time': elapsed,
                'errors_count': len(self.errors)
            }

class SearchWorker:
    """Main search worker coordinating the search operation"""
    
    def __init__(self, ftp_manager: FTPManager):
        self.ftp_manager = ftp_manager
        self.progress = SearchProgress()
        self.results = []
        self.results_lock = Lock()
        self.stop_event = Event()
        
    def search(self, search_params: Dict[str, Any], 
               progress_callback: Optional[Callable] = None) -> List[SearchResult]:
        """
        Execute search with given parameters
        
        Args:
            search_params: Dictionary containing:
                - start_date: datetime
                - end_date: datetime
                - keywords: List[str]
                - search_mode: str ('text', 'regex', 'xpath')
                - case_sensitive: bool
                - file_pattern: str
                - max_threads: int
            progress_callback: Function to call with progress updates
        """
        
        self.results = []
        self.stop_event.clear()
        
        try:
            # Extract parameters
            start_date = search_params['start_date']
            end_date = search_params['end_date']
            keywords = search_params['keywords']
            search_mode = search_params.get('search_mode', 'text')
            case_sensitive = search_params.get('case_sensitive', False)
            file_pattern = search_params.get('file_pattern', '')
            max_threads = search_params.get('max_threads', MAX_WORKER_THREADS)
            
            # Validate parameters
            if not keywords:
                raise ValueError("No keywords provided")
            
            # Get date directories
            logger.info(f"Searching from {start_date} to {end_date}")
            date_directories = self.ftp_manager.list_date_directories(start_date, end_date)
            
            if not date_directories:
                logger.warning("No directories found in date range")
                return []
            
            # Collect all files to process
            all_tasks = []
            total_files = 0
            
            for date_dir in date_directories:
                if self.stop_event.is_set():
                    break
                    
                files = self.ftp_manager.list_xml_files(date_dir, file_pattern)
                for filename, file_size in files:
                    # Skip very large files
                    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                        logger.warning(f"Skipping large file: {filename} ({file_size} bytes)")
                        continue
                    
                    all_tasks.append((date_dir, filename, file_size))
                    total_files += 1
            
            # Initialize progress
            self.progress.set_totals(len(date_directories), total_files)
            
            # Create search engine
            search_engine = self._create_search_engine(keywords, search_mode, case_sensitive)
            
            # Execute search with thread pool
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(self._search_file, task, search_engine): task 
                    for task in all_tasks
                }
                
                # Process completed tasks
                for future in as_completed(future_to_task):
                    if self.stop_event.is_set():
                        break
                        
                    task = future_to_task[future]
                    date_dir, filename, _ = task
                    
                    try:
                        result = future.result()
                        if result:
                            with self.results_lock:
                                self.results.append(result)
                            self.progress.add_match()
                        
                        self.progress.update_file(filename)
                        
                        # Call progress callback
                        if progress_callback:
                            progress_callback(self.progress.get_status())
                            
                    except Exception as e:
                        error_msg = f"Error processing {filename}: {e}"
                        logger.error(error_msg)
                        self.progress.add_error(error_msg)
            
            logger.info(f"Search completed. Found {len(self.results)} matches.")
            return self.results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _create_search_engine(self, keywords: List[str], search_mode: str, 
                             case_sensitive: bool):
        """Create appropriate search engine based on mode"""
        if search_mode == 'xpath':
            return SearchEngineFactory.create_xpath_search(keywords)
        elif search_mode == 'regex':
            return SearchEngineFactory.create_text_search(
                keywords, case_sensitive, use_regex=True
            )
        else:  # text
            return SearchEngineFactory.create_text_search(
                keywords, case_sensitive, use_regex=False
            )
    
    def _search_file(self, task, search_engine) -> Optional[SearchResult]:
        """Search a single file"""
        date_dir, filename, file_size = task
        
        if self.stop_event.is_set():
            return None
            
        try:
            # Get file stream
            conn, stream_func = self.ftp_manager.get_file_stream(date_dir, filename)
            if not conn or not stream_func:
                return None
            
            try:
                # Search in stream
                result = search_engine.search_in_stream(stream_func, date_dir, filename)
                return result
                
            finally:
                # Always release connection
                self.ftp_manager.release_file_stream(conn)
                
        except Exception as e:
            logger.error(f"Error searching file {filename}: {e}")
            return None
    
    def stop(self):
        """Stop the search operation"""
        self.stop_event.set()
        logger.info("Search stop requested")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress"""
        return self.progress.get_status()
    
    def get_results(self) -> List[SearchResult]:
        """Get search results"""
        with self.results_lock:
            return self.results.copy()
