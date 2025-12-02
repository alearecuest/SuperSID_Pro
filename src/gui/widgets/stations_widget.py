"""
VLF Stations management widget for SuperSID Pro
Displays and manages VLF transmitter stations configuration
"""

from PyQt6. QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QCheckBox, QFrame,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, QTextEdit,
    QMessageBox, QMenu, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QAction, QPalette, QColor, QPixmap
from typing import Optional, List
import json
import xml.etree.ElementTree as ET

from core.config_manager import ConfigManager, VLFStation
from core.logger import get_logger

class StationItem(QWidget):
    """Custom widget for displaying VLF station information"""
    
    # Signals
    toggled = pyqtSignal(str, bool)  # station_code, enabled
    edit_requested = pyqtSignal(str)  # station_code
    remove_requested = pyqtSignal(str)  # station_code
    
    def __init__(self, station: VLFStation, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.station = station
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the station item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Enable checkbox
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox. setChecked(self.station. enabled)
        self.enabled_checkbox.stateChanged.connect(self.on_toggle)
        layout.addWidget(self.enabled_checkbox)
        
        # Station info layout
        info_layout = QVBoxLayout()
        
        # Main info line
        main_info = QHBoxLayout()
        
        # Station code (prominent)
        code_label = QLabel(self.station.code)
        code_label.setStyleSheet("""
            QLabel {
                color: #0078d4;
                font-weight: bold;
                font-size: 13px;
                min-width: 60px;
            }
        """)
        main_info.addWidget(code_label)
        
        # Frequency
        freq_label = QLabel(f"{self.station.frequency:.1f} kHz")
        freq_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        main_info.addWidget(freq_label)
        
        main_info.addStretch()
        
        # Power info
        if self.station.power:
            power_label = QLabel(self.station.power)
            power_label.setStyleSheet("color: #ffaa00; font-size: 10px;")
            main_info.addWidget(power_label)
        
        info_layout.addLayout(main_info)
        
        # Location line
        location_label = QLabel(f"{self.station.name}")
        location_label.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        info_layout.addWidget(location_label)
        
        # Country line
        if self.station.country:
            country_label = QLabel(self.station.country)
            country_label.setStyleSheet("color: #888888; font-size: 10px; font-style: italic;")
            info_layout.addWidget(country_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Signal strength indicator (placeholder for future)
        self.signal_indicator = QLabel("●")
        self.signal_indicator.setStyleSheet("color: #404040; font-size: 16px;")
        self.signal_indicator.setToolTip("Signal strength indicator")
        layout.addWidget(self. signal_indicator)
        
        # Set background style
        self.setStyleSheet("""
            StationItem {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                margin: 1px;
            }
            
            StationItem:hover {
                background-color: #3d3d3d;
                border-color: #0078d4;
            }
        """)
        
        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def on_toggle(self, state: int):
        """Handle enable/disable toggle"""
        enabled = state == Qt.CheckState. Checked. value
        self.station.enabled = enabled
        self.toggled.emit(self.station. code, enabled)
        
        # Update visual state
        alpha = "FF" if enabled else "80"
        if enabled:
            self.setStyleSheet(self.styleSheet().replace("color: #", f"color: #"))
        else:
            # Make disabled stations more transparent
            pass
    
    def show_context_menu(self, position):
        """Show context menu"""
        menu = QMenu(self)
        
        edit_action = QAction("Edit Station", self)
        edit_action.setIcon(QIcon("assets/icons/edit.png"))
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.station.code))
        menu.addAction(edit_action)
        
        remove_action = QAction("Remove Station", self)
        remove_action.setIcon(QIcon("assets/icons/remove.png"))
        remove_action.triggered.connect(lambda: self.remove_requested.emit(self.station.code))
        menu.addAction(remove_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def update_signal_strength(self, strength: float):
        """Update signal strength indicator"""
        if strength > 0.8:
            color = "#00ff00"  # Strong signal - green
        elif strength > 0.5:
            color = "#ffaa00"  # Medium signal - yellow  
        elif strength > 0.2:
            color = "#ff8800"  # Weak signal - orange
        else:
            color = "#ff0000"  # Very weak/no signal - red
        
        self.signal_indicator.setStyleSheet(f"color: {color}; font-size: 16px;")

class StationEditDialog(QDialog):
    """Dialog for editing VLF station properties"""
    
    def __init__(self, station: Optional[VLFStation] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.station = station or VLFStation()
        self.is_new = station is None
        
        self.setWindowTitle("Add New Station" if self.is_new else "Edit Station")
        self.setModal(True)
        self.resize(400, 500)
        
        self.setup_ui()
        if not self.is_new:
            self.load_station_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Station code
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("e.g., NAA")
        form_layout.addRow("Station Code:", self.code_edit)
        
        # Station name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Cutler, ME")
        form_layout.addRow("Station Name:", self.name_edit)
        
        # Frequency
        self.frequency_spinbox = QDoubleSpinBox()
        self.frequency_spinbox.setRange(10.0, 100.0)
        self.frequency_spinbox.setDecimals(2)
        self.frequency_spinbox.setSuffix(" kHz")
        form_layout.addRow("Frequency:", self.frequency_spinbox)
        
        # Latitude
        self.latitude_spinbox = QDoubleSpinBox()
        self.latitude_spinbox.setRange(-90.0, 90.0)
        self.latitude_spinbox.setDecimals(6)
        self.latitude_spinbox.setSuffix("°")
        form_layout. addRow("Latitude:", self. latitude_spinbox)
        
        # Longitude
        self. longitude_spinbox = QDoubleSpinBox()
        self. longitude_spinbox.setRange(-180.0, 180.0)
        self.longitude_spinbox.setDecimals(6)
        self.longitude_spinbox.setSuffix("°")
        form_layout.addRow("Longitude:", self.longitude_spinbox)
        
        # Country
        self.country_edit = QLineEdit()
        self. country_edit.setPlaceholderText("e.g., USA")
        form_layout.addRow("Country:", self.country_edit)
        
        # Power
        self.power_edit = QLineEdit()
        self.power_edit.setPlaceholderText("e.g., 1000kW")
        form_layout. addRow("Power:", self.power_edit)
        
        # Callsign
        self.callsign_edit = QLineEdit()
        self.callsign_edit.setPlaceholderText("e.g., NAA")
        form_layout. addRow("Callsign:", self.callsign_edit)
        
        # Notes
        self.notes_edit = QTextEdit()
        self. notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Additional notes about the station...")
        form_layout.addRow("Notes:", self.notes_edit)
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Station Enabled")
        self.enabled_checkbox.setChecked(True)
        form_layout.addRow("", self.enabled_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self. save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self. cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLineEdit, QDoubleSpinBox, QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
    
    def load_station_data(self):
        """Load station data into form"""
        self.code_edit.setText(self.station.code)
        self.name_edit.setText(self.station.name)
        self.frequency_spinbox.setValue(self.station.frequency)
        self.latitude_spinbox.setValue(self.station.latitude)
        self.longitude_spinbox. setValue(self.station.longitude)
        self.country_edit. setText(self.station.country)
        self.power_edit. setText(self.station.power)
        self.callsign_edit.setText(self.station. callsign)
        self. notes_edit.setPlainText(self.station. notes)
        self.enabled_checkbox.setChecked(self. station.enabled)
    
    def get_station_data(self) -> VLFStation:
        """Get station data from form"""
        return VLFStation(
            code=self.code_edit. text(). strip(). upper(),
            name=self. name_edit.text().strip(),
            frequency=self.frequency_spinbox.value(),
            latitude=self.latitude_spinbox.value(),
            longitude=self.longitude_spinbox. value(),
            country=self. country_edit.text().strip(),
            power=self.power_edit.text().strip(),
            callsign=self.callsign_edit.text().strip(). upper(),
            notes=self. notes_edit.toPlainText().strip(),
            enabled=self.enabled_checkbox.isChecked()
        )

class StationsWidget(QGroupBox):
    """Widget for managing VLF stations"""
    
    # Signals
    station_selection_changed = pyqtSignal(list)  # List of enabled station codes
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__("VLF Stations", parent)
        
        self.config_manager = config_manager
        self. logger = get_logger(__name__)
        
        # Station items mapping
        self.station_items: dict[str, StationItem] = {}
        
        self.setup_ui()
        self.load_stations()
    
    def setup_ui(self):
        """Setup the widget UI"""
        self.setMaximumWidth(380)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Station count label
        self.station_count_label = QLabel("0 stations")
        self.station_count_label.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        header_layout.addWidget(self.station_count_label)
        
        header_layout.addStretch()
        
        # Add station button
        self.add_button = QPushButton("Add Station")
        self.add_button. setIcon(QIcon("assets/icons/add.png"))
        self.add_button.clicked.connect(self.add_station)
        header_layout.addWidget(self.add_button)
        
        # Import button
        self.import_button = QPushButton("Import")
        self.import_button. setIcon(QIcon("assets/icons/import.png"))
        self.import_button.clicked. connect(self.import_stations)
        header_layout.addWidget(self.import_button)
        
        layout.addLayout(header_layout)
        
        # Stations list
        self.stations_list = QListWidget()
        self.stations_list.setAlternatingRowColors(True)
        self.stations_list.setSelectionMode(QListWidget. SelectionMode.SingleSelection)
        layout.addWidget(self.stations_list)
        
        # Footer with selection info
        footer_layout = QHBoxLayout()
        
        self.enabled_count_label = QLabel("0 enabled")
        self.enabled_count_label.setStyleSheet("color: #00ff00; font-size: 11px; font-weight: bold;")
        footer_layout.addWidget(self.enabled_count_label)
        
        footer_layout.addStretch()
        
        # Quick actions
        self.enable_all_button = QPushButton("Enable All")
        self.enable_all_button.clicked.connect(self.enable_all_stations)
        footer_layout.addWidget(self.enable_all_button)
        
        self.disable_all_button = QPushButton("Disable All")
        self.disable_all_button.clicked.connect(self. disable_all_stations)
        footer_layout.addWidget(self.disable_all_button)
        
        layout.addLayout(footer_layout)
        
        # Apply styling
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
            
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
                selection-background-color: #0078d4;
            }
            
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            
            QPushButton:hover {
                background-color: #0078d4;
            }
        """)
    
    def load_stations(self):
        """Load stations from configuration"""
        stations = self.config_manager.get_vlf_stations()
        
        self.stations_list.clear()
        self.station_items.clear()
        
        for station in stations:
            self.add_station_item(station)
        
        self.update_counts()
        self.update_selection()
    
    def add_station_item(self, station: VLFStation):
        """Add a station item to the list"""
        # Create station item widget
        station_item = StationItem(station)
        station_item.toggled.connect(self.on_station_toggled)
        station_item.edit_requested.connect(self.edit_station)
        station_item.remove_requested.connect(self.remove_station)
        
        # Create list widget item
        list_item = QListWidgetItem()
        list_item.setSizeHint(station_item.sizeHint())
        
        # Add to list
        self.stations_list. addItem(list_item)
        self.stations_list.setItemWidget(list_item, station_item)
        
        # Store reference
        self.station_items[station.code] = station_item
    
    def add_station(self):
        """Add a new station"""
        dialog = StationEditDialog(parent=self)
        if dialog. exec() == QDialog.DialogCode. Accepted:
            station = dialog. get_station_data()
            
            # Validate station
            if not station.code:
                QMessageBox.warning(self, "Invalid Station", "Station code is required.")
                return
            
            if station.code in self.station_items:
                QMessageBox.warning(self, "Duplicate Station", f"Station {station.code} already exists.")
                return
            
            # Add to configuration
            if self.config_manager.add_vlf_station(station):
                self.add_station_item(station)
                self.update_counts()
                self.update_selection()
                self.logger.info(f"Added VLF station: {station.code}")
            else:
                QMessageBox. critical(self, "Error", f"Failed to add station {station.code}.")
    
    def edit_station(self, station_code: str):
        """Edit an existing station"""
        stations = self.config_manager.get_vlf_stations()
        station = next((s for s in stations if s.code == station_code), None)
        
        if station:
            dialog = StationEditDialog(station, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_station = dialog.get_station_data()
                
                # Remove old station
                self.config_manager.remove_vlf_station(station_code)
                
                # Add updated station
                if self.config_manager.add_vlf_station(updated_station):
                    self.load_stations()  # Reload all stations
                    self.logger.info(f"Updated VLF station: {station_code}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to update station {station_code}.")
    
    def remove_station(self, station_code: str):
        """Remove a station"""
        reply = QMessageBox.question(
            self,
            "Remove Station",
            f"Remove station {station_code}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.config_manager.remove_vlf_station(station_code):
                # Remove from UI
                if station_code in self.station_items:
                    # Find and remove the list item
                    for i in range(self.stations_list.count()):
                        item = self.stations_list.item(i)
                        widget = self.stations_list.itemWidget(item)
                        if isinstance(widget, StationItem) and widget.station.code == station_code:
                            self.stations_list. takeItem(i)
                            break
                    
                    del self.station_items[station_code]
                
                self.update_counts()
                self.update_selection()
                self.logger.info(f"Removed VLF station: {station_code}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to remove station {station_code}.")
    
    def on_station_toggled(self, station_code: str, enabled: bool):
        """Handle station enable/disable"""
        # Update configuration
        stations = self.config_manager.get_vlf_stations()
        for station in stations:
            if station.code == station_code:
                station.enabled = enabled
                break
        
        # Save configuration
        self.config_manager.set('vlf_stations. default_stations', [station.__dict__ for station in stations])
        self.config_manager.save_config()
        
        self.update_counts()
        self.update_selection()
        self.logger.info(f"Station {station_code} {'enabled' if enabled else 'disabled'}")
    
    def enable_all_stations(self):
        """Enable all stations"""
        for station_item in self.station_items.values():
            if not station_item.enabled_checkbox.isChecked():
                station_item.enabled_checkbox. setChecked(True)
    
    def disable_all_stations(self):
        """Disable all stations"""
        for station_item in self.station_items. values():
            if station_item.enabled_checkbox.isChecked():
                station_item.enabled_checkbox.setChecked(False)
    
    def update_counts(self):
        """Update station count displays"""
        total_count = len(self.station_items)
        enabled_count = sum(1 for item in self.station_items.values() if item.station.enabled)
        
        self.station_count_label.setText(f"{total_count} stations")
        self.enabled_count_label.setText(f"{enabled_count} enabled")
    
    def update_selection(self):
        """Update and emit current selection"""
        enabled_stations = [
            item.station. code for item in self.station_items.values() 
            if item.station. enabled
        ]
        
        self.station_selection_changed.emit(enabled_stations)
    
    def import_stations(self):
        """Import stations from KML files"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import VLF Stations",
            "",
            "KML Files (*.kml);;All Files (*)"
        )
        
        if file_path:
            try:
                self.import_stations_from_kml(file_path)
            except Exception as e:
                self.logger.error(f"Error importing stations: {e}")
                QMessageBox.critical(self, "Import Error", f"Failed to import stations:\n{str(e)}")
    
    def import_stations_from_kml(self, file_path: str):
        """Import stations from KML file"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Parse KML namespace
            namespace = {'kml': 'http://earth.google.com/kml/2.2'}
            
            imported_count = 0
            
            # Find all Placemark elements
            for placemark in root.findall('. //kml:Placemark', namespace):
                name_elem = placemark.find('kml:name', namespace)
                desc_elem = placemark.find('kml:description', namespace)
                coord_elem = placemark.find('. //kml:coordinates', namespace)
                
                if name_elem is not None and coord_elem is not None:
                    name = name_elem.text.strip()
                    coordinates = coord_elem.text.strip()
                    
                    # Parse coordinates (longitude, latitude, elevation)
                    try:
                        coords = coordinates.split(',')
                        longitude = float(coords[0])
                        latitude = float(coords[1])
                    except (ValueError, IndexError):
                        continue
                    
                    # Extract frequency from description if available
                    frequency = 20.0  # Default frequency
                    power = ""
                    country = ""
                    
                    if desc_elem is not None and desc_elem.text:
                        desc = desc_elem.text
                        # Try to extract frequency (look for patterns like "24. 0kHz" or "24.0 kHz")
                        import re
                        freq_match = re.search(r'(\d+\.?\d*)\s*kHz', desc)
                        if freq_match:
                            frequency = float(freq_match.group(1))
                        
                        # Extract country/location info
                        lines = desc.split('<br/>')
                        if len(lines) > 1:
                            country = lines[-1].strip()
                    
                    # Create station
                    station = VLFStation(
                        code=name,
                        name=name,
                        frequency=frequency,
                        latitude=latitude,
                        longitude=longitude,
                        enabled=False,  # Import as disabled by default
                        power=power,
                        country=country,
                        callsign=name,
                        notes=f"Imported from {file_path}"
                    )
                    
                    # Add if not duplicate
                    if station.code not in self.station_items:
                        if self.config_manager.add_vlf_station(station):
                            imported_count += 1
            
            # Reload stations
            if imported_count > 0:
                self.load_stations()
                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Successfully imported {imported_count} stations."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Import Complete", 
                    "No new stations were imported."
                )
            
        except ET.ParseError as e:
            raise Exception(f"Invalid KML file: {e}")
        except Exception as e:
            raise Exception(f"Error parsing KML: {e}")