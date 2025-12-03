"""
Main application window for SuperSID Pro - UPDATED with Charts
Modern PyQt6 interface with dark theme and professional styling
"""

import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QMenuBar, QToolBar, QPushButton,
    QLabel, QFrame, QSplitter, QSystemTrayIcon, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction, QFont, QPalette, QColor

from gui.widgets.observatory_widget import ObservatoryWidget
from gui.widgets.monitoring_widget import MonitoringWidget  # UPDATED
from gui.widgets.stations_widget import StationsWidget
from gui.widgets.space_weather_widget import SpaceWeatherWidget
from gui.widgets.vlf_database_widget import VLFDatabaseWidget
from gui.widgets. chart_widget import ChartWidget  # NEW
from gui.dialogs.setup_dialog import SetupDialog
from gui.styles.dark_theme import DarkTheme
from core.config_manager import ConfigManager
from core.logger import get_logger
from gui.widgets.realtime_vlf_widget import RealtimeVLFWidget
from core.vlf_gui_integration import VLFGUIIntegration

class SuperSIDProApp(QApplication):
    """Main application class"""
    
    def __init__(self, config_manager: ConfigManager, debug: bool = False):
        super().__init__(sys.argv)
        
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
        self. setPalette(DarkTheme.create_palette())
        self.setStyleSheet(DarkTheme.get_stylesheet())
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self. tray_icon = QSystemTrayIcon(self)
            
            # Create tray icon
            icon_path = Path("assets/icons/supersid_icon.png")
            if icon_path.exists():
                self.tray_icon.setIcon(QIcon(str(icon_path)))
            
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
            
            self.tray_icon.activated.connect(self.on_tray_activated)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    def run(self) -> int:
        """Run the application"""
        # Show setup dialog if first run
        if self.config_manager.get('application.first_run', True):
            reply = QMessageBox.question(
                None,
                "First Run Setup", 
                "This appears to be your first time running SuperSID Pro.\n\n"
                "Would you like to run the setup wizard to configure your observatory? ",
                QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # TODO: Implement setup dialog
                pass
            
            self.config_manager.set('application.first_run', False)
            self.config_manager.save_config()
        
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
        
        # Start monitoring
        self.start_monitoring()
        # Initialize VLF integration
        self.vlf_integration = VLFGUIIntegration(self.config_manager, self.vlf_widget)
        self.logger.info("Main window initialized")
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("SuperSID Pro - Solar Observatory Monitoring System")
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
        layout.addWidget(self.observatory_widget)
        
        # Stations widget
        self.stations_widget = StationsWidget(self. config_manager)
        layout. addWidget(self.stations_widget)
        
        # Space weather widget
        self.space_weather_widget = SpaceWeatherWidget(self.config_manager)
        layout.addWidget(self.space_weather_widget)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right monitoring panel"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        
        # Create tab widget for different views
        tab_widget = QTabWidget()
        
        # Real-time monitoring tab (MAIN CHARTS TAB)
        self.monitoring_tab = MonitoringWidget(self.config_manager)
        tab_widget. addTab(self.monitoring_tab, "Real-time Monitoring")
        
        # Historical data analysis tab
        self.charts_tab = ChartWidget(self.config_manager)
        tab_widget.addTab(self. charts_tab, "Historical Analysis")
        
        # Space weather details tab
        space_weather_detail = SpaceWeatherWidget(self.config_manager)
        tab_widget.addTab(space_weather_detail, "Space Weather")
        
        # VLF Database management tab
        self.vlf_database_tab = VLFDatabaseWidget(self.config_manager)
        tab_widget.addTab(self.vlf_database_tab, "VLF Database")

        # Real-time VLF monitoring tab
        self.vlf_widget = RealtimeVLFWidget()
        tab_widget.addTab(self. vlf_widget, "Real-time VLF")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def setup_menubar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_session_action = QAction("New Session", self)
        new_session_action.setShortcut("Ctrl+N")
        new_session_action.triggered.connect(self.new_session)
        file_menu.addAction(new_session_action)
        
        open_data_action = QAction("Open Data File", self)
        open_data_action.setShortcut("Ctrl+O")
        open_data_action.triggered.connect(self.open_data_file)
        file_menu.addAction(open_data_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export Data", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu. addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self. close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        fullscreen_action = QAction("Toggle Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = QAction("Settings", self)
        settings_action. setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        calibration_action = QAction("Station Calibration", self)
        calibration_action.triggered.connect(self.show_calibration)
        tools_menu. addAction(calibration_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About SuperSID Pro", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("Documentation", self)
        docs_action. setShortcut("F1")
        docs_action. triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
    
    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Start/Stop monitoring
        self.start_button = QPushButton("Pause")
        self.start_button. setToolTip("Pause/Resume monitoring")
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
            QPushButton:pressed {
                background-color: #1d4a17;
            }
        """)
        self.start_button. clicked.connect(self.toggle_monitoring)
        toolbar.addWidget(self.start_button)
        
        toolbar.addSeparator()
        
        # Status indicators
        self.connection_status = QLabel("🔴")
        self.connection_status. setToolTip("Connection Status")
        toolbar.addWidget(self.connection_status)
        
        self. data_status = QLabel("Ready")
        toolbar.addWidget(self.data_status)
        
        toolbar.addSeparator()
        
        # Quick export
        export_button = QPushButton("Export")
        export_button.setToolTip("Quick export current data")
        export_button. clicked.connect(self.export_data)
        toolbar.addWidget(export_button)
        
        # Screenshot
        screenshot_button = QPushButton("Screenshot")
        screenshot_button.setToolTip("Take screenshot of current view")
        screenshot_button.clicked.connect(self.take_screenshot)
        toolbar.addWidget(screenshot_button)
    
    def setup_statusbar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status messages
        self.status_message = QLabel("SuperSID Pro Ready")
        self.status_bar.addWidget(self.status_message)
        
        # Permanent widgets (right side)
        self.data_rate_label = QLabel("Data: 0 Hz")
        self.status_bar.addPermanentWidget(self.data_rate_label)
        
        self.memory_label = QLabel("Memory: 0 MB")
        self.status_bar.addPermanentWidget(self.memory_label)
        
        self.time_label = QLabel()
        self.status_bar. addPermanentWidget(self. time_label)
        
        # Update timer
        self.status_timer = QTimer()
        self.status_timer.timeout. connect(self.update_statusbar)
        self.status_timer.start(1000)
    
    def start_monitoring(self):
        """Start monitoring processes"""
        self.connection_status.setText("🟢")
        self.start_button.setText("Pause")
        self.status_message.setText("Monitoring Active")
        
        self.logger.info("Monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring processes"""
        self. connection_status.setText("🔴")
        self.start_button.setText("Start")
        self.status_message.setText("Monitoring Paused")
        
        self. logger.info("Monitoring paused")
    
    def toggle_monitoring(self):
        """Toggle monitoring state"""
        if self.start_button.text() == "Pause":
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def update_statusbar(self):
        """Update status bar information"""
        from datetime import datetime
        import psutil
        
        # Update time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label. setText(f"{current_time}")
        
        # Update memory usage
        try:
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            self.memory_label.setText(f"Memory: {memory_mb:.0f} MB")
        except:
            self.memory_label. setText("Memory: N/A")
    
    # Menu action handlers
    def new_session(self):
        """Start a new monitoring session"""
        self.logger. info("New session requested")
        # TODO: Implement new session logic
    
    def open_data_file(self):
        """Open a data file for analysis"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            self.logger. info(f"Opening data file: {filename}")
            # TODO: Implement data file loading
    
    def export_data(self):
        """Export current data"""
        self.logger.info("Data export requested")
        # TODO: Implement data export dialog
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def show_settings(self):
        """Show settings dialog"""
        self.logger.info("Settings dialog requested")
        # TODO: Implement settings dialog
    
    def show_calibration(self):
        """Show calibration dialog"""
        self.logger.info("Calibration dialog requested")
        # TODO: Implement calibration dialog
    
    def take_screenshot(self):
        """Take screenshot of current view"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"supersid_screenshot_{timestamp}.png"
        
        pixmap = self.grab()
        if pixmap. save(filename):
            self.status_message.setText(f"Screenshot saved: {filename}")
            self.logger.info(f"Screenshot saved: {filename}")
        else:
            self.status_message.setText("Failed to save screenshot")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SuperSID Pro",
            """
            <h2>SuperSID Pro v1.0.0</h2>
            <p><b>Professional Solar Radio Telescope Monitoring Software</b></p>
            
            <p>SuperSID Pro is designed for solar observatories worldwide to monitor 
            VLF (Very Low Frequency) signals and correlate them with space weather 
            data for solar activity research.</p>
            
            <p><b>Features:</b></p>
            <ul>
            <li>Real-time VLF signal monitoring</li>
            <li>Space weather integration</li>
            <li>Professional data analysis tools</li>
            <li>Multi-station support</li>
            <li>Historical data analysis</li>
            </ul>
            
            <p><b>Contact:</b><br>
            Observatory Software Solutions<br>
            support@observatorysoftware.com</p>
            """
        )
    
    def show_documentation(self):
        """Show documentation"""
        self.logger.info("Documentation requested")
        # TODO: Open documentation
    
    def closeEvent(self, event):
        """Handle close event"""
        # Cleanup VLF integration
        if hasattr(self, 'vlf_integration'):
            self.vlf_integration.cleanup()
    
        # Hide to system tray instead of closing
        event.ignore()
        self.hide()
    
        if hasattr(QApplication.instance(), 'tray_icon'):
            QApplication.instance().tray_icon.showMessage(
                "SuperSID Pro",
                "Application minimized to system tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
