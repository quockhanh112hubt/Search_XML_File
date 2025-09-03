#!/usr/bin/env python3
"""
Simple debug script to test FTP file reading without search
"""

import logging
from src.core.ftp_manager import FTPManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_ftp_download():
    """Test simple FTP file download"""
    
    ftp_manager = FTPManager()
    
    try:
        # Connect
        success = ftp_manager.connect("192.168.110.12", 21, "ktradmin", "123456")
        if not success:
            logger.error("Failed to connect to FTP")
            return
        
        logger.info("FTP connected successfully")
        
        # List directories
        directories = ftp_manager.list_date_directories(
            start_date="20240801", 
            end_date="20240802", 
            source_directory="SAMSUNG", 
            send_file_directory="Send File"
        )
        
        logger.info(f"Found directories: {directories}")
        
        if not directories:
            logger.warning("No directories found")
            return
            
        # List files in first directory
        first_dir = directories[0]
        files = ftp_manager.list_xml_files(
            first_dir, 
            "*.xml", 
            "SAMSUNG", 
            "Send File"
        )
        
        logger.info(f"Found {len(files)} files in {first_dir}")
        for filename, size in files[:3]:  # Only first 3 files
            logger.info(f"  {filename}: {size} bytes")
            
        if files:
            # Test downloading first file
            filename, size = files[0]
            logger.info(f"Testing download of {filename} ({size} bytes)...")
            
            conn, stream_func = ftp_manager.get_file_stream(
                first_dir, filename, "SAMSUNG", "Send File"
            )
            
            if conn and stream_func:
                logger.info("Stream function obtained successfully")
                
                # Test reading chunks
                total_bytes = 0
                def chunk_callback(data):
                    nonlocal total_bytes
                    total_bytes += len(data)
                    if total_bytes % 10240 == 0:  # Log every 10KB
                        logger.info(f"Downloaded {total_bytes} bytes...")
                
                logger.info("Starting file download...")
                stream_func(chunk_callback)
                logger.info(f"Download completed. Total: {total_bytes} bytes")
                
                # Release connection
                ftp_manager.release_file_stream(conn)
                logger.info("Connection released")
            else:
                logger.error("Failed to get stream function")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        ftp_manager.disconnect()
        logger.info("FTP disconnected")

if __name__ == "__main__":
    test_ftp_download()
