"""
Main application window for SuperSID Pro
Modern PyQt6 interface with dark theme and professional styling
"""

import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QMenuBar, QToolBar, QPushButton,
    QLabel, QFrame, QSplitter, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction, QFont, QPalette, QColor

from gui.widgets.observatory_widget import ObservatoryWidget
from gui.widgets.monitoring_widget import MonitoringWidget
from gui.widgets.stations_widget import StationsWidget
from gui.widgets.space_weather_widget import SpaceWeatherWidget
from gui.widgets. chart_widget import ChartWidget
from gui.dialogs.setup_dialog import SetupDialog
from gui.styles.dark_theme import DarkTheme
from core.config_manager import ConfigManager
from core.logger import get_logger

class SuperSIDProApp(QApplication):
    """Main application class"""
    
    def __init__(self, config_manager: ConfigManager, debug: bool = False):
        super().__init__(sys. argv)
        
        self.config_manager = config_manager
        self.debug = debug
        self.logger = get_logger(__name__)
        
        # Set application properties
        self.setApplicationName("SuperSID Pro")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("Observatory Software Solutions")
        
        # Apply dark theme
        self.apply_theme()
        
        # Create main window
        self.main_window = MainWindow(config_manager)
        
        # Setup system tray
        self.setup_system_tray()
        
        self.logger.info("SuperSID Pro application initialized")
    
    def apply_theme(self):
        """Apply dark theme to application"""
        self.setStyle('Fusion')
        self.setPalette(DarkTheme.create_palette())
        self.setStyleSheet(DarkTheme.get_stylesheet())
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Create tray icon
            icon_path = Path("assets/icons/supersid_icon.png")
            if icon_path.exists():
                self. tray_icon.setIcon(QIcon(str(icon_path)))
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show SuperSID Pro", self)
            show_action.triggered.connect(self.main_window.show)
            tray_menu.addAction(show_action)
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit)
            tray_menu. addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            self.tray_icon.activated. connect(self.on_tray_activated)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    def run(self) -> int:
        """Run the application"""
        # Show setup dialog if first run
        if self.config_manager.get('application. first_run', True):
            setup_dialog = SetupDialog(self.config_manager)
            if setup_dialog.exec() == SetupDialog.DialogCode.Accepted:
                self.config_manager.set('application.first_run', False)
                self.config_manager.save_config()
            else:
                return 0
        
        self.main_window.show()
        return self.exec()

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        self.setup_ui()
        self.setup_menubar()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # Start data collection
        self.start_data_collection()
        
        self.logger.info("Main window initialized")
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("SuperSID Pro - Solar Observatory Monitoring")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Set window icon
        icon_path = Path("assets/icons/supersid_icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter
        main_splitter = QSplitter(Qt. Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Controls and info
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Charts and monitoring
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter. setSizes([400, 1000])
    
    def create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(400)
        
        layout = QVBoxLayout(panel)
        
        # Observatory info widget
        self.observatory_widget = ObservatoryWidget(self.config_manager)
        layout.addWidget(self. observatory_widget)
        
        # Stations widget
        self.stations_widget = StationsWidget(self.config_manager)
        layout.addWidget(self.stations_widget)
        
        # Space weather widget
        self.space_weather_widget = SpaceWeatherWidget(self.config_manager)
        layout.addWidget(self.space_weather_widget)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right monitoring panel"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Real-time monitoring tab
        monitoring_tab = MonitoringWidget(self.config_manager)
        tab_widget. addTab(monitoring_tab, "Real-time Monitoring")
        
        # Charts tab
        charts_tab = ChartWidget(self.config_manager)
        tab_widget.addTab(charts_tab, "Historical Data")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def setup_menubar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Session", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Data", self)
        open_action. setShortcut("Ctrl+O")
        file_menu. addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar. addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self. show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Start/Stop monitoring
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2d5a27;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d7037;
            }
        """)
        toolbar.addWidget(self.start_button)
        
        toolbar.addSeparator()
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ff0000; font-size: 20px;")
        toolbar.addWidget(self.status_indicator)
        
        status_label = QLabel("Disconnected")
        toolbar.addWidget(status_label)
    
    def setup_statusbar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.showMessage("SuperSID Pro Ready")
    
    def start_data_collection(self):
        """Start data collection processes"""
        # This will be implemented with actual data collection
        pass
    
    def show_settings(self):
        """Show settings dialog"""
        # TODO: Implement settings dialog
        pass
    
    def show_about(self):
        """Show about dialog"""
        # TODO: Implement about dialog
        pass
    
    def closeEvent(self, event):
        """Handle close event"""
        # Hide to system tray instead of closing
        event.ignore()
        self.hide()
        
        if hasattr(QApplication. instance(), 'tray_icon'):
            QApplication.instance(). tray_icon.showMessage(
                "SuperSID Pro",
                "Application minimized to tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )