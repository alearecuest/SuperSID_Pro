"""
VLF Station Database Management Widget for SuperSID Pro - COMPLETE VERSION
Advanced interface for managing worldwide VLF transmitter database
"""

import sqlite3
from typing import Optional, List, Dict
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QLabel, QFrame, QTabWidget, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSortFilterProxyModel
from PyQt6.QtGui import QFont, QColor, QIcon

from core.config_manager import ConfigManager
from core. logger import get_logger, log_exception
from data.vlf_database import VLFDatabase, VLFStationExtended

class KMLImportWorker(QThread):
    """Worker thread for KML import operations"""
    
    progress = pyqtSignal(int, str)  # percentage, message
    finished = pyqtSignal(int, str)  # imported_count, message
    error = pyqtSignal(str)
    
    def __init__(self, database: VLFDatabase, kml_files: List[str]):
        super().__init__()
        self.database = database
        self.kml_files = kml_files
    
    def run(self):
        """Run KML import in background"""
        total_imported = 0
        
        try:
            for i, kml_file in enumerate(self.kml_files):
                self.progress.emit(
                    int((i / len(self.kml_files)) * 100),
                    f"Importing {kml_file}..."
                )
                
                imported = self.database.import_from_kml(kml_file)
                total_imported += imported
                
                self.progress.emit(
                    int(((i + 1) / len(self.kml_files)) * 100),
                    f"Imported {imported} stations from {kml_file}"
                )
            
            self.finished.emit(total_imported, f"Successfully imported {total_imported} stations")
            
        except Exception as e:
            self.error.emit(str(e))

