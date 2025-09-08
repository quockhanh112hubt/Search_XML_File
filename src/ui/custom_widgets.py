"""
Custom UI Widgets for XML Search Application
"""

from PyQt5.QtWidgets import QCheckBox, QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from .styles import COLORS


class CustomCheckBox(QWidget):
    """Custom checkbox with proper checkmark display"""
    
    stateChanged = pyqtSignal(int)
    
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.checked = False
        self.text = text
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Checkbox indicator
        self.indicator = QLabel()
        self.indicator.setFixedSize(22, 22)
        self.indicator.setAlignment(Qt.AlignCenter)
        self.update_indicator()
        
        # Text label
        self.label = QLabel(self.text)
        self.label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: 500;
        """)
        
        layout.addWidget(self.indicator)
        layout.addWidget(self.label)
        layout.addStretch()
        
        # Make clickable
        self.indicator.mousePressEvent = self.toggle_state
        self.label.mousePressEvent = self.toggle_state
        
    def update_indicator(self):
        if self.checked:
            self.indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['primary']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: 6px;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                }}
            """)
            self.indicator.setText("✓")
        else:
            self.indicator.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['bg_primary']};
                    border: 2px solid {COLORS['border']};
                    border-radius: 6px;
                }}
            """)
            self.indicator.setText("")
            
    def toggle_state(self, event):
        self.checked = not self.checked
        self.update_indicator()
        self.stateChanged.emit(2 if self.checked else 0)
        
    def isChecked(self):
        return self.checked
        
    def setChecked(self, checked):
        self.checked = checked
        self.update_indicator()
        
    def setText(self, text):
        self.text = text
        self.label.setText(text)
