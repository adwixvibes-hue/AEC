#!/usr/bin/env python3
"""
نظام إدارة مخاطر التأمين الذكي
"""

import sys
import os

from PyQt5.QtCore import Qt, QCoreApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont


def main():
    print("=" * 60)
    print("🏢 نظام إدارة مخاطر التأمين الذكي")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    app.setApplicationName("نظام إدارة مخاطر التأمين")
    app.setFont(QFont("Segoe UI", 10))
    
    from main_window import MainWindow
    window = MainWindow()
    window.show()
    
    print("✅ النظام جاهز للاستخدام")
    print("=" * 60)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()