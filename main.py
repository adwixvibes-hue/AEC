
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QColor

from ui.main_window import MainWindow
from ui.styles import AppStyles

def create_splash_screen():

    splash_pixmap = QPixmap(500, 300)
    splash_pixmap.fill(QColor('#0a0e27'))
    
    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
    
    font = QFont("Segoe UI", 20, QFont.Bold)
    splash.setFont(font)
    
    splash.showMessage(
        "🏢 R.AI\n\n"
        "نظام إدارة المخاطر الزلزالية للجزائر\n"
        "Seismic Risk Management System\n\n"
        "جار التحميل...",
        Qt.AlignCenter,
        QColor('#00ffff')
    )
    
    return splash

def main():

    app = QApplication(sys.argv)
    app.setApplicationName("R.AI")
    app.setApplicationVersion("1.0.0")
    app.setStyle('Fusion')
    
    app.setStyleSheet(AppStyles.MAIN_STYLE)
    
    splash = create_splash_screen()
    splash.show()
    app.processEvents()
    
    window = MainWindow()
    
    QTimer.singleShot(2000, lambda: (
        splash.finish(window),
        window.showMaximized()
    ))
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()