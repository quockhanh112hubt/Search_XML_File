"""
Build script to create executable file using PyInstaller
"""

import os
import subprocess
import sys
from pathlib import Path

# Paths
script_dir = Path(__file__).parent
main_script = script_dir / "Search_XML_File.py"
icon_path = script_dir / "Resource" / "icon.ico"
dist_dir = script_dir / "dist"
build_dir = script_dir / "build"

# PyInstaller command
cmd = [
    "pyinstaller",
    "--onefile",                    # Single exe file
    "--windowed",                   # No console window
    "--noconsole",                  # Hide console
    f"--icon={icon_path}",          # Application icon
    "--name=XML_Search_Tool",       # Exe name
    f"--distpath={dist_dir}",       # Output directory
    f"--workpath={build_dir}",      # Build directory
    "--clean",                      # Clean before build
    "--add-data=src;src",           # Include src folder
    "--add-data=config;config",     # Include config folder
    "--add-data=Resource;Resource", # Include Resource folder with icon
    "--hidden-import=PyQt5.QtCore",
    "--hidden-import=PyQt5.QtGui", 
    "--hidden-import=PyQt5.QtWidgets",
    "--hidden-import=xml.etree.ElementTree",
    "--hidden-import=ftplib",
    "--hidden-import=concurrent.futures",
    str(main_script)
]

if __name__ == "__main__":
    print("Building XML Search Tool executable...")
    print(f"Main script: {main_script}")
    print(f"Icon: {icon_path}")
    print(f"Output directory: {dist_dir}")
    print()
    
    # Check if files exist
    if not main_script.exists():
        print(f"Error: {main_script} not found!")
        sys.exit(1)
        
    if not icon_path.exists():
        print(f"Error: {icon_path} not found!")
        sys.exit(1)
    
    # Run PyInstaller
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created: {dist_dir / 'XML_Search_Tool.exe'}")
        
    except subprocess.CalledProcessError as e:
        print("Build failed!")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
