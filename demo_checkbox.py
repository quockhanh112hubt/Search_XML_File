#!/usr/bin/env python3
"""
Demo để test checkbox styling mới
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QCheckBox, QLabel
from PyQt5.QtCore import Qt

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.styles import COMPLETE_STYLESHEET, COLORS

class CheckboxDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Checkbox Style Demo")
        self.setMinimumSize(400, 300)
        
        # Apply stylesheet
        self.setStyleSheet(COMPLETE_STYLESHEET)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Checkbox Style Demo")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['primary']}; margin: 20px;")
        layout.addWidget(title)
        
        # Create test checkboxes
        self.checkbox1 = QCheckBox("Case Sensitive")
        self.checkbox2 = QCheckBox("Find all matches per file")
        self.checkbox3 = QCheckBox("Remember Password")
        self.checkbox4 = QCheckBox("Use Optimized Directory Search")
        
        # Apply custom styling
        self.setup_custom_checkbox(self.checkbox1)
        self.setup_custom_checkbox(self.checkbox2)
        self.setup_custom_checkbox(self.checkbox3)
        self.setup_custom_checkbox(self.checkbox4)
        
        # Add to layout
        layout.addWidget(self.checkbox1)
        layout.addWidget(self.checkbox2)
        layout.addWidget(self.checkbox3)
        layout.addWidget(self.checkbox4)
        
        # Test some checked states
        self.checkbox2.setChecked(True)
        self.checkbox4.setChecked(True)
        
        layout.addStretch()
        
        # Info label
        info = QLabel("Hover over checkboxes to see hover effects.\nClick to toggle checked/unchecked states.")
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-style: italic; margin: 20px;")
        layout.addWidget(info)
    
    def setup_custom_checkbox(self, checkbox):
        """Setup custom checkbox with modern styling and beautiful checkmark display"""
        
        def update_checkbox_style():
            # Get clean text without any checkmark symbols
            current_text = checkbox.text()
            clean_text = current_text.replace('✓ ', '').replace('☑ ', '').replace('✔ ', '').replace('✅ ', '')
            
            if checkbox.isChecked():
                # Add checkmark to text with modern styling
                checkbox.setText(f"✓ {clean_text}")
                
                # Apply checked state styling with beautiful effects
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        font-size: 14px;
                        font-weight: 600;
                        color: {COLORS['primary']};
                        spacing: 12px;
                        padding: 6px 0px;
                        background-color: transparent;
                    }}
                    
                    QCheckBox::indicator {{
                        width: 22px;
                        height: 22px;
                        border: 2px solid {COLORS['primary']};
                        border-radius: 5px;
                        background-color: {COLORS['primary']};
                        margin: 1px;
                    }}
                    
                    QCheckBox::indicator:checked {{
                        background-color: {COLORS['primary']};
                        border: 2px solid {COLORS['primary']};
                        color: white;
                        font-weight: bold;
                        font-size: 16px;
                        font-family: "Segoe UI Symbol", "Arial Unicode MS";
                    }}
                    
                    QCheckBox::indicator:checked:hover {{
                        background-color: {COLORS['primary_hover']};
                        border-color: {COLORS['primary_hover']};
                    }}
                    
                    QCheckBox::indicator:checked:pressed {{
                        background-color: #1e40af;
                    }}
                """)
            else:
                # Remove checkmark from text
                checkbox.setText(clean_text)
                
                # Apply unchecked state styling with smooth hover effects
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        font-size: 14px;
                        font-weight: 500;
                        color: {COLORS['text_primary']};
                        spacing: 12px;
                        padding: 6px 0px;
                        background-color: transparent;
                    }}
                    
                    QCheckBox::indicator {{
                        width: 22px;
                        height: 22px;
                        border: 2px solid {COLORS['border']};
                        border-radius: 5px;
                        background-color: {COLORS['bg_primary']};
                        margin: 1px;
                    }}
                    
                    QCheckBox::indicator:unchecked:hover {{
                        border-color: {COLORS['primary']};
                        background-color: {COLORS['primary_light']};
                    }}
                    
                    QCheckBox::indicator:unchecked:pressed {{
                        background-color: {COLORS['bg_secondary']};
                    }}
                    
                    QCheckBox:hover {{
                        color: {COLORS['text_white']};
                    }}
                """)
        
        # Connect state change signal
        checkbox.stateChanged.connect(lambda: update_checkbox_style())
        
        # Apply initial styling
        update_checkbox_style()
        
        # Add mouse tracking for better hover effects
        checkbox.setMouseTracking(True)
        
        # Add tooltip for better UX if not already set
        if not checkbox.toolTip():
            checkbox.setToolTip("Click to toggle this option")
            
        # Override the paintEvent to draw custom checkmark
        original_paint_event = checkbox.paintEvent
        
        def custom_paint_event(event):
            # Call original paint event
            original_paint_event(event)
            
            # If checked, draw custom checkmark
            if checkbox.isChecked():
                from PyQt5.QtGui import QPainter, QPen, QFont
                from PyQt5.QtCore import Qt
                
                painter = QPainter(checkbox)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Get indicator rectangle
                style = checkbox.style()
                from PyQt5.QtWidgets import QStyleOptionButton
                option = QStyleOptionButton()
                option.initFrom(checkbox)
                
                indicator_rect = style.subElementRect(
                    style.SE_CheckBoxIndicator, option, checkbox
                )
                
                # Set font for checkmark
                font = QFont("Segoe UI Symbol", 12)
                font.setBold(True)
                painter.setFont(font)
                
                # Set pen color
                pen = QPen(Qt.white)
                painter.setPen(pen)
                
                # Draw checkmark symbol
                painter.drawText(indicator_rect, Qt.AlignCenter, "✓")
                
                painter.end()
        
        # Replace the paint event
        checkbox.paintEvent = custom_paint_event

def main():
    app = QApplication(sys.argv)
    
    # Set application icon if available
    try:
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(__file__), "Resource", "icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except:
        pass
    
    window = CheckboxDemo()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
