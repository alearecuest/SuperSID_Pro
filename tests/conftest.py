"""
Pytest configuration and fixtures for SuperSID Pro tests
"""
import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent. parent / 'src'))

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_config():
    """Sample configuration for tests"""
    return {
        'observatory': {
            'name': 'Test Observatory',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'elevation': 10
        },
        'monitoring': {
            'sample_rate': 11025,
            'buffer_size': 1024
        }
    }

@pytest.fixture
def mock_kml_content():
    """Sample KML content for testing"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
<name>Test VLF Stations</name>
<Placemark>
<name>NAA</name>
<description>Frequency: 24.0 kHz</description>
<Point>
<coordinates>-67.2816,44.6449,0</coordinates>
</Point>
</Placemark>
</Document>
</kml>'''

# Handle GUI testing environment
@pytest.fixture(scope="session")
def qapp():
    """QApplication instance for GUI tests"""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    
    from PyQt6.QtWidgets import QApplication
    import sys
    
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    
    yield app
    
    if app:
        app.quit()

def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Set headless mode for CI environments
    import os
    if 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ:
        os.environ. setdefault("QT_QPA_PLATFORM", "offscreen")
