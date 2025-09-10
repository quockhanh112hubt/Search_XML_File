"""
FTP Connection Manager
Quản lý kết nối FTP với connection pooling và retry logic
"""

import ftplib
import socket
import time
import logging
from queue import Queue, Empty
from threading import Lock
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from config.settings import (
    FTP_TIMEOUT, FTP_MAX_RETRIES, FTP_RETRY_DELAY,
    FTP_CONNECTION_POOL_SIZE, SOURCE_DIRECTORY, SEND_FILE_DIRECTORY
)

logger = logging.getLogger(__name__)

class FTPConnection:
    """Single FTP connection wrapper"""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ftp = None
        self.last_used = time.time()
        self.is_connected = False
        
    def connect(self) -> bool:
        """Establish FTP connection"""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port, timeout=FTP_TIMEOUT)
            self.ftp.login(self.username, self.password)
            self.ftp.set_pasv(True)  # Use passive mode
            
            # Navigate to root directory to ensure we start from the correct location
            try:
                self.ftp.cwd('/')
                logger.info("Navigated to root directory")
            except Exception as e:
                logger.warning(f"Could not navigate to root directory: {e}")
                # Try to get current directory for debugging
                try:
                    current_dir = self.ftp.pwd()
                    logger.info(f"Current directory after login: {current_dir}")
                except:
                    pass
            
            self.is_connected = True
            self.last_used = time.time()
            logger.info(f"FTP connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"FTP connection failed: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Close FTP connection"""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                try:
                    self.ftp.close()
                except:
                    pass
            self.ftp = None
        self.is_connected = False
        
    def test_connection(self) -> bool:
        """Test if connection is still alive"""
        if not self.ftp:
            return False
        try:
            self.ftp.voidcmd("NOOP")
            self.last_used = time.time()
            return True
        except:
            self.is_connected = False
            return False

class FTPConnectionPool:
    """FTP Connection Pool Manager"""
    
    def __init__(self, host: str, port: int, username: str, password: str, 
                 pool_size: int = FTP_CONNECTION_POOL_SIZE):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = Lock()
        self.active_connections = 0
        
    def get_connection(self) -> Optional[FTPConnection]:
        """Get connection from pool or create new one"""
        try:
            # Try to get existing connection
            conn = self.pool.get_nowait()
            if conn.test_connection():
                return conn
            else:
                # Connection is dead, create new one
                conn.disconnect()
        except Empty:
            pass
            
        # Create new connection if pool not full
        with self.lock:
            if self.active_connections < self.pool_size:
                conn = FTPConnection(self.host, self.port, self.username, self.password)
                if conn.connect():
                    self.active_connections += 1
                    return conn
                    
        return None
    
    def return_connection(self, conn: FTPConnection):
        """Return connection to pool"""
        if conn and conn.is_connected:
            try:
                self.pool.put_nowait(conn)
            except:
                conn.disconnect()
                with self.lock:
                    self.active_connections -= 1
    
    def close_all(self):
        """Close all connections"""
        while True:
            try:
                conn = self.pool.get_nowait()
                conn.disconnect()
            except Empty:
                break
        with self.lock:
            self.active_connections = 0

class FTPManager:
    """High-level FTP operations manager"""
    
    def __init__(self):
        self.pool = None
        self.is_connected = False
        
    def connect(self, host: str, port: int, username: str, password: str) -> bool:
        """Initialize connection pool"""
        try:
            self.pool = FTPConnectionPool(host, port, username, password)
            
            # Test initial connection
            test_conn = self.pool.get_connection()
            if test_conn:
                self.pool.return_connection(test_conn)
                self.is_connected = True
                logger.info("FTP Manager connected successfully")
                return True
            else:
                logger.error("Failed to establish initial FTP connection")
                return False
                
        except Exception as e:
            logger.error(f"FTP Manager connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close all connections"""
        if self.pool:
            self.pool.close_all()
        self.is_connected = False
        
    def reconnect(self):
        """Reconnect to FTP server (refresh connection pool)"""
        if not self.pool:
            logger.warning("No pool to reconnect - connection was never established")
            return False
            
        try:
            # Store connection details
            host = self.pool.host
            port = self.pool.port
            username = self.pool.username
            password = self.pool.password
            
            logger.info("Reconnecting to FTP server...")
            
            # Close existing connections
            self.disconnect()
            
            # Re-establish connection
            return self.connect(host, port, username, password)
            
        except Exception as e:
            logger.error(f"FTP reconnection failed: {e}")
            return False
        
    def list_date_directories(self, start_date, end_date, source_directory: str = None) -> List[str]:
        """List directories within date range"""
        if not self.is_connected:
            return []
        
        # Use provided source directory or default
        source_dir = source_directory or SOURCE_DIRECTORY
        
        # Convert date objects to datetime if needed
        if hasattr(start_date, 'date'):
            # It's already a datetime object
            start_dt = start_date
        else:
            # It's a date object, convert to datetime
            start_dt = datetime.combine(start_date, datetime.min.time())
            
        if hasattr(end_date, 'date'):
            # It's already a datetime object
            end_dt = end_date
        else:
            # It's a date object, convert to datetime
            end_dt = datetime.combine(end_date, datetime.max.time())
            
        conn = self.pool.get_connection()
        if not conn:
            return []
            
        try:
            # Navigate to source directory
            logger.info(f"Navigating to source directory: /{source_dir}")
            conn.ftp.cwd(f"/{source_dir}")
            
            # Get all directories
            dirs = []
            conn.ftp.retrlines('LIST', dirs.append)
            logger.info(f"Found {len(dirs)} items in {source_dir}")
            
            # Log first few items for debugging
            for i, line in enumerate(dirs[:5]):
                logger.info(f"Item {i+1}: {line}")
            
            logger.info("Starting date directory filtering...")
            
            # Filter date directories
            date_dirs = []
            logger.info(f"Filtering directories for date range: {start_dt.date()} to {end_dt.date()}")
            logger.info(f"Start datetime: {start_dt}, End datetime: {end_dt}")
            
            for line in dirs:
                parts = line.split()
                logger.info(f"Processing line: {line}")
                
                # Flexible parsing - handle different FTP server formats
                if len(parts) >= 1:
                    logger.info(f"Line has {len(parts)} parts: {parts}")
                    
                    # Handle different FTP LIST formats
                    is_directory = False
                    dirname = None
                    
                    # Unix format: drwxrwxrwx ... dirname
                    if parts[0].startswith('d'):
                        is_directory = True
                        dirname = parts[-1]
                        logger.info(f"Unix format detected - directory: {dirname}")
                    
                    # Windows format: MM-DD-YY HH:MMAM/PM <DIR> dirname  
                    elif len(parts) >= 3 and '<DIR>' in parts:
                        is_directory = True
                        # Find <DIR> index and get next part as directory name
                        try:
                            dir_index = parts.index('<DIR>')
                            if dir_index + 1 < len(parts):
                                dirname = parts[dir_index + 1]
                                logger.info(f"Windows format detected - directory: {dirname}")
                            else:
                                logger.info("Windows format but no directory name after <DIR>")
                        except ValueError:
                            logger.info("Windows format detection failed")
                    
                    # DOS/other format: check if any part contains <DIR>
                    elif any('<DIR>' in part for part in parts):
                        is_directory = True
                        dirname = parts[-1]  # Last part as fallback
                        logger.info(f"DOS/other format detected - directory: {dirname}")
                    
                    else:
                        logger.info(f"✗ Not a directory (no 'd' prefix or <DIR> marker)")
                        continue
                        
                    if is_directory and dirname:
                        logger.info(f"Found directory candidate: {dirname}")
                        
                        # Check if it's a valid date directory (YYYYMMDD format)
                        if len(dirname) == 8 and dirname.isdigit():
                            logger.info(f"Directory {dirname} matches date format")
                            try:
                                dir_date = datetime.strptime(dirname, "%Y%m%d")
                                logger.info(f"Checking {dirname} -> {dir_date} vs range {start_dt} to {end_dt}")
                                logger.info(f"Comparison: {start_dt} <= {dir_date} <= {end_dt} = {start_dt <= dir_date <= end_dt}")
                                
                                if start_dt <= dir_date <= end_dt:
                                    date_dirs.append(dirname)
                                    logger.info(f"✓ Added date directory: {dirname}")
                                else:
                                    logger.info(f"✗ {dirname} outside range: {dir_date} not between {start_dt} and {end_dt}")
                            except ValueError as e:
                                logger.info(f"✗ Invalid date format {dirname}: {e}")
                                continue
                        else:
                            logger.info(f"✗ {dirname} - not valid date format (length: {len(dirname)}, isdigit: {dirname.isdigit()})")
                    else:
                        logger.info(f"✗ Directory detection failed")
                else:
                    logger.info(f"✗ Empty line or no parts")
                            
            logger.info(f"Found {len(date_dirs)} date directories in range: {date_dirs}")
            return sorted(date_dirs)
            
        except Exception as e:
            logger.error(f"Error listing directories: {e}")
            return []
        finally:
            self.pool.return_connection(conn)
    
    def list_xml_files(self, date_dir: str, file_pattern: str = None, 
                      source_directory: str = None, send_file_directory: str = None) -> List[Tuple[str, int]]:
        """List XML files in Send File directory for specific date"""
        if not self.is_connected:
            return []

        # Use provided directories or defaults
        source_dir = source_directory or SOURCE_DIRECTORY
        send_file_dir = send_file_directory or SEND_FILE_DIRECTORY
            
        conn = self.pool.get_connection()
        if not conn:
            return []
            
        try:
            # First, let's check what's directly in the date directory
            logger.info(f"=== Exploring directory structure for {date_dir} ===")
            
            # Try different possible paths
            paths_to_try = [
                f"/{date_dir}",  # Direct date directory
                f"/{source_dir}/{date_dir}",  # Default source + date
                f"/{source_dir}/{date_dir}/{send_file_dir}",  # Full default path
                f"/SAMSUNG/{date_dir}",  # From log we saw SAMSUNG
                f"/SAMSUNG/{date_dir}/Send File",  # SAMSUNG + date + Send File
            ]
            
            files_found = []
            successful_path = None
            
            for path in paths_to_try:
                try:
                    logger.info(f"Trying path: {path}")
                    conn.ftp.cwd(path)
                    
                    # Get file list
                    file_list = []
                    conn.ftp.retrlines('LIST', file_list.append)
                    logger.info(f"Found {len(file_list)} items in {path}")
                    
                    for i, line in enumerate(file_list):
                        logger.info(f"  Item {i+1}: {line}")
                    
                    # Parse files and directories
                    for line in file_list:
                        parts = line.split()
                        logger.info(f"Processing line: {line}")
                        logger.info(f"Line parts ({len(parts)}): {parts}")
                        
                        if len(parts) >= 1:
                            # Handle different FTP formats for files
                            is_file = False
                            filename = None
                            
                            # Unix format: -rwxrwxrwx ... filename
                            if parts[0].startswith('-'):
                                is_file = True
                                filename = parts[-1]
                                logger.info(f"Unix format file detected: {filename}")
                            
                            # Windows format: MM-DD-YY HH:MMAM/PM size filename
                            elif len(parts) >= 3 and '<DIR>' not in parts:
                                # If no <DIR> marker, assume it's a file
                                is_file = True
                                filename = parts[-1]
                                logger.info(f"Windows format file detected: {filename}")
                            
                            # Check for XML extension
                            if is_file and filename and filename.lower().endswith('.xml'):
                                # Apply file pattern filter if provided
                                if file_pattern:
                                    import fnmatch
                                    if not fnmatch.fnmatch(filename, file_pattern):
                                        logger.info(f"File {filename} doesn't match pattern {file_pattern}")
                                        continue
                                
                                try:
                                    # Try to get file size from different positions
                                    size = 0
                                    if len(parts) >= 5:
                                        # Try common size positions
                                        for size_pos in [4, 2, 3]:
                                            try:
                                                size = int(parts[size_pos])
                                                break
                                            except (ValueError, IndexError):
                                                continue
                                    
                                    files_found.append((filename, size))
                                    logger.info(f"✓ Found XML file: {filename} (size: {size})")
                                except Exception as e:
                                    files_found.append((filename, 0))
                                    logger.info(f"✓ Found XML file: {filename} (size unknown: {e})")
                            elif is_file and filename:
                                logger.info(f"✗ Not XML file: {filename}")
                            else:
                                logger.info(f"✗ Not a file or no filename detected")
                    
                    if files_found:
                        successful_path = path
                        logger.info(f"SUCCESS: Found {len(files_found)} XML files in {path}")
                        break
                    else:
                        logger.info(f"No XML files found in {path}")
                        
                except Exception as e:
                    logger.info(f"Failed to access {path}: {e}")
                    continue
            
            if successful_path:
                logger.info(f"Final result: {len(files_found)} XML files from {successful_path}")
                return files_found
            else:
                logger.info("No XML files found in any attempted path")
                return []
            
        except Exception as e:
            logger.error(f"Error listing files in {date_dir}: {e}")
            return []
        finally:
            self.pool.return_connection(conn)
    
    def get_file_stream(self, date_dir: str, filename: str, 
                       source_directory: str = None, send_file_directory: str = None):
        """Get file stream for reading"""
        if not self.is_connected:
            return None, None
        
        # Use provided directories or defaults
        source_dir = source_directory or SOURCE_DIRECTORY
        send_file_dir = send_file_directory or SEND_FILE_DIRECTORY
            
        conn = self.pool.get_connection()
        if not conn:
            return None, None
            
        try:
            # Navigate to file directory
            path = f"/{source_dir}/{date_dir}/{send_file_dir}"
            conn.ftp.cwd(path)
            
            # Test if file exists first
            try:
                file_size = conn.ftp.size(filename)
                logger.debug(f"File {filename} exists, size: {file_size}")
            except Exception as e:
                logger.error(f"File {filename} does not exist or cannot be accessed: {e}")
                self.pool.return_connection(conn)
                return None, None
            
            # Return connection and callback for streaming
            return conn, lambda callback: conn.ftp.retrbinary(f'RETR {filename}', callback)
            
        except Exception as e:
            logger.error(f"Error opening file stream {filename}: {e}")
            self.pool.return_connection(conn)
            return None, None
    
    def release_file_stream(self, conn: FTPConnection):
        """Release file stream connection"""
        if conn:
            self.pool.return_connection(conn)
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if hasattr(self, 'pool') and self.pool:
            try:
                self.pool.close_all()
                logger.info("All FTP pool connections closed")
            except Exception as e:
                logger.error(f"Error closing FTP pool: {e}")
                
        # Also close main connection
        if hasattr(self, 'ftp') and self.ftp:
            try:
                self.ftp.quit()
                logger.info("Main FTP connection closed")
            except Exception as e:
                logger.error(f"Error closing main FTP connection: {e}")
        
        self.is_connected = False
    
    def download_file(self, ftp_file_path: str, local_file_path: str) -> bool:
        """Download a file from FTP server to local path"""
        try:
            conn = self.pool.get_connection()
            if not conn:
                logger.error("Failed to get FTP connection from pool")
                return False
            
            try:
                with open(local_file_path, 'wb') as local_file:
                    conn.ftp.retrbinary(f'RETR {ftp_file_path}', local_file.write)
                logger.info(f"Successfully downloaded: {ftp_file_path}")
                return True
            finally:
                self.pool.return_connection(conn)
                
        except Exception as e:
            logger.error(f"Download failed for {ftp_file_path}: {e}")
            return False
