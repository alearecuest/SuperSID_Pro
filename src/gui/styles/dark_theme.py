"""
Dark theme styling for SuperSID Pro
Modern, professional dark theme with blue accents
"""

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

class DarkTheme:
    """Dark theme configuration"""
    
    # Color palette
    BACKGROUND = "#1e1e1e"
    SURFACE = "#2d2d2d"
    PRIMARY = "#0078d4"
    PRIMARY_DARK = "#106ebe"
    ACCENT = "#00ff00"
    ERROR = "#ff4444"
    WARNING = "#ffaa00"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b3b3b3"
    BORDER = "#404040"
    
    @staticmethod
    def create_palette() -> QPalette:
        """Create dark theme palette"""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(DarkTheme.BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DarkTheme.TEXT_PRIMARY))
        
        # Base colors
        palette.setColor(QPalette.ColorRole.Base, QColor(DarkTheme.SURFACE))
        palette. setColor(QPalette.ColorRole.AlternateBase, QColor("#3a3a3a"))
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(DarkTheme.TEXT_PRIMARY))
        palette.setColor(QPalette. ColorRole.BrightText, QColor("#ffffff"))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(DarkTheme. SURFACE))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DarkTheme.TEXT_PRIMARY))
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole. Highlight, QColor(DarkTheme.PRIMARY))
        palette. setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, QColor(DarkTheme.PRIMARY))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(DarkTheme.PRIMARY_DARK))
        
        return palette
    
    @staticmethod
    def get_stylesheet() -> str:
        """Get complete application stylesheet"""
        return f"""
        /* Main application styling */
        QMainWindow {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme. TEXT_PRIMARY};
        }}
        
        /* Tab widget styling */
        QTabWidget::pane {{
            border: 1px solid {DarkTheme.BORDER};
            background-color: {DarkTheme.SURFACE};
        }}
        
        QTabBar::tab {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.TEXT_SECONDARY};
            padding: 8px 16px;
            margin: 2px;
            border: 1px solid {DarkTheme.BORDER};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {DarkTheme.PRIMARY};
            color: {DarkTheme.TEXT_PRIMARY};
        }}
        
        QTabBar::tab:hover {{
            background-color: {DarkTheme.PRIMARY_DARK};
            color: {DarkTheme. TEXT_PRIMARY};
        }}
        
        /* Frame styling */
        QFrame {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            border-radius: 4px;
            margin: 2px;
        }}
        
        /* Label styling */
        QLabel {{
            color: {DarkTheme.TEXT_PRIMARY};
            background-color: transparent;
        }}
        
        /* Button styling */
        QPushButton {{
            background-color: {DarkTheme.SURFACE};
            color: {DarkTheme.TEXT_PRIMARY};
            border: 1px solid {DarkTheme.BORDER};
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {DarkTheme.PRIMARY};
            border-color: {DarkTheme. PRIMARY};
        }}
        
        QPushButton:pressed {{
            background-color: {DarkTheme.PRIMARY_DARK};
        }}
        
        QPushButton:disabled {{
            background-color: #404040;
            color: #808080;
            border-color: #404040;
        }}
        
        /* Input styling */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.TEXT_PRIMARY};
            border: 1px solid {DarkTheme.BORDER};
            padding: 6px;
            border-radius: 4px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, 
        QDoubleSpinBox:focus, QComboBox:focus {{
            border-color: {DarkTheme.PRIMARY};
        }}
        
        /* List and tree widgets */
        QListWidget, QTreeWidget, QTableWidget {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.TEXT_PRIMARY};
            border: 1px solid {DarkTheme.BORDER};
            gridline-color: {DarkTheme.BORDER};
            selection-background-color: {DarkTheme.PRIMARY};
        }}
        
        QListWidget::item, QTreeWidget::item, QTableWidget::item {{
            padding: 4px;
        }}
        
        QListWidget::item:selected, QTreeWidget::item:selected, 
        QTableWidget::item:selected {{
            background-color: {DarkTheme.PRIMARY};
        }}
        
        QListWidget::item:hover, QTreeWidget::item:hover, 
        QTableWidget::item:hover {{
            background-color: {DarkTheme.PRIMARY_DARK};
        }}
        
        /* Scrollbar styling */
        QScrollBar:vertical {{
            background-color: {DarkTheme. BACKGROUND};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {DarkTheme.BORDER};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {DarkTheme.PRIMARY};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* Menu styling */
        QMenuBar {{
            background-color: {DarkTheme.SURFACE};
            color: {DarkTheme.TEXT_PRIMARY};
            border-bottom: 1px solid {DarkTheme.BORDER};
        }}
        
        QMenuBar::item {{
            padding: 6px 12px;
            background-color: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {DarkTheme.PRIMARY};
        }}
        
        QMenu {{
            background-color: {DarkTheme.SURFACE};
            color: {DarkTheme.TEXT_PRIMARY};
            border: 1px solid {DarkTheme.BORDER};
        }}
        
        QMenu::item {{
            padding: 6px 12px;
        }}
        
        QMenu::item:selected {{
            background-color: {DarkTheme. PRIMARY};
        }}
        
        /* Toolbar styling */
        QToolBar {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            spacing: 3px;
        }}
        
        /* Status bar styling */
        QStatusBar {{
            background-color: {DarkTheme.SURFACE};
            color: {DarkTheme.TEXT_PRIMARY};
            border-top: 1px solid {DarkTheme.BORDER};
        }}
        
        /* Progress bar styling */
        QProgressBar {{
            border: 1px solid {DarkTheme.BORDER};
            border-radius: 4px;
            background-color: {DarkTheme.BACKGROUND};
            text-align: center;
            color: {DarkTheme.TEXT_PRIMARY};
        }}
        
        QProgressBar::chunk {{
            background-color: {DarkTheme.PRIMARY};
            border-radius: 3px;
        }}
        
        /* Splitter styling */
        QSplitter::handle {{
            background-color: {DarkTheme.BORDER};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        """