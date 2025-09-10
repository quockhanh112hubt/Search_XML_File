# Logging configuration

import logging
import os
from config.settings import LOG_LEVEL, LOG_FILE, MAX_LOG_SIZE_MB

def setup_logging():
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if not log_dir:  # If LOG_FILE has no directory part
        log_dir = 'logs'
        log_file_path = os.path.join(log_dir, os.path.basename(LOG_FILE))
    else:
        log_file_path = LOG_FILE
    
    # Ensure logs directory exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"Created logs directory: {log_dir}")
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Set up log rotation
    from logging.handlers import RotatingFileHandler
    
    # Remove default file handler and add rotating handler
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)
    
    rotating_handler = RotatingFileHandler(
        log_file_path,  # Use the corrected path
        maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    rotating_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(rotating_handler)
