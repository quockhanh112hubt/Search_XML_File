#!/usr/bin/env python3
"""
Test FTP stream with timeout
"""

import logging
import time
from datetime import date
from src.core.ftp_manager import FTPManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def test_ftp_stream_with_timeout():
    """Test FTP stream with timeout"""
    
    ftp_manager = FTPManager()
    
    try:
        # Connect
        success = ftp_manager.connect("192.168.110.12", 21, "test", "1234")
        if not success:
            logger.error("Failed to connect to FTP")
            return
        
        logger.info("FTP connected successfully")
        
        # First, list files to see what's actually available
        directories = ftp_manager.list_date_directories(
            start_date=date(2025, 9, 2), 
            end_date=date(2025, 9, 3), 
            source_directory="SAMSUNG"
        )
        
        logger.info(f"Available directories: {directories}")
        
        for date_dir in directories:
            files = ftp_manager.list_xml_files(
                date_dir, 
                "*.xml", 
                "SAMSUNG", 
                "Send File"
            )
            logger.info(f"Files in {date_dir}: {[f[0] for f in files[:5]]}")  # First 5 files
        
        # Test downloading the first available file
        if directories:
            date_dir = directories[0]
            files = ftp_manager.list_xml_files(
                date_dir, 
                "*.xml", 
                "SAMSUNG", 
                "Send File"
            )
            
            if files:
                filename, file_size = files[0]
                logger.info(f"Testing download of first available file: {filename} ({file_size} bytes)")
            else:
                logger.error("No files found in directories")
                return
        else:
            logger.error("No directories found")
            return
        
        try:
            conn, stream_func = ftp_manager.get_file_stream(
                date_dir, filename, "SAMSUNG", "Send File"
            )
            
            if conn and stream_func:
                logger.info("Stream function obtained successfully")
                
                # Test reading without timeout first
                total_bytes = 0
                chunk_count = 0
                start_time = time.time()
                
                def chunk_callback(data):
                    nonlocal total_bytes, chunk_count
                    chunk_count += 1
                    total_bytes += len(data)
                    
                    if chunk_count % 10 == 0:  # Log every 10 chunks
                        elapsed = time.time() - start_time
                        logger.info(f"Chunk {chunk_count}: {len(data)} bytes (total: {total_bytes}, elapsed: {elapsed:.1f}s)")
                
                logger.info("Starting file download...")
                stream_func(chunk_callback)
                
                elapsed = time.time() - start_time
                logger.info(f"Download completed. Total: {total_bytes} bytes in {chunk_count} chunks, time: {elapsed:.1f}s")
                
                # Release connection
                ftp_manager.release_file_stream(conn)
                logger.info("Connection released successfully")
            else:
                logger.error("Failed to get stream function")
                
        except Exception as e:
            logger.error(f"Exception during download: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        ftp_manager.disconnect()
        logger.info("FTP disconnected")

if __name__ == "__main__":
    test_ftp_stream_with_timeout()
