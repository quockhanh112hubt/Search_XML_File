"""
Modern UI Styles for XML Search Application
"""

# Color Palette - Dark Theme
COLORS = {
    # Primary colors
    'primary': '#3b82f6',      # Bright Blue
    'primary_hover': '#2563eb',
    'primary_light': '#1e293b',
    
    # Secondary colors  
    'secondary': '#64748b',    # Slate
    'secondary_light': '#374151',
    
    # Success/Error colors
    'success': '#10b981',      # Emerald
    'success_light': '#064e3b',
    'error': '#ef4444',        # Red
    'error_light': '#7f1d1d',
    'warning': '#f59e0b',      # Amber
    'warning_light': '#78350f',
    
    # Background colors - Dark theme
    'bg_primary': '#111827',   # Dark gray
    'bg_secondary': '#1f2937', # Darker gray
    'bg_dark': '#0f172a',      # Very dark
    
    # Text colors - Light for dark theme
    'text_primary': '#f9fafb', # Light
    'text_secondary': '#d1d5db', # Gray
    'text_light': '#94a3b8',   # Light gray
    'text_white': '#ffffff',
    
    # Border colors - Dark theme
    'border': '#374151',       # Dark border
    'border_focus': '#3b82f6', # Blue border
}

# Modern button styles
BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: {COLORS['text_white']};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['primary_hover']};
        }}
        QPushButton:pressed {{
            background-color: #1e40af;
        }}
        QPushButton:disabled {{
            background-color: {COLORS['secondary']};
            color: {COLORS['text_light']};
        }}
    """,
    
    'secondary': f"""
        QPushButton {{
            background-color: {COLORS['bg_primary']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border']};
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            min-height: 20px;
        }}
        QPushButton:hover {{
            border-color: {COLORS['primary']};
            color: {COLORS['primary']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['primary_light']};
        }}
    """,
    
    'success': f"""
        QPushButton {{
            background-color: {COLORS['success']};
            color: {COLORS['text_white']};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: #047857;
        }}
    """,
    
    'error': f"""
        QPushButton {{
            background-color: {COLORS['error']};
            color: {COLORS['text_white']};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: #b91c1c;
        }}
    """,
}

# Input field styles
INPUT_STYLES = f"""
    QLineEdit, QTextEdit, QPlainTextEdit {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 14px;
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {COLORS['border_focus']};
        outline: none;
    }}
    QDateEdit {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 16px;
        font-weight: 600;
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        min-height: 35px;
    }}
    QDateEdit:focus {{
        border-color: {COLORS['border_focus']};
    }}
    QDateEdit::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left-width: 1px;
        border-left-color: {COLORS['border']};
        border-left-style: solid;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
        background-color: {COLORS['primary']};
        padding: 0px;
    }}
    QDateEdit::down-arrow {{
        image: none;
        border: none;
        width: 16px;
        height: 16px;
        background-color: transparent;
    }}
    QDateEdit::drop-down:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    QDateEdit QCalendarWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
    }}
    QDateEdit QCalendarWidget QToolButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 5px;
        margin: 2px;
    }}
    QDateEdit QCalendarWidget QToolButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    QDateEdit QCalendarWidget QAbstractItemView:enabled {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        selection-background-color: {COLORS['primary']};
        selection-color: white;
    }}
    QSpinBox {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        background-color: {COLORS['bg_primary']};
        min-height: 20px;
    }}
    QSpinBox:focus {{
        border-color: {COLORS['border_focus']};
    }}
"""

# ComboBox styles
COMBOBOX_STYLES = f"""
    QComboBox {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        background-color: {COLORS['bg_primary']};
        min-height: 20px;
        color: {COLORS['text_primary']};
    }}
    QComboBox:focus {{
        border-color: {COLORS['border_focus']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {COLORS['text_secondary']};
        margin-right: 10px;
    }}
    QComboBox QAbstractItemView {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        background-color: {COLORS['bg_primary']};
        selection-background-color: {COLORS['primary_light']};
        padding: 4px;
    }}
"""

# GroupBox styles
GROUPBOX_STYLES = f"""
    QGroupBox {{
        font-size: 16px;
        font-weight: 600;
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 12px;
        margin-top: 12px;
        padding-top: 12px;
        background-color: {COLORS['bg_primary']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 4px 12px;
        background-color: transparent;
        color: {COLORS['primary']};
        font-weight: 700;
        border: none;
        border-radius: 6px;
    }}
"""

# Tab styles
TAB_STYLES = f"""
    QTabWidget::pane {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        background-color: {COLORS['bg_primary']};
        margin-top: -2px;
    }}
    QTabBar::tab {{
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_secondary']};
        border: 2px solid {COLORS['border']};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 12px 24px;
        margin-right: 2px;
        font-size: 14px;
        font-weight: 600;
        min-width: 100px;
    }}
    QTabBar::tab:selected {{
        background-color: {COLORS['primary']};
        color: {COLORS['text_white']};
        border-color: {COLORS['primary']};
        border-bottom: 2px solid {COLORS['primary']};
        font-weight: 700;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
    }}
