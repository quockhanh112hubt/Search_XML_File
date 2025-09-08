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
            conn.ftp.cwd(f"/{source_dir}")
            
            # Get all directories
            dirs = []
            conn.ftp.retrlines('LIST', dirs.append)
            
            # Filter date directories
            date_dirs = []
            for line in dirs:
                parts = line.split()
                if len(parts) >= 9 and parts[0].startswith('d'):
                    dirname = parts[-1]
                    if len(dirname) == 8 and dirname.isdigit():
                        try:
                            dir_date = datetime.strptime(dirname, "%Y%m%d")
                            if start_dt <= dir_date <= end_dt:
                                date_dirs.append(dirname)
                        except ValueError:
                            continue
                            
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
            # Navigate to Send File directory
            path = f"/{source_dir}/{date_dir}/{send_file_dir}"
            conn.ftp.cwd(path)
            
            # Get file list with sizes
            files = []
            file_list = []
            conn.ftp.retrlines('LIST', file_list.append)
            
            for line in file_list:
                parts = line.split()
                if len(parts) >= 9 and not parts[0].startswith('d'):
                    filename = parts[-1]
                    if filename.lower().endswith('.xml'):
                        # Apply file pattern filter if provided
                        if file_pattern:
                            import fnmatch
                            if not fnmatch.fnmatch(filename, file_pattern):
                                continue
                        
                        try:
                            size = int(parts[4])
                            files.append((filename, size))
                        except (ValueError, IndexError):
                            files.append((filename, 0))
            
            return files
            
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
