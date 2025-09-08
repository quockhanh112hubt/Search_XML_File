"""
Debug script to inspect FTP directory structure
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.ftp_manager import FTPManager
from src.utils.logging_config import setup_logging

def debug_ftp_structure():
    """Debug FTP directory structure"""
    setup_logging()
    
    ftp_manager = FTPManager()
    
    try:
        # Connect to FTP
        print("Connecting to FTP...")
        if not ftp_manager.connect():
            print("Failed to connect to FTP!")
            return
            
        print("Connected successfully!")
        
        # List root directory
        print("\n=== ROOT DIRECTORY ===")
        try:
            dirs = []
            ftp_manager.ftp.retrlines('LIST', dirs.append)
            for line in dirs:
                print(f"ROOT: {line}")
        except Exception as e:
            print(f"Error listing root: {e}")
        
        # Check SAMSUNG directory
        print("\n=== SAMSUNG DIRECTORY ===")
        try:
            ftp_manager.ftp.cwd('SAMSUNG')
            dirs = []
            ftp_manager.ftp.retrlines('LIST', dirs.append)
            for line in dirs:
                print(f"SAMSUNG: {line}")
        except Exception as e:
            print(f"Error accessing SAMSUNG: {e}")
            
        # Check for date directories (20250908, etc.)
        print("\n=== LOOKING FOR DATE DIRECTORIES ===")
        try:
            dirs = []
            ftp_manager.ftp.retrlines('LIST', dirs.append)
            
            date_dirs = []
            for line in dirs:
                parts = line.split()
                if len(parts) >= 9 and parts[0].startswith('d'):
                    dirname = parts[-1]
                    print(f"Found directory: {dirname}")
                    if len(dirname) == 8 and dirname.isdigit():
                        date_dirs.append(dirname)
                        
            print(f"Date directories found: {date_dirs}")
            
            # Check inside first date directory if exists
            if date_dirs:
                test_dir = date_dirs[0]
                print(f"\n=== INSIDE {test_dir} ===")
                try:
                    ftp_manager.ftp.cwd(test_dir)
                    dirs = []
                    ftp_manager.ftp.retrlines('LIST', dirs.append)
                    for line in dirs[:10]:  # Show first 10 items
                        print(f"{test_dir}: {line}")
                except Exception as e:
                    print(f"Error accessing {test_dir}: {e}")
                    
        except Exception as e:
            print(f"Error checking date directories: {e}")
            
    except Exception as e:
        print(f"Debug error: {e}")
    finally:
        ftp_manager.disconnect()

if __name__ == "__main__":
    debug_ftp_structure()
