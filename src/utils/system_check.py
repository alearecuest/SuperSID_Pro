"""
System requirements checker for SuperSID Pro
Verifies all dependencies and system capabilities
"""

import sys
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import importlib.util
from dataclasses import dataclass

from core.logger import get_logger, log_exception

@dataclass
class SystemRequirement:
    """System requirement definition"""
    name: str
    description: str
    required: bool = True
    version_min: Optional[str] = None
    check_function: Optional[callable] = None

@dataclass
class CheckResult:
    """Result of a system check"""
    name: str
    passed: bool
    message: str
    details: Optional[str] = None
    version: Optional[str] = None

class SystemCheck:
    """System requirements checker"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self. results: List[CheckResult] = []
    
    @staticmethod
    def verify_requirements() -> bool:
        """Quick verification of essential requirements"""
        checker = SystemCheck()
        return checker.run_all_checks()
    
    def run_all_checks(self) -> bool:
        """Run all system checks"""
        self.results. clear()
        
        # Python version check
        self.check_python_version()
        
        # Required Python packages
        self.check_python_packages()
        
        # Audio system check
        self.check_audio_system()
        
        # GUI system check
        self.check_gui_system()
        
        # Network connectivity
        self.check_network()
        
        # File system permissions
        self.check_file_permissions()
        
        # Log results
        self._log_results()
        
        # Return True if all required checks passed
        failed_required = [r for r in self.results if not r.passed and 'required' in r.name. lower()]
        return len(failed_required) == 0
    
    def check_python_version(self) -> None:
        """Check Python version compatibility"""
        current_version = sys.version_info
        min_version = (3, 9)
        
        if current_version >= min_version:
            self.results.append(CheckResult(
                "Python Version (Required)",
                True,
                f"Python {current_version. major}.{current_version.minor}.{current_version.micro} ✓",
                f"Minimum required: {min_version[0]}.{min_version[1]}",
                f"{current_version.major}.{current_version.minor}.{current_version.micro}"
            ))
        else:
            self.results. append(CheckResult(
                "Python Version (Required)",
                False,
                f"Python version too old: {current_version.major}.{current_version.minor}",
                f"Minimum required: {min_version[0]}.{min_version[1]}",
                f"{current_version.major}.{current_version.minor}. {current_version.micro}"
            ))
    
    def check_python_packages(self) -> None:
        """Check required Python packages"""
        required_packages = [
            ("PyQt6", "PyQt6"),
            ("numpy", "numpy"),
            ("scipy", "scipy"),
            ("matplotlib", "matplotlib"),
            ("requests", "requests"),
            ("pandas", "pandas"),
        ]
        
        optional_packages = [
            ("pyaudio", "pyaudio"),
            ("sounddevice", "sounddevice"),
            ("plotly", "plotly"),
            ("dash", "dash"),
        ]
        
        # Check required packages
        for package_name, import_name in required_packages:
            self._check_package(package_name, import_name, required=True)
        
        # Check optional packages
        for package_name, import_name in optional_packages:
            self._check_package(package_name, import_name, required=False)
    
    def _check_package(self, package_name: str, import_name: str, required: bool = True) -> None:
        """Check if a specific package is available"""
        try:
            spec = importlib.util.find_spec(import_name)
            if spec is not None:
                # Try to get version
                version = "unknown"
                try:
                    module = importlib.import_module(import_name)
                    if hasattr(module, '__version__'):
                        version = module.__version__
                    elif hasattr(module, 'VERSION'):
                        version = str(module.VERSION)
                except:
                    pass
                
                status = "Required" if required else "Optional"
                self.results.append(CheckResult(
                    f"{package_name} ({status})",
                    True,
                    f"{package_name} available ✓",
                    f"Import name: {import_name}",
                    version
                ))
            else:
                status = "Required" if required else "Optional"
                self.results. append(CheckResult(
                    f"{package_name} ({status})",
                    False,
                    f"{package_name} not found ✗",
                    f"Install with: pip install {package_name}"
                ))
        except Exception as e:
            status = "Required" if required else "Optional"
            self.results. append(CheckResult(
                f"{package_name} ({status})",
                False,
                f"Error checking {package_name}: {str(e)}",
                f"Install with: pip install {package_name}"
            ))
    
    def check_audio_system(self) -> None:
        """Check audio system availability"""
        # Check for audio backends
        audio_available = False
        audio_details = []
        
        # Check PyAudio
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            device_count = pa.get_device_count()
            pa.terminate()
            audio_available = True
            audio_details.append(f"PyAudio: {device_count} devices found")
        except Exception as e:
            audio_details.append(f"PyAudio: Not available ({e})")
        
        # Check sounddevice
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            audio_available = True
            audio_details.append(f"Sounddevice: {len(devices)} devices found")
        except Exception as e:
            audio_details.append(f"Sounddevice: Not available ({e})")
        
        self.results.append(CheckResult(
            "Audio System (Optional)",
            audio_available,
            "Audio system available ✓" if audio_available else "No audio system found ✗",
            "; ".join(audio_details)
        ))
    
    def check_gui_system(self) -> None:
        """Check GUI system availability"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QCoreApplication
            
            # Test if we can create a QApplication
            app = QCoreApplication. instance()
            if app is None:
                test_app = QApplication([])
                gui_available = True
                test_app.quit()
                test_app = None
            else:
                gui_available = True
            
            self.results.append(CheckResult(
                "GUI System (Required)",
                True,
                "PyQt6 GUI system available ✓",
                f"Platform: {platform.system()}"
            ))
            
        except Exception as e:
            self.results.append(CheckResult(
                "GUI System (Required)",
                False,
                f"GUI system not available: {str(e)}",
                "PyQt6 GUI framework required"
            ))
    
    def check_network(self) -> None:
        """Check network connectivity"""
        try:
            import requests
            
            # Test connectivity to key services
            test_urls = [
                ("Google DNS", "https://8.8.8.8"),
                ("NOAA SWPC", "https://services.swpc.noaa.gov"),
                ("Space Weather Live", "https://www.spaceweatherlive.com")
            ]
            
            network_details = []
            any_success = False
            
            for name, url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        network_details. append(f"{name}: OK")
                        any_success = True
                    else:
                        network_details.append(f"{name}: HTTP {response.status_code}")
                except requests.RequestException:
                    network_details.append(f"{name}: Failed")
            
            self.results.append(CheckResult(
                "Network Connectivity (Optional)",
                any_success,
                "Network connectivity available ✓" if any_success else "Network issues detected ✗",
                "; ". join(network_details)
            ))
            
        except ImportError:
            self.results. append(CheckResult(
                "Network Connectivity (Optional)",
                False,
                "Cannot test network (requests not available)",
                "Install requests package for network features"
            ))
    
    def check_file_permissions(self) -> None:
        """Check file system permissions"""
        test_directories = [
            Path("data"),
            Path("data/logs"),
            Path("data/exports"),
            Path("data/cache"),
            Path("config")
        ]
        
        permission_details = []
        all_permissions_ok = True
        
        for directory in test_directories:
            try:
                # Create directory if it doesn't exist
                directory.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = directory / ". permission_test"
                test_file.write_text("test")
                test_file.unlink()
                
                permission_details.append(f"{directory}: OK")
                
            except Exception as e:
                permission_details. append(f"{directory}: Failed ({e})")
                all_permissions_ok = False
        
        self.results.append(CheckResult(
            "File Permissions (Required)",
            all_permissions_ok,
            "File permissions OK ✓" if all_permissions_ok else "File permission issues ✗",
            "; ". join(permission_details)
        ))
    
    def _log_results(self) -> None:
        """Log all check results"""
        self.logger.info("=== System Requirements Check ===")
        
        for result in self.results:
            if result.passed:
                self. logger.info(f"✓ {result.name}: {result.message}")
            else:
                self.logger.warning(f"✗ {result.name}: {result.message}")
            
            if result.details:
                self.logger.debug(f"  Details: {result.details}")
            if result.version:
                self. logger.debug(f"  Version: {result.version}")
        
        failed_count = len([r for r in self.results if not r.passed])
        total_count = len(self.results)
        
        self.logger.info(f"System Check Complete: {total_count - failed_count}/{total_count} checks passed")
        
        if failed_count > 0:
            self.logger. warning(f"{failed_count} checks failed - see details above")
    
    def get_system_info(self) -> Dict[str, str]:
        """Get comprehensive system information"""
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        }
        
        # Add memory info if available
        try:
            import psutil
            memory = psutil.virtual_memory()
            info["total_memory_gb"] = f"{memory.total / (1024**3):.1f}"
            info["available_memory_gb"] = f"{memory.available / (1024**3):.1f}"
        except ImportError:
            pass
        
        return info
    
    def generate_report(self) -> str:
        """Generate a comprehensive system report"""
        if not self.results:
            self.run_all_checks()
        
        report = ["SuperSID Pro System Requirements Report", "=" * 50, ""]
        
        # System information
        report.append("System Information:")
        for key, value in self.get_system_info().items():
            report.append(f"  {key}: {value}")
        report.append("")
        
        # Check results
        report.append("Requirements Check Results:")
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            report.append(f"  [{status}] {result.name}")
            report.append(f"         {result.message}")
            if result.details:
                report. append(f"         Details: {result.details}")
            if result.version:
                report.append(f"         Version: {result.version}")
            report.append("")
        
        # Summary
        passed = len([r for r in self.results if r.passed])
        total = len(self.results)
        report.append(f"Summary: {passed}/{total} checks passed")
        
        failed_required = [r for r in self. results if not r.passed and "required" in r.name.lower()]
        if failed_required:
            report.append("")
            report.append("CRITICAL: Required components failed:")
            for result in failed_required:
                report.append(f"  - {result.name}: {result.message}")
        
        return "\n".join(report)