"""

# Table styles
TABLE_STYLES = f"""
    QTableWidget {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        background-color: {COLORS['bg_primary']};
        gridline-color: {COLORS['border']};
        font-size: 14px;
        selection-background-color: {COLORS['primary_light']};
        alternate-background-color: #374151;
    }}
    QTableWidget::item {{
        padding: 12px 8px;
        border-bottom: 1px solid {COLORS['border']};
    }}
    QTableWidget::item:selected {{
        background-color: {COLORS['primary_light']};
        color: {COLORS['primary']};
    }}
    QHeaderView::section {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 12px 8px;
        font-weight: 600;
        font-size: 14px;
    }}
    QHeaderView::section:vertical {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        padding: 8px 12px;
        font-weight: 600;
        font-size: 14px;
        min-width: 50px;
        text-align: center;
    }}
"""

# Progress bar styles
PROGRESS_STYLES = f"""
    QProgressBar {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        background-color: {COLORS['bg_secondary']};
        text-align: center;
        font-size: 14px;
        font-weight: 600;
        color: {COLORS['text_primary']};
        height: 24px;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['primary']};
        border-radius: 6px;
        margin: 2px;
    }}
"""

# Checkbox styles - Modern and Beautiful
CHECKBOX_STYLES = f"""
    QCheckBox {{
        font-size: 14px;
        font-weight: 500;
        color: {COLORS['text_primary']};
        spacing: 12px;
        padding: 4px 0px;
    }}
    
    /* Modern checkbox indicator */
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {COLORS['border']};
        border-radius: 4px;
        background-color: {COLORS['bg_primary']};
        margin: 1px;
    }}
    
    /* Unchecked state */
    QCheckBox::indicator:unchecked {{
        background-color: {COLORS['bg_primary']};
        border: 2px solid {COLORS['border']};
    }}
    
    /* Checked state with checkmark */
    QCheckBox::indicator:checked {{
        background-color: {COLORS['primary']};
        border: 2px solid {COLORS['primary']};
        color: white;
        font-weight: bold;
        font-size: 14px;
        text-align: center;
    }}
    
    /* Hover effects */
    QCheckBox::indicator:unchecked:hover {{
        border-color: {COLORS['primary']};
        background-color: {COLORS['primary_light']};
    }}
    
    QCheckBox::indicator:checked:hover {{
        background-color: {COLORS['primary_hover']};
        border-color: {COLORS['primary_hover']};
    }}
    
    /* Focus state */
    QCheckBox::indicator:focus {{
        outline: none;
        border-color: {COLORS['primary']};
    }}
    
    /* Disabled state */
    QCheckBox::indicator:disabled {{
        background-color: {COLORS['bg_secondary']};
        border-color: {COLORS['secondary']};
        opacity: 0.5;
    }}
    
    QCheckBox:disabled {{
        color: {COLORS['text_light']};
        opacity: 0.6;
    }}
    
    /* Text styling for different states */
    QCheckBox:checked {{
        color: {COLORS['primary']};
        font-weight: 600;
    }}
    
    QCheckBox:hover {{
        color: {COLORS['text_white']};
    }}
"""

# Label styles
LABEL_STYLES = f"""
    QLabel {{
        color: {COLORS['text_primary']};
        font-size: 14px;
    }}
    .header-label {{
        font-size: 18px;
        font-weight: 700;
        color: {COLORS['text_primary']};
        margin: 16px 0;
    }}
    .status-label {{
        font-size: 14px;
        font-weight: 600;
        padding: 8px 12px;
        border-radius: 6px;
        background-color: {COLORS['bg_secondary']};
    }}
"""

# Main window styles
MAIN_WINDOW_STYLES = f"""
    QMainWindow {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
    }}
    QWidget {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}
"""

# Combine all styles
COMPLETE_STYLESHEET = f"""
{MAIN_WINDOW_STYLES}
{INPUT_STYLES}
{COMBOBOX_STYLES}
{GROUPBOX_STYLES}
{TAB_STYLES}
{TABLE_STYLES}
{PROGRESS_STYLES}
{CHECKBOX_STYLES}
{LABEL_STYLES}
"""
