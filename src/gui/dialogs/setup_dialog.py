"""
Setup Dialog for SuperSID Pro - Basic placeholder
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class SetupDialog(QDialog):
    """Basic setup dialog placeholder"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self. setWindowTitle("Setup")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Setup Dialog - Coming Soon"))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)