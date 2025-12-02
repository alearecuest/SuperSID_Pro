#!/usr/bin/env python3
"""
Integration patch for VLF Database into main_window.py
"""

def apply_integration():
    """Apply VLF Database integration to main_window.py"""
    
    file_path = 'src/gui/main_window.py'
    
    # Read current content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import for VLF Database Widget
    import_line = "from gui.widgets.space_weather_widget import SpaceWeatherWidget"
    new_import = "from gui.widgets.vlf_database_widget import VLFDatabaseWidget"
    
    if new_import not in content:
        content = content.replace(import_line, f"{import_line}\n{new_import}")
    
    # Add VLF Database widget to left panel (after stations, before space weather)
    old_left_panel = """        # Stations widget
        self. stations_widget = StationsWidget(self. config_manager)
        layout. addWidget(self.stations_widget)
        
        # Space weather widget"""
    
    new_left_panel = """        # Stations widget
        self.stations_widget = StationsWidget(self. config_manager)
        layout. addWidget(self.stations_widget)
        
        # VLF Database widget
        self.vlf_database_widget = VLFDatabaseWidget(self.config_manager)
        layout.addWidget(self. vlf_database_widget)
        
        # Space weather widget"""
    
    content = content.replace(old_left_panel, new_left_panel)
    
    # Add VLF Database tab to right panel
    old_right_panel = """        # Space weather details tab
        space_weather_detail = SpaceWeatherWidget(self.config_manager)
        tab_widget.addTab(space_weather_detail, "Space Weather")"""
    
    new_right_panel = """        # Space weather details tab
        space_weather_detail = SpaceWeatherWidget(self.config_manager)
        tab_widget.addTab(space_weather_detail, "Space Weather")
        
        # VLF Database management tab
        self.vlf_database_tab = VLFDatabaseWidget(self.config_manager)
        tab_widget.addTab(self.vlf_database_tab, "VLF Database")"""
    
    content = content.replace(old_right_panel, new_right_panel)
    
    # Write back the modified content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("VLF Database integration applied to main_window.py")

if __name__ == "__main__":
    apply_integration()