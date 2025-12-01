"""
Observatory information widget for SuperSID Pro
Displays and allows editing of observatory configuration
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QTextEdit, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
from typing import Optional
import pytz
from datetime import datetime

from core.config_manager import ConfigManager, ObservatoryConfig
from core. logger import get_logger

class ObservatoryWidget(QGroupBox):
    """Widget for observatory configuration and information"""
    
    # Signals
    configuration_changed = pyqtSignal(ObservatoryConfig)
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__("Observatory Configuration", parent)
        
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Current configuration
        self.current_config = self.config_manager.get_observatory_config()
        
        self.setup_ui()
        self.load_configuration()
        self.connect_signals()
        
        # Update status
        self.update_status_display()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setMaximumWidth(380)
        self.setMinimumHeight(400)
        
        main_layout = QVBoxLayout(self)
        
        # Status indicator at top
        self.create_status_section(main_layout)
        
        # Basic information form
        self.create_basic_info_section(main_layout)
        
        # Location information form  
        self.create_location_section(main_layout)
        
        # Additional information
        self.create_additional_info_section(main_layout)
        
        # Control buttons
        self.create_buttons_section(main_layout)
        
        # Apply modern styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2d2d2d;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #0078d4;
                font-size: 14px;
            }
            
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
                font-size: 11px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
            QComboBox:focus, QTextEdit:focus {
                border-color: #0078d4;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
    
    def create_status_section(self, layout: QVBoxLayout):
        """Create status indicator section"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_frame.setMaximumHeight(80)
        
        status_layout = QHBoxLayout(status_frame)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ff4444; font-size: 24px;")
        status_layout.addWidget(self. status_indicator)
        
        # Status text
        self.status_label = QLabel("Not Configured")
        self.status_label.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 14px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Monitor ID display (prominent)
        self.monitor_id_display = QLabel("Monitor: --")
        self.monitor_id_display.setStyleSheet("""
            color: #00ff00; 
            font-weight: bold; 
            font-size: 16px;
            padding: 5px;
            border: 1px solid #404040;
            border-radius: 4px;
            background-color: #1e1e1e;
        """)
        status_layout. addWidget(self.monitor_id_display)
        
        layout.addWidget(status_frame)
    
    def create_basic_info_section(self, layout: QVBoxLayout):
        """Create basic information section"""
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # Monitor ID
        self.monitor_id_spinbox = QSpinBox()
        self.monitor_id_spinbox.setRange(1, 9999)
        self.monitor_id_spinbox.setSpecialValueText("Not Set")
        basic_layout.addRow("Monitor ID:", self.monitor_id_spinbox)
        
        # Observatory name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter observatory name")
        basic_layout.addRow("Observatory Name:", self.name_edit)
        
        # Contact email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("contact@observatory.com")
        basic_layout.addRow("Contact Email:", self.email_edit)
        
        # Website
        self.website_edit = QLineEdit()
        self. website_edit.setPlaceholderText("https://www.observatory.com")
        basic_layout.addRow("Website:", self.website_edit)
        
        layout.addWidget(basic_group)
    
    def create_location_section(self, layout: QVBoxLayout):
        """Create location information section"""
        location_group = QGroupBox("Location")
        location_layout = QFormLayout(location_group)
        
        # Latitude
        self.latitude_spinbox = QDoubleSpinBox()
        self.latitude_spinbox.setRange(-90.0, 90.0)
        self.latitude_spinbox.setDecimals(6)
        self.latitude_spinbox.setSuffix("°")
        self.latitude_spinbox.setSpecialValueText("Not Set")
        location_layout.addRow("Latitude:", self.latitude_spinbox)
        
        # Longitude  
        self.longitude_spinbox = QDoubleSpinBox()
        self.longitude_spinbox.setRange(-180.0, 180.0)
        self.longitude_spinbox.setDecimals(6)
        self.longitude_spinbox.setSuffix("°")
        self. longitude_spinbox.setSpecialValueText("Not Set")
        location_layout.addRow("Longitude:", self.longitude_spinbox)
        
        # Elevation
        self.elevation_spinbox = QDoubleSpinBox()
        self.elevation_spinbox.setRange(-500.0, 9000.0)
        self.elevation_spinbox.setDecimals(1)
        self.elevation_spinbox.setSuffix(" m")
        location_layout.addRow("Elevation:", self.elevation_spinbox)
        
        # Timezone
        self.timezone_combo = QComboBox()
        self.populate_timezones()
        location_layout.addRow("Timezone:", self.timezone_combo)
        
        layout.addWidget(location_group)
    
    def create_additional_info_section(self, layout: QVBoxLayout):
        """Create additional information section"""
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)
        
        # Description
        self.description_edit = QTextEdit()
        self. description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Brief description of the observatory...")
        additional_layout.addRow("Description:", self.description_edit)
        
        # Established date
        self.established_edit = QLineEdit()
        self.established_edit.setPlaceholderText("YYYY or YYYY-MM-DD")
        additional_layout.addRow("Established:", self.established_edit)
        
        layout.addWidget(additional_group)
    
    def create_buttons_section(self, layout: QVBoxLayout):
        """Create control buttons section"""
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Configuration")
        self.save_button.setIcon(QIcon("assets/icons/save.png"))  # You'll need to add this icon
        buttons_layout.addWidget(self. save_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button. setIcon(QIcon("assets/icons/reset.png"))  # You'll need to add this icon
        buttons_layout.addWidget(self.reset_button)
        
        layout.addLayout(buttons_layout)
    
    def populate_timezones(self):
        """Populate timezone combobox with common timezones"""
        # Common timezones for observatories
        common_timezones = [
            "UTC",
            "UTC-1", "UTC-2", "UTC-3", "UTC-4", "UTC-5", "UTC-6",
            "UTC-7", "UTC-8", "UTC-9", "UTC-10", "UTC-11", "UTC-12",
            "UTC+1", "UTC+2", "UTC+3", "UTC+4", "UTC+5", "UTC+6",
            "UTC+7", "UTC+8", "UTC+9", "UTC+10", "UTC+11", "UTC+12",
            "America/New_York",
            "America/Chicago", 
            "America/Denver",
            "America/Los_Angeles",
            "America/Montevideo",
            "America/Argentina/Buenos_Aires",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/Moscow",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney"
        ]
        
        self.timezone_combo.addItems(common_timezones)
    
    def connect_signals(self):
        """Connect widget signals"""
        # Connect value change signals
        self.monitor_id_spinbox.valueChanged.connect(self.on_configuration_changed)
        self.name_edit.textChanged.connect(self.on_configuration_changed)
        self.email_edit. textChanged.connect(self.on_configuration_changed)
        self.website_edit.textChanged. connect(self.on_configuration_changed)
        self.latitude_spinbox.valueChanged.connect(self.on_configuration_changed)
        self.longitude_spinbox.valueChanged.connect(self. on_configuration_changed)
        self.elevation_spinbox.valueChanged.connect(self.on_configuration_changed)
        self. timezone_combo.currentTextChanged. connect(self.on_configuration_changed)
        self.description_edit.textChanged.connect(self.on_configuration_changed)
        self.established_edit. textChanged.connect(self.on_configuration_changed)
        
        # Connect buttons
        self.save_button. clicked.connect(self.save_configuration)
        self.reset_button.clicked.connect(self. reset_configuration)
    
    def load_configuration(self):
        """Load configuration into widgets"""
        config = self.current_config
        
        # Block signals during loading
        self.blockSignals(True)
        
        self.monitor_id_spinbox. setValue(config.monitor_id)
        self.name_edit. setText(config.name)
        self.email_edit.setText(config.contact_email)
        self.website_edit.setText(config.website)
        self.latitude_spinbox.setValue(config.latitude)
        self.longitude_spinbox.setValue(config.longitude)
        self.elevation_spinbox. setValue(config.elevation)
        
        # Set timezone
        timezone_index = self.timezone_combo.findText(config.timezone)
        if timezone_index >= 0:
            self.timezone_combo.setCurrentIndex(timezone_index)
        
        self.description_edit.setPlainText(config.description)
        self.established_edit. setText(config.established or "")
        
        # Restore signals
        self.blockSignals(False)
    
    def get_current_configuration(self) -> ObservatoryConfig:
        """Get current configuration from widgets"""
        return ObservatoryConfig(
            monitor_id=self.monitor_id_spinbox.value(),
            name=self.name_edit.text(),
            latitude=self.latitude_spinbox. value(),
            longitude=self. longitude_spinbox.value(),
            timezone=self.timezone_combo.currentText(),
            elevation=self.elevation_spinbox. value(),
            contact_email=self.email_edit.text(),
            website=self.website_edit.text(),
            description=self.description_edit.toPlainText(),
            established=self.established_edit.text() or None
        )
    
    def on_configuration_changed(self):
        """Handle configuration changes"""
        self.update_status_display()
    
    def update_status_display(self):
        """Update status indicators"""
        config = self.get_current_configuration()
        
        # Check if configuration is complete
        is_complete = (
            config.monitor_id > 0 and
            config. name. strip() != "" and
            config.latitude != 0.0 and
            config.longitude != 0.0
        )
        
        if is_complete:
            self.status_indicator.setStyleSheet("color: #00ff00; font-size: 24px;")
            self.status_label.setText("Configuration Complete")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
            self.monitor_id_display. setText(f"Monitor: #{config.monitor_id:03d}")
        else:
            self.status_indicator.setStyleSheet("color: #ffaa00; font-size: 24px;")
            self.status_label.setText("Configuration Incomplete")
            self.status_label.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 14px;")
            self.monitor_id_display.setText("Monitor: --")
    
    def save_configuration(self):
        """Save current configuration"""
        try:
            config = self.get_current_configuration()
            
            # Validate configuration
            validation_errors = self.validate_configuration(config)
            if validation_errors:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Configuration validation failed:\n" + "\n".join(validation_errors)
                )
                return
            
            # Save to config manager
            self.config_manager. set_observatory_config(config)
            self.config_manager.save_config()
            
            self.current_config = config
            self. update_status_display()
            
            # Emit signal
            self.configuration_changed.emit(config)
            
            QMessageBox.information(
                self,
                "Configuration Saved",
                f"Observatory configuration for Monitor #{config.monitor_id:03d} saved successfully!"
            )
            
            self.logger.info(f"Observatory configuration saved: Monitor #{config.monitor_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving observatory configuration: {e}")
            QMessageBox.critical(
                self,
                "Save Error", 
                f"Failed to save configuration:\n{str(e)}"
            )
    
    def reset_configuration(self):
        """Reset configuration to last saved values"""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Reset all changes to last saved configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_config = self.config_manager.get_observatory_config()
            self.load_configuration()
            self.update_status_display()
            self.logger.info("Observatory configuration reset to saved values")
    
    def validate_configuration(self, config: ObservatoryConfig) -> list[str]:
        """Validate observatory configuration"""
        errors = []
        
        if config.monitor_id <= 0:
            errors.append("Monitor ID must be greater than 0")
        
        if not config.name.strip():
            errors.append("Observatory name is required")
        
        if not (-90 <= config.latitude <= 90):
            errors.append("Latitude must be between -90 and 90 degrees")
        
        if not (-180 <= config.longitude <= 180):
            errors.append("Longitude must be between -180 and 180 degrees")
        
        if config.elevation < -500 or config.elevation > 9000:
            errors.append("Elevation must be between -500 and 9000 meters")
        
        # Email validation (basic)
        if config.contact_email and "@" not in config.contact_email:
            errors.append("Invalid email format")
        
        # Website validation (basic)
        if config.website and not (config.website.startswith("http://") or config.website.startswith("https://")):
            errors.append("Website must start with http:// or https://")
        
        return errors
    
    def get_coordinates_string(self) -> str:
        """Get formatted coordinates string"""
        config = self.get_current_configuration()
        
        lat_dir = "N" if config.latitude >= 0 else "S"
        lon_dir = "E" if config.longitude >= 0 else "W"
        
        return f"{abs(config.latitude):.4f}°{lat_dir}, {abs(config.longitude):. 4f}°{lon_dir}"