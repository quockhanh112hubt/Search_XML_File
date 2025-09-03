"""
Settings Manager for saving and loading user preferences
"""

import json
import os
from typing import Dict, Any

class SettingsManager:
    """Manage application settings persistence"""
    
    def __init__(self, settings_file: str = "user_settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "ftp": {
                "host": "",
                "port": 21,
                "username": "",
                "password": "",  # Note: In production, encrypt this
                "remember_password": False
            },
            "directories": {
                "source_directory": "SAMSUNG",
                "send_file_directory": "Send File", 
                "receive_file_directory": "Receive File"
            },
            "search": {
                "default_file_pattern": "TCO_*_KMC_*.xml",
                "case_sensitive": False,
                "max_threads": 8
            },
            "ui": {
                "last_date_range": "Last 7 Days",
                "last_search_mode": "Text Contains"
            }
        }
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                
                # Merge with defaults to handle new settings
                settings = self.default_settings.copy()
                self._deep_update(settings, saved_settings)
                return settings
            else:
                return self.default_settings.copy()
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def _deep_update(self, base_dict: dict, update_dict: dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
