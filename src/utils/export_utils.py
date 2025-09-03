"""
Export utilities for search results
"""

import csv
import pandas as pd
from typing import List
from datetime import datetime

from ..core.search_engine import SearchResult

class ResultExporter:
    """Export search results to various formats"""
    
    @staticmethod
    def export_to_csv(results: List[SearchResult], filename: str):
        """Export results to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Date', 'Filename', 'File Path', 'Match Type', 
                           'Match Content', 'Line Number'])
            
            # Write data
            for result in results:
                writer.writerow([
                    result.date_dir,
                    result.filename,
                    result.file_path,
                    result.match_type,
                    result.match_content,
                    result.line_number
                ])
    
    @staticmethod
    def export_to_excel(results: List[SearchResult], filename: str):
        """Export results to Excel file"""
        data = []
        for result in results:
            data.append({
                'Date': result.date_dir,
                'Filename': result.filename,
                'File Path': result.file_path,
                'Match Type': result.match_type,
                'Match Content': result.match_content,
                'Line Number': result.line_number
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Search Results', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Search Results']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
