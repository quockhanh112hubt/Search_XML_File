# Configuration settings for XML Search Application

# FTP Connection Settings
FTP_TIMEOUT = 30  # seconds
FTP_MAX_RETRIES = 3
FTP_RETRY_DELAY = 1  # seconds

# Threading Settings
MAX_WORKER_THREADS = 8
FTP_CONNECTION_POOL_SIZE = 5

# Search Settings
DEFAULT_CHUNK_SIZE = 256 * 1024  # 256KB
CHUNK_OVERLAP_SIZE = 1024  # 1KB overlap for boundary matches
MAX_FILE_SIZE_MB = 50  # Skip files larger than this

# Default file patterns
DEFAULT_FILE_PATTERN = "TCO_*_KMC_*.xml"
XML_EXTENSIONS = ['.xml']

# Date format for FTP directories
FTP_DATE_FORMAT = "%Y%m%d"

# FTP Directory structure
SOURCE_DIRECTORY = "SAMSUNG"
SEND_FILE_DIRECTORY = "Send File"
RECEIVE_FILE_DIRECTORY = "Receive File"

# Export settings
EXPORT_FORMATS = ['CSV', 'Excel']
MAX_EXPORT_ROWS = 100000

# UI Settings
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
PROGRESS_UPDATE_INTERVAL = 100  # ms

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "xml_search.log"
MAX_LOG_SIZE_MB = 10
