#!/usr/bin/env python3
"""
SuperSID Pro - Professional Solar Radio Telescope Monitoring Software
Main application entry point

Author: Observatory Software Solutions
License: Commercial
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys. path.insert(0, os. path.join(os.path. dirname(__file__), 'src'))

from gui.main_window import SuperSIDProApp
from core.config_manager import ConfigManager
from core. logger import setup_logger
from utils.system_check import SystemCheck

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='SuperSID Pro - Solar Observatory Monitoring')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', type=str, help='Configuration file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(debug=args.debug)
    
    # System check
    if not SystemCheck.verify_requirements():
        print("System requirements not met. Please check the documentation.")
        return 1
    
    # Initialize configuration
    config_file = args.config or 'config/default_config.json'
    config_manager = ConfigManager(config_file)
    
    # Start application
    app = SuperSIDProApp(config_manager, debug=args.debug)
    return app.run()

if __name__ == "__main__":
    sys.exit(main())