class StationTableWidget(QTableWidget):
    """Enhanced table widget for VLF stations"""
    
    station_selected = pyqtSignal(object)  # VLFStationExtended
    station_toggled = pyqtSignal(str, bool)  # code, enabled
    
    def __init__(self):
        super().__init__()
        
        self.stations: List[VLFStationExtended] = []
        self.setup_table()
    
    def setup_table(self):
        """Setup table headers and properties"""
        headers = [
            "Code", "Name", "Frequency (kHz)", "Country", "Distance (km)",
            "Power", "Azimuth (°)", "Priority", "Enabled", "Status", "Notes"
        ]
        
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        
        # Configure column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Code
        header.resizeSection(0, 80)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Frequency
        header.resizeSection(2, 100)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Country
        header.resizeSection(3, 100)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Distance
        header.resizeSection(4, 100)
        
        # Connect signals
        self.cellClicked.connect(self.on_cell_clicked)
        self.cellDoubleClicked.connect(self. on_cell_double_clicked)
        
        # Style
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #404040;
                background-color: #2d2d2d;
                alternate-background-color: #3a3a3a;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
        """)
    
    def update_stations(self, stations: List[VLFStationExtended]):
        """Update table with station data"""
        self.stations = stations
        self.setRowCount(len(stations))
        
        for row, station in enumerate(stations):
            # Code
            self.setItem(row, 0, QTableWidgetItem(station.code))
            
            # Name
            self.setItem(row, 1, QTableWidgetItem(station.name))
            
            # Frequency
            freq_item = QTableWidgetItem(f"{station.frequency:.1f}")
            freq_item.setData(Qt.ItemDataRole.UserRole, station.frequency)
            self.setItem(row, 2, freq_item)
            
            # Country
            self. setItem(row, 3, QTableWidgetItem(station. country))
            
            # Distance
            if station.distance_km:
                distance_text = f"{station.distance_km:.0f}"
                distance_item = QTableWidgetItem(distance_text)
                distance_item.setData(Qt.ItemDataRole.UserRole, station.distance_km)
            else:
                distance_item = QTableWidgetItem("Unknown")
                distance_item.setData(Qt.ItemDataRole.UserRole, float('inf'))
            self.setItem(row, 4, distance_item)
            
            # Power
            self.setItem(row, 5, QTableWidgetItem(station.power))
            
            # Azimuth
            if station.azimuth:
                azimuth_text = f"{station.azimuth:. 0f}"
                azimuth_item = QTableWidgetItem(azimuth_text)
                azimuth_item.setData(Qt.ItemDataRole.UserRole, station.azimuth)
            else:
                azimuth_item = QTableWidgetItem("")
                azimuth_item. setData(Qt.ItemDataRole.UserRole, 0)
            self.setItem(row, 6, azimuth_item)
            
            # Priority
            priority_item = QTableWidgetItem(str(station.priority))
            priority_item.setData(Qt.ItemDataRole.UserRole, station.priority)
            self.setItem(row, 7, priority_item)
            
            # Enabled checkbox
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            enabled_item.setCheckState(Qt.CheckState.Checked if station.enabled else Qt.CheckState.Unchecked)
            self.setItem(row, 8, enabled_item)
            
            # Status
            status_item = QTableWidgetItem(station.operational_status. title())
            if station.operational_status == "active":
                status_item.setBackground(QColor("#2d5a27"))
            elif station.operational_status == "inactive":
                status_item.setBackground(QColor("#5a272d"))
            else:
                status_item.setBackground(QColor("#5a5527"))
            self.setItem(row, 9, status_item)
            
            # Notes (truncated)
            notes_text = station.notes[:50] + "..." if len(station.notes) > 50 else station.notes
            self.setItem(row, 10, QTableWidgetItem(notes_text))
    
    def on_cell_clicked(self, row: int, column: int):
        """Handle cell click"""
        if 0 <= row < len(self.stations):
            station = self.stations[row]
            
            # Handle enabled checkbox
            if column == 8:  # Enabled column
                item = self.item(row, column)
                if item:
                    enabled = item.checkState() == Qt.CheckState.Checked
                    self.station_toggled. emit(station.code, enabled)
            
            self.station_selected.emit(station)
    
    def on_cell_double_clicked(self, row: int, column: int):
        """Handle cell double click"""
        if 0 <= row < len(self.stations):
            station = self.stations[row]
            # Could open detailed station editor here
            print(f"Double clicked station: {station.code}")

class VLFDatabaseWidget(QWidget):
    """Main VLF database management widget"""
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Initialize database
        self.database = VLFDatabase(config_manager)
        
        # Current stations
        self.current_stations: List[VLFStationExtended] = []
        
        self.setup_ui()
        self.load_stations()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Main database tab
        main_tab = self.create_main_tab()
        tab_widget.addTab(main_tab, "Station Database")
        
        # Import/Export tab
        import_tab = self.create_import_tab()
        tab_widget.addTab(import_tab, "Import/Export")
        
        # Recommendations tab
        recommendations_tab = self.create_recommendations_tab()
        tab_widget.addTab(recommendations_tab, "Recommendations")
        
        # Statistics tab
        stats_tab = self.create_statistics_tab()
        tab_widget.addTab(stats_tab, "Statistics")
        
        layout.addWidget(tab_widget)
    
    def create_main_tab(self) -> QWidget:
        """Create main database management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filters section
        filters_group = QGroupBox("Filters")
        filters_layout = QGridLayout(filters_group)
        
        # Frequency range
        filters_layout.addWidget(QLabel("Frequency Range (kHz):"), 0, 0)
        self.freq_min_spin = QDoubleSpinBox()
        self.freq_min_spin.setRange(0, 1000)
        self.freq_min_spin.setValue(10)
        self.freq_min_spin.setSuffix(" kHz")
        filters_layout.addWidget(self.freq_min_spin, 0, 1)
        
        filters_layout.addWidget(QLabel("to"), 0, 2)
        self.freq_max_spin = QDoubleSpinBox()
        self.freq_max_spin.setRange(0, 1000)
        self.freq_max_spin.setValue(50)
        self.freq_max_spin.setSuffix(" kHz")
        filters_layout. addWidget(self.freq_max_spin, 0, 3)
        
        # Distance filter
        filters_layout.addWidget(QLabel("Max Distance (km):"), 1, 0)
        self.distance_spin = QSpinBox()
        self.distance_spin.setRange(0, 20000)
        self.distance_spin.setValue(10000)
        self.distance_spin.setSpecialValueText("Any")
        self.distance_spin.setSuffix(" km")
        filters_layout.addWidget(self.distance_spin, 1, 1)
        
        # Country filter
        filters_layout.addWidget(QLabel("Country:"), 1, 2)
        self. country_combo = QComboBox()
        self.country_combo.addItem("All Countries")
        filters_layout.addWidget(self. country_combo, 1, 3)
        
        # Status filters
        self.active_only_check = QCheckBox("Active stations only")
        self.active_only_check.setChecked(True)
        filters_layout.addWidget(self. active_only_check, 2, 0, 1, 2)
        
        self.enabled_only_check = QCheckBox("Enabled stations only")
        filters_layout.addWidget(self. enabled_only_check, 2, 2, 1, 2)
        
        # Filter buttons
        filter_buttons_layout = QHBoxLayout()
        
        self.apply_filters_btn = QPushButton("Apply Filters")
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        filter_buttons_layout.addWidget(self.apply_filters_btn)
        
        self.clear_filters_btn = QPushButton("Clear Filters")
        self.clear_filters_btn.clicked.connect(self. clear_filters)
        filter_buttons_layout.addWidget(self.clear_filters_btn)
        
        filter_buttons_layout.addStretch()
        filters_layout.addLayout(filter_buttons_layout, 3, 0, 1, 4)
        
        layout.addWidget(filters_group)
        
        # Station table
        self.station_table = StationTableWidget()
        self.station_table.station_selected.connect(self.on_station_selected)
        self.station_table.station_toggled.connect(self.on_station_toggled)
        layout.addWidget(self.station_table)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.enable_selected_btn = QPushButton("Enable Selected")
        self.enable_selected_btn.clicked.connect(lambda: self.toggle_selected_stations(True))
        actions_layout.addWidget(self.enable_selected_btn)
        
        self.disable_selected_btn = QPushButton("Disable Selected")
        self. disable_selected_btn.clicked. connect(lambda: self.toggle_selected_stations(False))
        actions_layout.addWidget(self.disable_selected_btn)
        
        actions_layout.addStretch()
        
        self.sync_config_btn = QPushButton("Sync with Config")
        self.sync_config_btn.clicked.connect(self.sync_with_config)
        actions_layout.addWidget(self.sync_config_btn)
        
        layout.addLayout(actions_layout)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self. status_label)
        
        status_layout.addStretch()
        
        self.station_count_label = QLabel("0 stations")
        status_layout.addWidget(self.station_count_label)
        
        layout.addLayout(status_layout)
        
        return widget
    
    def create_import_tab(self) -> QWidget:
        """Create import/export tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Import section
        import_group = QGroupBox("Import KML Files")
        import_layout = QVBoxLayout(import_group)
        
        # File selection
        file_selection_layout = QHBoxLayout()
        
        self.kml_files_edit = QTextEdit()
        self.kml_files_edit.setMaximumHeight(100)
        self.kml_files_edit.setPlaceholderText("Select KML files to import...")
        file_selection_layout. addWidget(self.kml_files_edit)
        
        select_files_btn = QPushButton("Browse...")
        select_files_btn. clicked.connect(self.select_kml_files)
        file_selection_layout.addWidget(select_files_btn)
        
        import_layout.addLayout(file_selection_layout)
        
        # Import progress
        self.import_progress = QProgressBar()
        self.import_progress.setVisible(False)
        import_layout.addWidget(self.import_progress)
        
        # Import buttons
        import_buttons_layout = QHBoxLayout()
        
        self.start_import_btn = QPushButton("Start Import")
        self. start_import_btn.clicked. connect(self.start_import)
        import_buttons_layout. addWidget(self.start_import_btn)
        
        import_buttons_layout.addStretch()
        import_layout.addLayout(import_buttons_layout)
        
        layout.addWidget(import_group)
        
        # Export section
        export_group = QGroupBox("Export Database")
        export_layout = QVBoxLayout(export_group)
        
        export_buttons_layout = QHBoxLayout()
        
        export_csv_btn = QPushButton("Export to CSV")
        export_csv_btn.clicked.connect(self.export_to_csv)
        export_buttons_layout.addWidget(export_csv_btn)
        
        export_kml_btn = QPushButton("Export to KML")
        export_kml_btn.clicked. connect(self.export_to_kml)
        export_buttons_layout.addWidget(export_kml_btn)
        
        export_config_btn = QPushButton("Export to Config")
        export_config_btn.clicked.connect(self.export_to_config)
        export_buttons_layout.addWidget(export_config_btn)
        
        export_buttons_layout.addStretch()
        export_layout.addLayout(export_buttons_layout)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        return widget
    
    def create_recommendations_tab(self) -> QWidget:
        """Create recommendations tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Recommendations header
        recommendations_group = QGroupBox("Station Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        info_text = QLabel("""
        Based on your observatory location, here are the recommended VLF stations 
        for optimal monitoring.  Stations are ranked by distance, signal strength, 
        and reliability.
        """)
        info_text.setWordWrap(True)
        recommendations_layout. addWidget(info_text)
        
        # Get recommendations button
        get_recommendations_btn = QPushButton("Get Recommendations")
        get_recommendations_btn. clicked.connect(self.get_recommendations)
        recommendations_layout. addWidget(get_recommendations_btn)
        
        # Recommendations table (smaller version)
        self.recommendations_table = StationTableWidget()
        self. recommendations_table.setMaximumHeight(300)
        recommendations_layout.addWidget(self.recommendations_table)
        
        # Quick enable buttons
        quick_actions_layout = QHBoxLayout()
        
        enable_top5_btn = QPushButton("Enable Top 5")
        enable_top5_btn.clicked.connect(lambda: self.enable_top_recommendations(5))
        quick_actions_layout.addWidget(enable_top5_btn)
        
        enable_top10_btn = QPushButton("Enable Top 10")
        enable_top10_btn.clicked.connect(lambda: self.enable_top_recommendations(10))
        quick_actions_layout.addWidget(enable_top10_btn)
        
        quick_actions_layout.addStretch()
        recommendations_layout.addLayout(quick_actions_layout)
        
        layout.addWidget(recommendations_group)
        layout.addStretch()
        
        return widget
    
    def create_statistics_tab(self) -> QWidget:
        """Create statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Database info
        info_group = QGroupBox("Database Information")
        info_layout = QGridLayout(info_group)
        
        self.total_stations_label = QLabel("0")
        info_layout.addWidget(QLabel("Total Stations:"), 0, 0)
        info_layout.addWidget(self. total_stations_label, 0, 1)
        
        self.active_stations_label = QLabel("0")
        info_layout. addWidget(QLabel("Active Stations:"), 1, 0)
        info_layout.addWidget(self.active_stations_label, 1, 1)
        
        self.countries_count_label = QLabel("0")
        info_layout.addWidget(QLabel("Countries:"), 2, 0)
        info_layout.addWidget(self. countries_count_label, 2, 1)
        
        self.frequency_range_label = QLabel("0 - 0 kHz")
        info_layout.addWidget(QLabel("Frequency Range:"), 3, 0)
        info_layout.addWidget(self.frequency_range_label, 3, 1)
        
        self. last_updated_label = QLabel("Never")
        info_layout.addWidget(QLabel("Last Updated:"), 4, 0)
        info_layout.addWidget(self.last_updated_label, 4, 1)
        
        layout.addWidget(info_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_statistics)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        return widget
    
    # METHODS IMPLEMENTATION
    
    def load_stations(self):
        """Load all stations from database"""
        try:
            self.current_stations = self.database.get_all_stations()
            self.station_table.update_stations(self.current_stations)
            self.update_country_filter()
            self.update_status()
            
            self.logger.info(f"Loaded {len(self.current_stations)} stations")
            
        except Exception as e:
            log_exception(e, "Loading VLF stations")
            QMessageBox.critical(self, "Error", f"Failed to load stations: {e}")
    
    def apply_filters(self):
        """Apply current filters to station list"""
        try:
            # Get filter values
            freq_min = self.freq_min_spin.value() if self.freq_min_spin. value() > 0 else None
            freq_max = self. freq_max_spin.value() if self.freq_max_spin.value() < 1000 else None
            max_distance = self.distance_spin.value() if self.distance_spin. value() > 0 else None
            
            countries = None
            if self.country_combo.currentText() != "All Countries":
                countries = [self.country_combo.currentText()]
            
            operational_only = self.active_only_check.isChecked()
            enabled_only = self.enabled_only_check.isChecked()
            
            # Apply filters
            filtered_stations = self.database.filter_stations(
                frequency_min=freq_min,
                frequency_max=freq_max,
                max_distance_km=max_distance,
                countries=countries,
                operational_only=operational_only,
                enabled_only=enabled_only
            )
            
            self.current_stations = filtered_stations
            self.station_table.update_stations(filtered_stations)
            self.update_status()
            
            self.logger.info(f"Applied filters, showing {len(filtered_stations)} stations")
            
        except Exception as e:
            log_exception(e, "Applying station filters")
            QMessageBox. warning(self, "Filter Error", f"Failed to apply filters: {e}")
    
    def clear_filters(self):
        """Clear all filters and show all stations"""
        self.freq_min_spin.setValue(0)
        self.freq_max_spin.setValue(1000)
        self.distance_spin. setValue(0)
        self.country_combo.setCurrentText("All Countries")
        self.active_only_check.setChecked(False)
        self.enabled_only_check.setChecked(False)
        
        self.load_stations()
    
    def update_country_filter(self):
        """Update country filter dropdown"""
        try:
            db_info = self.database.get_database_info()
            self.country_combo.clear()
            self.country_combo.addItem("All Countries")
            
            if db_info. countries:
                for country in db_info.countries:
                    self.country_combo.addItem(country)
                    
        except Exception as e:
            log_exception(e, "Updating country filter")
    
    def update_status(self):
        """Update status information"""
        count = len(self.current_stations)
        enabled_count = sum(1 for s in self.current_stations if s.enabled)
        
        self.station_count_label.setText(f"{count} stations ({enabled_count} enabled)")
        self.status_label.setText("Ready")
    
    def on_station_selected(self, station: VLFStationExtended):
        """Handle station selection"""
        info_text = f"Selected: {station.code} - {station.name}"
        if station.distance_km:
            info_text += f" ({station.distance_km:. 0f} km)"
        
        self.status_label.setText(info_text)
    
    def on_station_toggled(self, code: str, enabled: bool):
        """Handle station enabled/disabled toggle"""
        try:
            # Update in database
            with sqlite3.connect(self.database. db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE vlf_stations SET enabled=? WHERE code=?", (enabled, code))
                conn.commit()
            
            # Update current data
            for station in self.current_stations:
                if station.code == code:
                    station.enabled = enabled
                    break
            
            self.update_status()
            
            action = "enabled" if enabled else "disabled"
            self.logger. info(f"Station {code} {action}")
            
        except Exception as e:
            log_exception(e, f"Toggling station {code}")
            QMessageBox. warning(self, "Error", f"Failed to update station: {e}")
    
    def toggle_selected_stations(self, enabled: bool):
        """Enable or disable selected stations"""
        try:
            selected_rows = set()
            for item in self.station_table.selectedItems():
                selected_rows. add(item.row())
            
            if not selected_rows:
                QMessageBox.information(self, "No Selection", "Please select stations to modify")
                return
            
            # Update database
            codes_to_update = []
            for row in selected_rows:
                if row < len(self.current_stations):
                    station = self.current_stations[row]
                    codes_to_update.append(station.code)
                    station.enabled = enabled
            
            if codes_to_update:
                with sqlite3.connect(self. database.db_path) as conn:
                    cursor = conn. cursor()
                    placeholders = ",".join(["?" for _ in codes_to_update])
                    cursor.execute(f"UPDATE vlf_stations SET enabled=? WHERE code IN ({placeholders})", 
                                 [enabled] + codes_to_update)
                    conn.commit()
                
                # Refresh table
                self.station_table.update_stations(self. current_stations)
                self. update_status()
                
                action = "enabled" if enabled else "disabled"
                self.logger. info(f"{action} {len(codes_to_update)} selected stations")
            
        except Exception as e:
            log_exception(e, "Toggling selected stations")
            QMessageBox.warning(self, "Error", f"Failed to update stations: {e}")
    
    def sync_with_config(self):
        """Synchronize enabled stations with config manager"""
        try:
            self.database.sync_with_config_manager()
            QMessageBox.information(self, "Sync Complete", "Enabled stations synchronized with configuration")
            
        except Exception as e:
            log_exception(e, "Synchronizing with config")
            QMessageBox.critical(self, "Sync Error", f"Failed to sync with config: {e}")
    
    def select_kml_files(self):
        """Select KML files for import"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select KML Files", "", "KML Files (*.kml);;All Files (*)"
        )
        
        if files:
            self.kml_files_edit.setPlainText("\n".join(files))
    
    def start_import(self):
        """Start KML import process"""
        kml_text = self.kml_files_edit.toPlainText(). strip()
        if not kml_text:
            QMessageBox.warning(self, "No Files", "Please select KML files to import")
            return
        
        kml_files = [f.strip() for f in kml_text.split('\n') if f. strip()]
        
        # Verify files exist
        missing_files = [f for f in kml_files if not Path(f).exists()]
        if missing_files:
            QMessageBox.critical(self, "Files Not Found", 
                               f"The following files were not found:\n" + "\n".join(missing_files))
            return
        
        # Start import worker
        self.import_worker = KMLImportWorker(self.database, kml_files)
        self.import_worker.progress.connect(self.on_import_progress)
        self.import_worker.finished.connect(self.on_import_finished)
        self.import_worker.error.connect(self.on_import_error)
        
        # Show progress and disable buttons
        self.import_progress.setVisible(True)
        self.start_import_btn. setEnabled(False)
        
        self.import_worker.start()
    
    def on_import_progress(self, percentage: int, message: str):
        """Handle import progress update"""
        self. import_progress.setValue(percentage)
        self.status_label. setText(message)
    
    def on_import_finished(self, imported_count: int, message: str):
        """Handle import completion"""
        self.import_progress.setVisible(False)
        self. start_import_btn.setEnabled(True)
        
        QMessageBox.information(self, "Import Complete", message)
        
        # Refresh stations
        self.load_stations()
        self.refresh_statistics()
    
    def on_import_error(self, error_message: str):
        """Handle import error"""
        self.import_progress.setVisible(False)
        self.start_import_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Import Error", f"Import failed: {error_message}")
    
    def get_recommendations(self):
        """Get station recommendations"""
        try:
            recommended = self.database.get_recommended_stations(max_stations=20)
            self.recommendations_table.update_stations(recommended)
            
            if not recommended:
                QMessageBox.information(self, "No Recommendations", 
                                      "No recommendations available.  Please set your observatory location.")
            else:
                self.status_label.setText(f"Found {len(recommended)} recommended stations")
                
        except Exception as e:
            log_exception(e, "Getting station recommendations")
            QMessageBox. warning(self, "Recommendation Error", f"Failed to get recommendations: {e}")
    
    def enable_top_recommendations(self, count: int):
        """Enable top N recommended stations"""
        try:
            recommended = self.database.get_recommended_stations(max_stations=count)
            
            if not recommended:
                QMessageBox.information(self, "No Recommendations", "No recommendations available")
                return
            
            # Enable stations in database
            codes_to_enable = [station.code for station in recommended]
            
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn. cursor()
                placeholders = ",".join(["?" for _ in codes_to_enable])
                cursor.execute(f"UPDATE vlf_stations SET enabled=1 WHERE code IN ({placeholders})", 
                             codes_to_enable)
                conn.commit()
            
            # Refresh displays
            self.load_stations()
            self.get_recommendations()
            
            QMessageBox.information(self, "Stations Enabled", 
                                  f"Enabled top {len(recommended)} recommended stations")
            
        except Exception as e:
            log_exception(e, f"Enabling top {count} recommendations")
            QMessageBox.warning(self, "Error", f"Failed to enable recommendations: {e}")
    
    def refresh_statistics(self):
        """Refresh database statistics"""
        try:
            db_info = self.database.get_database_info()
            
            self.total_stations_label.setText(str(db_info.total_stations))
            self.active_stations_label.setText(str(db_info.active_stations))
            self.countries_count_label.setText(str(len(db_info.countries or [])))
            
            if db_info.frequency_range:
                freq_min, freq_max = db_info. frequency_range
                self.frequency_range_label.setText(f"{freq_min:. 1f} - {freq_max:. 1f} kHz")
            
            if db_info.last_updated:
                from datetime import datetime
                try:
                    update_time = datetime.fromisoformat(db_info.last_updated)
                    self.last_updated_label.setText(update_time.strftime("%Y-%m-%d %H:%M"))
                except:
                    self.last_updated_label.setText(db_info.last_updated)
            else:
                self.last_updated_label.setText("Never")
                
        except Exception as e:
            log_exception(e, "Refreshing statistics")
    
    def export_to_csv(self):
        """Export stations to CSV file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export to CSV", "vlf_stations.csv", "CSV Files (*.csv)"
            )
            
            if filename:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Header
                    writer.writerow([
                        "Code", "Name", "Frequency", "Latitude", "Longitude", "Country",
                        "Power", "Distance_km", "Azimuth", "Status", "Enabled", "Notes"
                    ])
                    
                    # Data
                    for station in self.current_stations:
                        writer. writerow([
                            station. code, station.name, station. frequency,
                            station.latitude, station.longitude, station.country,
                            station.power, station.distance_km or "",
                            station.azimuth or "", station.operational_status,
                            station.enabled, station. notes
                        ])
                
                QMessageBox.information(self, "Export Complete", f"Exported {len(self. current_stations)} stations to {filename}")
                
        except Exception as e:
            log_exception(e, "Exporting to CSV")
            QMessageBox. critical(self, "Export Error", f"Failed to export CSV: {e}")
    
    def export_to_kml(self):
        """Export stations to KML file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export to KML", "vlf_stations.kml", "KML Files (*.kml)"
            )
            
            if filename:
                # Create KML content
                kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
<name>VLF Stations</name>
<description>VLF transmitter stations exported from SuperSID Pro</description>
'''
                
                for station in self.current_stations:
                    description = f"""
Frequency: {station.frequency} kHz
Power: {station.power}
Country: {station.country}
Status: {station.operational_status}
Notes: {station.notes}
""". strip()
                    
                    kml_content += f'''
<Placemark>
<name>{station.code} - {station.name}</name>
<description>{description}</description>
<Point>
<coordinates>{station.longitude},{station.latitude}</coordinates>
</Point>
</Placemark>
'''
                
                kml_content += '''
</Document>
</kml>'''
                
                with open(filename, 'w', encoding='utf-8') as kml_file:
                    kml_file.write(kml_content)
                
                QMessageBox. information(self, "Export Complete", f"Exported {len(self.current_stations)} stations to {filename}")
                
        except Exception as e:
            log_exception(e, "Exporting to KML")
            QMessageBox.critical(self, "Export Error", f"Failed to export KML: {e}")
    
    def export_to_config(self):
        """Export enabled stations to config format"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Config", "vlf_config.json", "JSON Files (*. json)"
            )
            
            if filename:
                enabled_stations = [s for s in self.current_stations if s.enabled]
                
                config_data = {
                    "vlf_stations": {
                        "default_stations": []
                    }
                }
                
                for station in enabled_stations:
                    station_config = {
                        "code": station.code,
                        "name": station.name,
                        "frequency": station.frequency,
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                        "enabled": True,
                        "power": station.power,
                        "country": station.country,
                        "callsign": station.callsign,
                        "notes": station.notes[:100]  # Limit length
                    }
                    config_data["vlf_stations"]["default_stations"].append(station_config)
                
                import json
                with open(filename, 'w', encoding='utf-8') as config_file:
                    json. dump(config_data, config_file, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, "Export Complete", 
                                      f"Exported {len(enabled_stations)} enabled stations to {filename}")
                
        except Exception as e:
            log_exception(e, "Exporting to config")
            QMessageBox.critical(self, "Export Error", f"Failed to export config: {e}")