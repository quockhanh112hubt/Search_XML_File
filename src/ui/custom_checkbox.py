"""
Custom Checkbox Widget with Beautiful Checkmark
"""

from PyQt5.QtWidgets import QCheckBox, QStyle, QStyleOption
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush, QFont
from src.ui.styles import COLORS


class CustomCheckBox(QCheckBox):
    """Custom checkbox with beautiful checkmark drawing"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(self.get_base_style())
        
    def get_base_style(self):
        """Get base stylesheet for the checkbox"""
        return f"""
            CustomCheckBox {{
                font-size: 14px;
                font-weight: 500;
                color: {COLORS['text_primary']};
                spacing: 12px;
                padding: 4px 0px;
            }}
            
            CustomCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {COLORS['border']};
                border-radius: 4px;
                background-color: {COLORS['bg_primary']};
                margin: 1px;
            }}
            
            CustomCheckBox::indicator:unchecked {{
                background-color: {COLORS['bg_primary']};
                border: 2px solid {COLORS['border']};
            }}
            
            CustomCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border: 2px solid {COLORS['primary']};
            }}
            
            CustomCheckBox::indicator:unchecked:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['primary_light']};
            }}
            
            CustomCheckBox::indicator:checked:hover {{
                background-color: {COLORS['primary_hover']};
                border-color: {COLORS['primary_hover']};
            }}
            
            CustomCheckBox:checked {{
                color: {COLORS['primary']};
                font-weight: 600;
            }}
            
            CustomCheckBox:hover {{
                color: {COLORS['text_white']};
            }}
            
            CustomCheckBox:disabled {{
                color: {COLORS['text_light']};
                opacity: 0.6;
            }}
        """
    
    def paintEvent(self, event):
        """Custom paint event to draw beautiful checkmark"""
        # Call parent paint event first
        super().paintEvent(event)
        
        if self.isChecked():
            # Get the indicator rectangle
            style = self.style()
            opt = QStyleOption()
            opt.initFrom(self)
            
            # Calculate indicator position
            indicator_rect = style.subElementRect(
                QStyle.SE_CheckBoxIndicator, opt, self
            )
            
            # Create painter
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Set pen for checkmark
            pen = QPen(Qt.white)
            pen.setWidth(2)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            
            # Draw checkmark
            self.draw_checkmark(painter, indicator_rect)
            
            painter.end()
    
    def draw_checkmark(self, painter, rect):
        """Draw a beautiful checkmark inside the given rectangle"""
        # Calculate checkmark points
        center_x = rect.center().x()
        center_y = rect.center().y()
        
        # Checkmark dimensions (relative to rect size)
        size = min(rect.width(), rect.height()) * 0.6
        
        # Checkmark points
        x1 = center_x - size * 0.3
        y1 = center_y
        
        x2 = center_x - size * 0.1
        y2 = center_y + size * 0.2
        
        x3 = center_x + size * 0.3
        y3 = center_y - size * 0.2
        
        # Draw checkmark lines
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        painter.drawLine(int(x2), int(y2), int(x3), int(y3))
    
    def setText(self, text):
        """Override setText to handle checkmark symbols in text"""
        # Remove any existing checkmark symbols
        clean_text = text.replace('✓ ', '').replace('☑ ', '').replace('✔ ', '')
        
        if self.isChecked():
            super().setText(f"✓ {clean_text}")
        else:
            super().setText(clean_text)
    
    def setChecked(self, checked):
        """Override setChecked to update text with checkmark"""
        super().setChecked(checked)
        
        # Update text with or without checkmark
        current_text = self.text()
        clean_text = current_text.replace('✓ ', '').replace('☑ ', '').replace('✔ ', '')
        
        if checked:
            super().setText(f"✓ {clean_text}")
        else:
            super().setText(clean_text)
            
        # Update style
        if checked:
            self.setStyleSheet(self.get_base_style() + f"""
                CustomCheckBox {{
                    color: {COLORS['primary']} !important;
                    font-weight: 600 !important;
                }}
            """)
        else:
            self.setStyleSheet(self.get_base_style())
