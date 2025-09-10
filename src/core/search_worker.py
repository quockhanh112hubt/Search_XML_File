"""
Search Worker Module
Handles multi-threaded search operations
"""

import time
import logging
import threading
import os
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from threading import Event, Lock
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .ftp_manager import FTPManager
from .local_file_manager import LocalFileManager, LocalSearchResult
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
    
    def __init__(self, ftp_manager: FTPManager = None):
        self.ftp_manager = ftp_manager
        self.local_file_manager = LocalFileManager()
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
                - search_source: str ('FTP Server (Content)', 'Local Directory', 'FTP Server (Filename Only)')
                - keywords: List[str]
                - search_mode: str ('text', 'regex', 'xpath')
                - case_sensitive: bool
                - file_pattern: str
                - max_threads: int
                - start_date: datetime (for FTP)
                - end_date: datetime (for FTP)
                - local_directory: str (for local search)
            progress_callback: Function to call with progress updates
        """
        
        self.results = []
        self.stop_event.clear()
        
        try:
            # Determine search source
            search_source = search_params.get('search_source', '🌐 FTP Server (Content)')
            
            if 'Local Directory' in search_source:
                return self._search_local_directory(search_params, progress_callback)
            elif 'Filename Only' in search_source:
                return self._search_ftp_filenames(search_params, progress_callback)
            else:
                return self._search_ftp_content(search_params, progress_callback)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise e
    
    def _search_ftp_content(self, search_params: Dict[str, Any], 
                           progress_callback: Optional[Callable] = None) -> List[SearchResult]:
        """Original FTP content search functionality"""
        try:
            # Extract parameters
            start_date = search_params['start_date']
            end_date = search_params['end_date']
            keywords = search_params['keywords']
            search_mode = search_params.get('search_mode', 'text')
            case_sensitive = search_params.get('case_sensitive', False)
            file_pattern = search_params.get('file_pattern', '')
            max_threads = search_params.get('max_threads', MAX_WORKER_THREADS)
            find_all_matches = search_params.get('find_all_matches', False)
            
            # Extract directory settings
            source_directory = search_params.get('source_directory', 'SAMSUNG')
            send_file_directory = search_params.get('send_file_directory', 'Send File')
            
            # Validate parameters
            if not keywords:
                raise ValueError("No keywords provided")
            
            # Get date directories
            logger.info(f"Searching from {start_date} to {end_date}")
            use_optimized = search_params.get('use_optimized_search', True)
            date_directories = self.ftp_manager.list_date_directories(
                start_date, end_date, source_directory, use_optimized
            )
            
            if not date_directories:
                logger.warning("No directories found in date range")
                return []

            # Initialize progress with directory count first
            self.progress.set_totals(len(date_directories), 0)  # Files count will be updated as we go
            
            # Log search info
            logger.info(f"Found {len(date_directories)} directories for streaming search")
            logger.info(f"Directories: {date_directories}")
            
            # Create search engine
            search_engine = self._create_search_engine(keywords, search_mode, case_sensitive)
            
            # Process directories in streaming batches
            logger.info(f"Starting streaming search with {max_threads} threads...")
            return self._execute_streaming_search(
                date_directories, file_pattern, source_directory, 
                send_file_directory, find_all_matches, search_engine, 
                max_threads, progress_callback
            )
            
        except Exception as e:
            logger.error(f"FTP content search failed: {e}")
            return []
    
    def _execute_streaming_search(self, date_directories, file_pattern, source_directory, 
                                send_file_directory, find_all_matches, search_engine, 
                                max_threads, progress_callback):
        """Execute search using streaming approach to handle large datasets"""
        try:
            BATCH_SIZE = 20  # Reduced from 50 to 20 for better memory management
            processed_directories = 0
            total_files_processed = 0
            
            # Reduce thread count for very large datasets
            effective_threads = min(max_threads, 4) if len(date_directories) > 100 else max_threads
            logger.info(f"Using {effective_threads} threads for large dataset processing")
            
            with ThreadPoolExecutor(max_workers=effective_threads) as executor:
                for date_dir in date_directories:
                    if self.stop_event.is_set():
                        break
                        
                    try:
                        # Get files for this directory
                        files = self.ftp_manager.list_xml_files(
                            date_dir, file_pattern, source_directory, send_file_directory
                        )
                        
                        if not files:
                            processed_directories += 1
                            continue
                        
                        # Update total files count for progress
                        self.progress.total_files += len(files)
                        
                        # Process files in batches
                        for i in range(0, len(files), BATCH_SIZE):
                            if self.stop_event.is_set():
                                break
                                
                            batch = files[i:i + BATCH_SIZE]
                            batch_tasks = []
                            
                            # Create tasks for this batch
                            for filename, file_size in batch:
                                # Skip very large files
                                if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                                    logger.warning(f"Skipping large file: {filename} ({file_size} bytes)")
                                    continue
                                
                                task = (date_dir, filename, file_size, source_directory, send_file_directory, find_all_matches)
                                batch_tasks.append(task)
                            
                            if not batch_tasks:
                                continue
                            
                            # Submit batch for processing
                            future_to_task = {
                                executor.submit(self._search_file, task, search_engine): task 
                                for task in batch_tasks
                            }
                            
                            # Wait for batch completion
                            for future in as_completed(future_to_task):
                                if self.stop_event.is_set():
                                    break
                                    
                                try:
                                    result = future.result()
                                    if result:
                                        with self.results_lock:
                                            self.results.append(result)
                                        self.progress.add_match()
                                    
                                    # Update progress
                                    self.progress.update_file(future_to_task[future][1])  # filename
                                    total_files_processed += 1
                                    
                                    # Call progress callback
                                    if progress_callback:
                                        progress_callback(self.progress.get_status())
                                        
                                except Exception as e:
                                    logger.error(f"Error processing file: {e}")
                                    continue
                            
                            # Memory cleanup after each batch
                            gc.collect()
                            
                            # Log batch completion
                            logger.info(f"Completed batch {i//BATCH_SIZE + 1} of directory {date_dir} ({len(batch_tasks)} files)")
                        
                        processed_directories += 1
                        
                        # Log directory completion
                        logger.info(f"Completed directory {date_dir} ({processed_directories}/{len(date_directories)})")
                        
                    except Exception as e:
                        logger.error(f"Error processing directory {date_dir}: {e}")
                        processed_directories += 1
                        continue
            
            logger.info(f"Streaming search completed. Processed {total_files_processed} files from {processed_directories} directories")
            return self.results.copy()
            
        except Exception as e:
            logger.error(f"Streaming search failed: {e}")
            return []
    
    def _search_local_directory(self, search_params: Dict[str, Any], 
                               progress_callback: Optional[Callable] = None) -> List[SearchResult]:
        """Local directory search functionality (simplified like SearchXML.py)"""
        try:
            # Extract parameters
            local_directory = search_params['local_directory']
            keywords = search_params['keywords']
            search_mode = search_params.get('search_mode', 'text')
            case_sensitive = search_params.get('case_sensitive', False)
            file_pattern = search_params.get('file_pattern', '')
            max_threads = search_params.get('max_threads', MAX_WORKER_THREADS)
            find_all_matches = search_params.get('find_all_matches', False)
            
            # Validate parameters
            if not keywords:
                raise ValueError("No keywords provided")
            
            # Set base directory
            if not self.local_file_manager.set_base_directory(local_directory):
                raise ValueError(f"Cannot access directory: {local_directory}")
            
            # Discover XML files
            logger.info(f"Discovering XML files in: {local_directory}")
            xml_files = self.local_file_manager.discover_xml_files(file_pattern)
            
            if not xml_files:
                logger.warning("No XML files found in directory")
                return []
            
            # Filter out very large files
            filtered_files = []
            for rel_path, size in xml_files:
                if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    logger.warning(f"Skipping large file: {rel_path} ({size} bytes)")
                    continue
                filtered_files.append((rel_path, size))
            
            # Initialize progress (use 1 directory for local search)
            self.progress.set_totals(1, len(filtered_files))
            self.progress.update_directory("Local Directory")
            
            # Log search info
            logger.info(f"Found {len(filtered_files)} XML files to search in local directory")
            
            if len(filtered_files) == 0:
                logger.warning("No accessible XML files found to search")
                return []
            
            # Use simple search approach like SearchXML.py
            logger.info(f"Starting local search with {max_threads} threads...")
            
            found_matches = {}
            
            # Simple file processing function (enhanced like SearchXML.py)
            def process_local_file(file_info):
                """Process a single local file (enhanced to find all keywords like SearchXML.py)"""
                rel_path, size = file_info
                filename = os.path.basename(rel_path)
                
                if self.stop_event.is_set():
                    return None
                    
                try:
                    # Read file content directly
                    content = self.local_file_manager.get_file_stream(rel_path)
                    if content is None:
                        logger.warning(f"Could not read local file: {filename}")
                        return None
                    
                    # Track results for this file (like SearchXML.py)
                    file_results = []
                    
                    # Search for each keyword (like SearchXML.py)
                    for keyword in keywords:
                        search_keyword = keyword if case_sensitive else keyword.lower()
                        search_content = content if case_sensitive else content.lower()
                        
                        count = search_content.count(search_keyword)
                        if count > 0:
                            # Create search result for this keyword
                            result = SearchResult(
                                date_dir=os.path.dirname(rel_path) or ".",
                                filename=filename,
                                match_type="Text Match",
                                match_content=f"Found '{keyword}' {count} times",
                                line_number=1
                            )
                            
                            file_results.append(result)
                            logger.info(f"✓ Match found in {filename}: '{keyword}' ({count} times)")
                    
                    # Add all results for this file to global results
                    if file_results:
                        with self.results_lock:
                            self.results.extend(file_results)
                        logger.info(f"✓ Total {len(file_results)} keyword matches found in {filename}")
                        return file_results  # Return list of results
                    else:
                        logger.debug(f"✗ No keywords match in {filename}")
                        return None
                    
                except Exception as e:
                    error_msg = f"Error processing local file {filename}: {e}"
                    logger.error(error_msg)
                    return None
            
            # Execute search with thread pool (like SearchXML.py)
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Submit all tasks
                futures = []
                for file_info in filtered_files:
                    future = executor.submit(process_local_file, file_info)
                    futures.append((future, file_info))
                
                # Process completed tasks (updated to handle multiple results per file)
                for future, file_info in futures:
                    if self.stop_event.is_set():
                        logger.info("Local search stopped by user")
                        break
                        
                    rel_path, size = file_info
                    filename = os.path.basename(rel_path)
                    
                    try:
                        result = future.result()
                        if result:
                            # result can be a list of SearchResult or None
                            if isinstance(result, list):
                                # Multiple keyword matches in this file
                                for _ in result:
                                    self.progress.add_match()
                                logger.debug(f"Added {len(result)} matches for {filename}")
                            else:
                                # Single result (backward compatibility)
                                self.progress.add_match()
                        
                        self.progress.update_file(filename)
                        
                        # Call progress callback
                        if progress_callback:
                            progress_callback(self.progress.get_status())
                            
                    except Exception as e:
                        error_msg = f"Error processing {filename}: {e}"
                        logger.error(error_msg)
                        self.progress.add_error(error_msg)
            
            logger.info(f"Local search completed. Found {len(self.results)} matches.")
            return self.results
            
        except Exception as e:
            logger.error(f"Local directory search failed: {e}")
            raise
    
    def _search_ftp_filenames(self, search_params: Dict[str, Any], 
                             progress_callback: Optional[Callable] = None) -> List[SearchResult]:
        """FTP filename-only search functionality"""
        try:
            # Extract parameters
            start_date = search_params['start_date']
            end_date = search_params['end_date']
            source_directory = search_params.get('source_directory', '')
            send_file_directory = search_params.get('send_file_directory', '')
            keywords = search_params['keywords']  # These are filename patterns
            file_pattern = search_params.get('file_pattern', '*.xml')
            case_sensitive = search_params.get('case_sensitive', False)
            
            # Validate parameters
            if not keywords:
                raise ValueError("No filename patterns provided")
            
            logger.info(f"Starting FTP filename search from {start_date} to {end_date}")
            logger.info(f"Filename patterns to search: {keywords}")
            
            # Get date directories
            date_directories = self.ftp_manager.list_date_directories(start_date, end_date, source_directory, search_params.get('use_optimized_search', True))
            
            if not date_directories:
                logger.warning("No directories found in date range")
                return []
            
            # Initialize progress
            total_dirs = len(date_directories)
            self.progress.set_totals(total_dirs, 0)  # We'll update file count as we discover
            
            logger.info(f"Searching filenames in {total_dirs} directories")
            
            total_matches = 0
            
            # Search through each date directory
            for i, date_dir in enumerate(date_directories):
                if self.stop_event.is_set():
                    logger.info("FTP filename search stopped by user")
                    break
                
                self.progress.update_directory(date_dir)
                logger.info(f"Scanning directory {i+1}/{total_dirs}: {date_dir}")
                
                try:
                    # Get all XML files in this directory
                    files = self.ftp_manager.list_xml_files(
                        date_dir, file_pattern, source_directory, send_file_directory
                    )
                    
                    if not files:
                        logger.debug(f"No XML files found in {date_dir}")
                        continue
                    
                    logger.info(f"Found {len(files)} XML files in {date_dir}")
                    
                    # Search filenames against patterns
                    for filename, file_size in files:
                        if self.stop_event.is_set():
                            break
                        
                        # Check each filename pattern
                        for pattern in keywords:
                            pattern = pattern.strip()
                            if not pattern:
                                continue
                            
                            # Perform filename matching
                            if self._filename_matches_pattern(filename, pattern, case_sensitive):
                                # Create result for filename match
                                result = SearchResult(
                                    date_dir=date_dir,
                                    filename=filename,
                                    match_type="Filename Match",
                                    match_content=f"Filename matches pattern: '{pattern}'",
                                    line_number=0  # Not applicable for filename search
                                )
                                
                                with self.results_lock:
                                    self.results.append(result)
                                
                                total_matches += 1
                                self.progress.add_match()
                                
                                logger.info(f"✓ Filename match: {filename} matches '{pattern}'")
                                break  # Don't duplicate matches for same file
                        
                        self.progress.update_file(filename)
                    
                    # Call progress callback
                    if progress_callback:
                        progress_callback(self.progress.get_status())
                        
                except Exception as e:
                    error_msg = f"Error scanning directory {date_dir}: {e}"
                    logger.error(error_msg)
                    self.progress.add_error(error_msg)
                    continue
            
            logger.info(f"FTP filename search completed. Found {total_matches} filename matches.")
            return self.results
            
        except Exception as e:
            logger.error(f"FTP filename search failed: {e}")
            raise
    
    def _filename_matches_pattern(self, filename: str, pattern: str, case_sensitive: bool = False) -> bool:
        """Check if filename matches the given pattern"""
        try:
            # Prepare strings for comparison
            search_filename = filename if case_sensitive else filename.lower()
            search_pattern = pattern if case_sensitive else pattern.lower()
            
            # Simple pattern matching strategies:
            
            # 1. Exact substring match (most common)
            if search_pattern in search_filename:
                return True
            
            # 2. Wildcard pattern matching
            if '*' in pattern or '?' in pattern:
                import fnmatch
                return fnmatch.fnmatch(search_filename, search_pattern)
            
            # 3. Multiple pattern matching (comma-separated)
            if ',' in pattern:
                patterns = [p.strip() for p in pattern.split(',')]
                for p in patterns:
                    if self._filename_matches_pattern(filename, p, case_sensitive):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error matching filename '{filename}' against pattern '{pattern}': {e}")
            return False
    
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
        """Search a single file with proper connection management (thread-safe) and retry logic"""
        date_dir, filename, file_size, source_directory, send_file_directory, find_all_matches = task
        
        if self.stop_event.is_set():
            logger.debug(f"⏹ Stopping search for {filename} (stop requested)")
            return None
        
        max_retries = 3
        retry_delay = [1, 2, 3]  # Exponential backoff delays
        
        for attempt in range(max_retries):
            conn = None
            try:
                logger.debug(f"� [T{threading.current_thread().ident % 10000}] Attempt {attempt + 1}/{max_retries} - Searching {filename} (size: {file_size} bytes)...")
                
                # Get file stream from connection pool
                conn, stream_func = self.ftp_manager.get_file_stream(
                    date_dir, filename, source_directory, send_file_directory
                )
                if not conn or not stream_func:
                    logger.warning(f"❌ Attempt {attempt + 1} - Could not get stream for {filename}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay[attempt])
                        # Force FTP manager to refresh connections
                        try:
                            self.ftp_manager.reconnect()
                        except:
                            pass
                        continue
                    return None

                logger.debug(f"🔍 [T{threading.current_thread().ident % 10000}] Starting search in {filename}...")
                
                # Search in stream with early termination control and smaller chunk size for large files
                early_termination = not find_all_matches
                chunk_size = 64 * 1024 if file_size > 100 * 1024 else 256 * 1024
                
                result = search_engine.search_in_stream(
                    stream_func, date_dir, filename, chunk_size, early_termination
                )
                
                logger.debug(f"✅ [T{threading.current_thread().ident % 10000}] Search completed for {filename}, result: {'Found' if result else 'Not found'}")
                
                # Success - release connection and return result
                if conn:
                    try:
                        self.ftp_manager.release_file_stream(conn)
                        logger.debug(f"🔌 [T{threading.current_thread().ident % 10000}] Released connection for {filename}")
                    except Exception as e:
                        logger.error(f"💥 Error releasing connection for {filename}: {e}")
                
                return result
                    
            except (ConnectionError, OSError, TimeoutError, ConnectionResetError) as conn_error:
                # Network/connection specific errors - retry
                logger.warning(f"🔄 [T{threading.current_thread().ident % 10000}] Connection error on attempt {attempt + 1} for {filename}: {conn_error}")
                
                # Release problematic connection
                if conn:
                    try:
                        self.ftp_manager.release_file_stream(conn)
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    import time
                    logger.info(f"⏳ Retrying {filename} in {retry_delay[attempt]} seconds...")
                    time.sleep(retry_delay[attempt])
                    # Force reconnection for next attempt
                    try:
                        self.ftp_manager.reconnect()
                    except:
                        pass
                else:
                    logger.error(f"💥 All {max_retries} attempts failed for {filename} - skipping file")
                    return None
                    
            except Exception as e:
                # Other errors - don't retry, but log appropriately
                if "10060" in str(e) or "timeout" in str(e).lower() or "connection" in str(e).lower():
                    # This is likely a connection issue, retry
                    logger.warning(f"🔄 [T{threading.current_thread().ident % 10000}] Connection-related error on attempt {attempt + 1} for {filename}: {e}")
                    
                    if conn:
                        try:
                            self.ftp_manager.release_file_stream(conn)
                        except:
                            pass
                    
                    if attempt < max_retries - 1:
                        import time
                        logger.info(f"⏳ Retrying {filename} in {retry_delay[attempt]} seconds...")
                        time.sleep(retry_delay[attempt])
                        try:
                            self.ftp_manager.reconnect()
                        except:
                            pass
                    else:
                        logger.error(f"💥 All {max_retries} attempts failed for {filename} - skipping file")
                        return None
                else:
                    # Non-recoverable error
                    logger.error(f"� [T{threading.current_thread().ident % 10000}] Non-recoverable error searching file {filename}: {e}")
                    if conn:
                        try:
                            self.ftp_manager.release_file_stream(conn)
                        except:
                            pass
                    return None
        
        # If we get here, all retries failed
        logger.error(f"💥 All retry attempts exhausted for {filename}")
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
